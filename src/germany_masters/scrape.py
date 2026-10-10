"""Scrapes every programme matching the configured DAAD search into one CSV."""

from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from . import config, daad
from .classify import is_applied_sciences
from .reference import QS_2026, get_known_opening


def _record(item: dict, detail: dict) -> dict:
    """Merges a search result with its detail page and the researched opening dates."""
    university = item.get("academy") or "N/A"
    program = item.get("courseName") or item.get("courseNameShort") or "N/A"
    deadline_overview = item.get("applicationDeadline") or "Please enquire"
    tuition_overview = item.get("tuitionFees") or "None / No tuition fees"

    start = detail.get("Summer_App_Start_Date", "Not specified")
    deadline = detail.get("Summer_App_Deadline", deadline_overview)
    start_source = "DAAD" if start != "Not specified" else ""
    notes = ""
    known = get_known_opening(university, program)
    if start == "Not specified" and known:
        start, start_source, notes = known["start"], known["source"], known["note"]
        if deadline == "Please enquire" and known["deadline"]:
            deadline = known["deadline"]
    elif start == "Not specified":
        start = "Not published (only deadline listed)" if deadline != "Please enquire" else "Not published"
        start_source = "Check Official_Course_Website"

    return {
        "QS_2026_Rank": QS_2026.get(university, ""),
        "Institution_Type": "University of Applied Sciences" if is_applied_sciences(university) else "University",
        "University": university,
        "Program_Name": program,
        "City": item.get("city") or "N/A",
        "Subject_Field": item.get("subject") or "N/A",
        "Beginning_Semester": item.get("beginning") or "Summer semester",
        "Duration": item.get("programmeDuration") or "N/A",
        "Teaching_Language": ", ".join(item.get("languages") or []) or "English",
        "Tuition_Fees_Overview": tuition_overview,
        "Tuition_Fees_Detail": detail.get("Tuition_Fees_Detail", tuition_overview),
        "Tuition_Fees_Note": detail.get("Tuition_Fees_Note", ""),
        "Semester_Contribution": detail.get("Semester_Contribution", "N/A"),
        "Application_Start_Date": start,
        "Application_Deadline": deadline,
        "Application_Start_Source": start_source,
        "Application_Notes": notes,
        "Summer_App_Period_NonEU": detail.get("Summer_App_Period_NonEU", "Please enquire"),
        "Summer_App_Period_EU": detail.get("Summer_App_Period_EU", "Please enquire"),
        "Summer_App_Period_All": detail.get("Summer_App_Period_All", deadline_overview),
        "Winter_App_Period": detail.get("Winter_App_Period", "Please enquire"),
        "Application_Method": detail.get("Submit_Application_Via", "University Portal"),
        "Application_Method_Raw": detail.get("Submit_Application_Via_Raw", ""),
        "UniAssist_Evidence": detail.get("UniAssist_Evidence", ""),
        "Academic_Requirements": detail.get("Academic_Admission_Requirements", "See course website"),
        "Language_Requirements": detail.get("Language_Requirements", "English"),
        "Course_Content": detail.get("Course_Content", ""),
        "Support_Services": " | ".join(item.get("supportInternationalStudents") or []),
        "Official_Course_Website": detail.get("Official_Course_Website", "N/A"),
        "DAAD_Link": f"{config.DAAD_BASE_URL}{item['link']}" if item.get("link") else "N/A",
        "Contact_Email": detail.get("Contact_Email", "N/A"),
        "Detail_Fetch_Status": detail.get("Detail_Fetch_Status", "NOT FETCHED"),
    }


def _qs_sort_key(rank: str) -> int:
    return int(rank.split("-")[0]) if rank else 99_999


def run(output=config.DATA_CSV) -> pd.DataFrame:
    print(f"[*] Searching DAAD for {config.INTAKE_NAME} programmes...")
    courses, total = daad.search()
    print(f"[*] DAAD reports {total} matching programmes.")
    if total > len(courses):
        print(f"[!] WARNING: only {len(courses)} of {total} returned. Raise PAGE_SIZE in config.py.")

    details = {}
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as pool:
        futures = {pool.submit(daad.fetch_detail, c["id"]): c["id"] for c in courses}
        for done, future in enumerate(as_completed(futures), 1):
            details[futures[future]] = future.result()
            if done % 20 == 0 or done == len(courses):
                print(f"    {done}/{len(courses)} detail pages processed")

    df = pd.DataFrame([_record(c, details.get(c.get("id"), {})) for c in courses])
    df["_qs"] = df["QS_2026_Rank"].map(_qs_sort_key)
    df = df.sort_values(["_qs", "University", "Program_Name"]).drop(columns="_qs").reset_index(drop=True)

    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False, encoding="utf-8-sig")

    failed = (df["Detail_Fetch_Status"] != "OK").sum()
    has_start = (~df["Application_Start_Date"].str.startswith("Not published")).sum()
    print(f"[+] Saved {len(df)} programmes to {output.relative_to(config.ROOT)}")
    print(f"[*] Opening date known for {has_start}/{len(df)} programmes")
    if failed:
        print(f"[!] WARNING: {failed} detail pages failed; see the Detail_Fetch_Status column.")
    return df
