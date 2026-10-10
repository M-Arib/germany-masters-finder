"""Talks to the DAAD International Programmes website: search API and detail pages."""

import random
import re
import time
import urllib.parse

import primp
from bs4 import BeautifulSoup

from . import config

DETAIL_DEFAULTS = {
    "Summer_App_Period_NonEU": "Please enquire",
    "Summer_App_Period_EU": "Please enquire",
    "Summer_App_Period_All": "Please enquire",
    "Summer_App_Start_Date": "Not specified",
    "Summer_App_Deadline": "Please enquire",
    "Winter_App_Period": "Please enquire",
    "Submit_Application_Via": "University Portal / Website",
    "Submit_Application_Via_Raw": "",
    "Academic_Admission_Requirements": "See course website",
    "Language_Requirements": "English",
    "Tuition_Fees_Detail": "None",
    "Tuition_Fees_Note": "",
    "Semester_Contribution": "Approx. 250-400 EUR / semester",
    "Course_Content": "",
    "UniAssist_Evidence": "",
    "Official_Course_Website": "N/A",
    "Contact_Email": "N/A",
    "Detail_Fetch_Status": "OK",
}

_DATE = r"\d{1,2}\s+[A-Za-z]+(?:\s+\d{4})?"
_RANGE = re.compile(rf"({_DATE})\s*(?:-|–|to)\s*({_DATE})")
_UNI_ASSIST = re.compile(r"uni-?assist|\bVPD\b|Vorprüfungsdokumentation|preliminary (review )?documentation", re.I)


def new_client() -> primp.Client:
    return primp.Client(impersonate="random", timeout=config.REQUEST_TIMEOUT)


def get_with_retries(client: primp.Client, url: str, headers: dict):
    """GET with exponential backoff. Returns (response, error) with exactly one of them set."""
    error = ""
    for attempt in range(config.RETRIES):
        try:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp, ""
            error = f"HTTP {resp.status_code}"
        except Exception as e:  # network errors vary by platform; report them all the same way
            error = f"{type(e).__name__}: {e}"
        time.sleep(2 ** attempt)
    return None, error


def search_params(url: str = config.TARGET_URL) -> dict:
    """Turns a DAAD result-page URL into search API parameters for the configured intake."""
    raw = urllib.parse.parse_qs(urllib.parse.urlparse(url).query, keep_blank_values=False)
    params = {k: [v.strip() for v in vals if v.strip()] for k, vals in raw.items()}
    params = {k: v for k, v in params.items() if v}
    params["bgn[]"] = [config.SEMESTER_CODE]
    params["limit"] = [str(config.PAGE_SIZE)]
    params.pop("offset", None)
    return params


def search(url: str = config.TARGET_URL) -> tuple[list[dict], int]:
    """Returns (courses, total number of matches DAAD reports)."""
    query = urllib.parse.urlencode(search_params(url), doseq=True)
    headers = {"Referer": url, "X-Requested-With": "XMLHttpRequest", "Accept": "application/json, text/plain, */*"}
    resp, error = get_with_retries(new_client(), f"{config.SEARCH_API_URL}?{query}", headers)
    if resp is None:
        raise RuntimeError(f"DAAD search API unreachable after {config.RETRIES} attempts ({error})")
    data = resp.json()
    courses = data.get("courses", [])
    return courses, data.get("numResults", len(courses))


def fetch_detail(course_id) -> dict:
    """Downloads and parses one programme's detail page. Never raises; failures go in Detail_Fetch_Status."""
    time.sleep(random.uniform(0.3, 1.0))  # be polite to DAAD's servers
    headers = {"Referer": config.RESULT_PAGE_URL, "X-Requested-With": "XMLHttpRequest"}
    resp, error = get_with_retries(new_client(), config.DETAIL_URL.format(course_id=course_id), headers)
    if resp is None:
        return {**DETAIL_DEFAULTS, "Detail_Fetch_Status": f"FAILED ({error})"}
    try:
        return parse_detail_html(resp.text)
    except Exception as e:  # keep the row; a broken page shouldn't stop the whole scrape
        return {**DETAIL_DEFAULTS, "Detail_Fetch_Status": f"PARSE ERROR ({type(e).__name__}: {e})"}


def _parse_application_periods(dd, data: dict) -> None:
    lines = [line.strip() for line in dd.get_text("\n", strip=True).split("\n") if line.strip()]
    joined = " | ".join(lines)
    has_winter = "winter" in joined.lower()

    summer_non_eu, summer_eu, summer_all, winter = [], [], [], []
    for section in joined.split("The following is valid for applicants from:"):
        sec = section.strip()
        low = sec.lower()
        if not sec:
            continue
        if "summer" in low:
            if "non-eu" in low:
                summer_non_eu.append(sec)
            elif "eu countries" in low:
                summer_eu.append(sec)
            else:
                summer_all.append(sec)
        elif "winter" in low:
            winter.append(sec)

    if summer_non_eu:
        data["Summer_App_Period_NonEU"] = " // ".join(summer_non_eu)
    if summer_eu:
        data["Summer_App_Period_EU"] = " // ".join(summer_eu)
    if summer_all:
        data["Summer_App_Period_All"] = " // ".join(summer_all)
    elif not summer_non_eu and not summer_eu and not has_winter:
        data["Summer_App_Period_All"] = joined
    if winter:
        data["Winter_App_Period"] = " // ".join(winter)

    # Dates come ONLY from summer-semester text so winter dates never become summer deadlines.
    # Non-EU periods are preferred since they are usually the earliest.
    if summer_non_eu or summer_all or summer_eu:
        summer_text = " // ".join(summer_non_eu or summer_all or summer_eu)
    else:
        summer_text = "" if has_winter else joined

    if m := _RANGE.search(summer_text):
        data["Summer_App_Start_Date"], data["Summer_App_Deadline"] = m.group(1).strip(), m.group(2).strip()
        return
    if m := re.search(rf"until\s+({_DATE})", summer_text, re.I) or re.search(rf"by\s+({_DATE})", summer_text, re.I):
        data["Summer_App_Deadline"] = m.group(1).strip()


def parse_detail_html(html: str) -> dict:
    """Extracts application periods, fees, requirements and links from a DAAD detail page."""
    soup = BeautifulSoup(html, "html.parser")
    data = dict(DETAIL_DEFAULTS)

    for dt in soup.find_all("dt"):
        title = dt.get_text(strip=True).lower()
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        text = dd.get_text(" ", strip=True)

        if ("application period" in title or "application deadline" in title) and "more information" not in title:
            _parse_application_periods(dd, data)
        elif "submit application via" in title or "application method" in title:
            data["Submit_Application_Via_Raw"] = text
            links = [a["href"] for a in dd.find_all("a", href=True)]
            if "uni-assist" in text.lower():
                data["Submit_Application_Via"] = "uni-assist"
            elif links:
                data["Submit_Application_Via"] = f"University Portal ({links[0]})"
            else:
                data["Submit_Application_Via"] = text
        elif "admission requirements" in title:
            data["Academic_Admission_Requirements"] = text
        elif "language requirements" in title:
            data["Language_Requirements"] = text
        elif title.startswith("tuition fees per semester"):
            data["Tuition_Fees_Detail"] = text
        elif "tuition fee" in title:
            # e.g. "Description of tuition fees": kept apart so it doesn't overwrite the amount
            data["Tuition_Fees_Note"] = text
        elif "semester contribution" in title:
            data["Semester_Contribution"] = text
        elif title.startswith("description/content") or title == "course organisation":
            data["Course_Content"] = f"{data['Course_Content']} {text}".strip()

    links = soup.find_all("a", href=re.compile(r"^http"))
    website = next((a["href"] for a in links
                    if any(w in a.get_text(strip=True).lower() for w in ("course website", "programme website"))), None)
    website = website or next((a["href"] for a in links
                               if "website" in a.get_text(strip=True).lower() and "daad" not in a["href"]), None)
    if website:
        data["Official_Course_Website"] = website

    page_text = soup.get_text(" ", strip=True)
    snippets = []
    for m in _UNI_ASSIST.finditer(page_text):
        snip = page_text[max(0, m.start() - 150): m.end() + 150]
        if not any(snip[:60] in s for s in snippets):
            snippets.append(snip)
    data["UniAssist_Evidence"] = " || ".join(snippets[:3])

    if mail := soup.find("a", href=re.compile(r"^mailto:")):
        data["Contact_Email"] = mail["href"].replace("mailto:", "").strip()

    return data
