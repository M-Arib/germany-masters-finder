import sys
import time
import random
import json
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import primp
from bs4 import BeautifulSoup

# Ensure Windows terminal handles UTF-8 smoothly
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# =================================================================
# 1. CONFIGURATION & URLS
# =================================================================
TARGET_URL = (
    "https://www2.daad.de/deutschland/studienangebote/international-programmes/en/result/"
    "?q=&degree%5B%5D=2&lang%5B%5D=2&subjectGroup%5B%5D=193&cert=&admReq=&langExamPC=&langExamLC="
    "&langExamSC=&fos%5B%5D=226&langDeAvailable=&langEnAvailable=&lvlEn%5B%5D=&modStd%5B%5D="
    "&cit%5B%5D=&tyi%5B%5D=&ins%5B%5D=&fee=&bgn%5B%5D=2&dat%5B%5D=&prep_subj%5B%5D="
    "&prep_degree%5B%5D=&sort=4&dur=&subjects%5B%5D=226&subjects%5B%5D=229&subjects%5B%5D=232"
    "&subjects%5B%5D=233&subjects%5B%5D=236&subjects%5B%5D=547&subjects%5B%5D=548&limit=10&offset=&display=list"
)

SOLR_API_ENDPOINT = "https://www2.daad.de/deutschland/studienangebote/international-programmes/api/solr/en/search.json"
BASE_SITE_URL = "https://www2.daad.de"
OUTPUT_CSV_FILE = "summer_2027.csv"

# =================================================================
# 2. UNIVERSITY RANKINGS MAPPING (QS World Ranking & German Rank)
# =================================================================
GERMAN_UNI_RANKS = {
    # Top Research & TU9 Excellence Universities
    "Technical University of Munich": {"qs_rank": 28, "german_rank": 1, "type": "TU9 / Excellence Uni"},
    "RWTH Aachen University": {"qs_rank": 99, "german_rank": 5, "type": "TU9 / Excellence Uni"},
    "University of Bonn": {"qs_rank": 195, "german_rank": 9, "type": "Excellence Uni"},
    "University of Freiburg": {"qs_rank": 212, "german_rank": 10, "type": "Excellence Uni"},
    "University of Göttingen": {"qs_rank": 252, "german_rank": 11, "type": "Top Research Uni"},
    "University of Tübingen": {"qs_rank": 255, "german_rank": 12, "type": "Excellence Uni"},
    "Technical University of Darmstadt": {"qs_rank": 267, "german_rank": 13, "type": "TU9 Uni"},
    "Dresden University of Technology": {"qs_rank": 269, "german_rank": 14, "type": "TU9 / Excellence Uni"},
    "University of Stuttgart": {"qs_rank": 312, "german_rank": 15, "type": "TU9 Uni"},
    "University of Münster": {"qs_rank": 384, "german_rank": 16, "type": "Top Research Uni"},
    "Julius-Maximilians-Universität Würzburg": {"qs_rank": 440, "german_rank": 17, "type": "Top Research Uni"},
    "Leibniz University Hannover": {"qs_rank": 471, "german_rank": 18, "type": "TU9 Uni"},
    "Kiel University": {"qs_rank": 480, "german_rank": 19, "type": "Research Uni"},
    "University of Potsdam": {"qs_rank": 490, "german_rank": 20, "type": "Research Uni"},
    "University of Bayreuth": {"qs_rank": 501, "german_rank": 21, "type": "Research Uni"},
    "University of Konstanz": {"qs_rank": 505, "german_rank": 22, "type": "Excellence Uni"},
    "Saarland University": {"qs_rank": 510, "german_rank": 23, "type": "Top CS/AI Research Uni"},
    "University of Rostock": {"qs_rank": 550, "german_rank": 24, "type": "Research Uni"},
    "TU Dortmund University": {"qs_rank": 590, "german_rank": 25, "type": "Research Uni"},
    "University of Augsburg": {"qs_rank": 600, "german_rank": 26, "type": "Research Uni"},
    "University of Regensburg": {"qs_rank": 620, "german_rank": 27, "type": "Research Uni"},
    "Ulm University": {"qs_rank": 630, "german_rank": 28, "type": "Research Uni"},
    "University of Siegen": {"qs_rank": 650, "german_rank": 29, "type": "Research Uni"},
    "RPTU University Kaiserslautern-Landau": {"qs_rank": 680, "german_rank": 30, "type": "Technical Uni"},
    "Chemnitz University of Technology": {"qs_rank": 700, "german_rank": 31, "type": "Technical Uni"},
    "University of Bamberg": {"qs_rank": 720, "german_rank": 32, "type": "Research Uni"},
    "University of Passau": {"qs_rank": 750, "german_rank": 33, "type": "Research Uni"},
    "Otto von Guericke University Magdeburg": {"qs_rank": 760, "german_rank": 34, "type": "Research Uni"},
    "Technische Universität Braunschweig": {"qs_rank": 770, "german_rank": 35, "type": "TU9 Uni"},
    "Technische Universität Ilmenau": {"qs_rank": 800, "german_rank": 36, "type": "Technical Uni"},
    "Universität zu Lübeck": {"qs_rank": 801, "german_rank": 37, "type": "Top CS/Medicine Uni"},
    "Bauhaus-Universität Weimar": {"qs_rank": 850, "german_rank": 38, "type": "Specialized Uni"},
    "Brandenburg University of Technology Cottbus-Senftenberg": {"qs_rank": 900, "german_rank": 39, "type": "Technical Uni"},
    "Paderborn University": {"qs_rank": 950, "german_rank": 40, "type": "Top CS Uni"},
    "Trier University": {"qs_rank": 1000, "german_rank": 41, "type": "Research Uni"},
    "University of Hildesheim": {"qs_rank": 1050, "german_rank": 42, "type": "Research Uni"},
    "University of Koblenz": {"qs_rank": 1100, "german_rank": 43, "type": "Research Uni"},
    "Osnabrück University": {"qs_rank": 1150, "german_rank": 44, "type": "Research Uni (Cognitive Science)"},
    "Marburg University": {"qs_rank": 1160, "german_rank": 45, "type": "Research Uni"},

    # Top Universities of Applied Sciences (Hochschule / HAW / TH)
    "HTW Berlin University of Applied Sciences": {"qs_rank": 1200, "german_rank": 46, "type": "UAS (Applied Sciences)"},
    "Technische Hochschule Köln - University of Applied Sciences": {"qs_rank": 1210, "german_rank": 47, "type": "UAS (Applied Sciences)"},
    "Technische Hochschule Nürnberg Georg Simon Ohm": {"qs_rank": 1220, "german_rank": 48, "type": "UAS (Applied Sciences)"},
    "Technische Hochschule Ingolstadt": {"qs_rank": 1230, "german_rank": 49, "type": "Top AI/Mobility UAS"},
    "Deggendorf Institute of Technology": {"qs_rank": 1240, "german_rank": 50, "type": "International UAS"},
    "Darmstadt University of Applied Sciences": {"qs_rank": 1250, "german_rank": 51, "type": "UAS (Applied Sciences)"},
    "Karlsruhe University of Applied Sciences": {"qs_rank": 1260, "german_rank": 52, "type": "Engineering UAS"},
    "Heilbronn University of Applied Sciences": {"qs_rank": 1270, "german_rank": 53, "type": "UAS (Applied Sciences)"},
    "Hochschule Bonn-Rhein-Sieg": {"qs_rank": 1280, "german_rank": 54, "type": "Top CS UAS"},
    "Hof University of Applied Sciences": {"qs_rank": 1290, "german_rank": 55, "type": "UAS (Applied Sciences)"},
    "Technical University of Applied Sciences Augsburg": {"qs_rank": 1300, "german_rank": 56, "type": "UAS (Applied Sciences)"},
    "Technical University of Applied Sciences Würzburg-Schweinfurt (THWS)": {"qs_rank": 1310, "german_rank": 57, "type": "UAS (Applied Sciences)"},
    "Stuttgart Technical University of Applied Sciences": {"qs_rank": 1320, "german_rank": 58, "type": "UAS (Applied Sciences)"},
    "Hochschule Bielefeld – University of Applied Sciences and Arts (HSBI)": {"qs_rank": 1330, "german_rank": 59, "type": "UAS (Applied Sciences)"},
    "RheinMain University of Applied Sciences": {"qs_rank": 1340, "german_rank": 60, "type": "UAS (Applied Sciences)"},
    "Rhine-Waal University of Applied Sciences": {"qs_rank": 1350, "german_rank": 61, "type": "International UAS"},
    "Aalen University": {"qs_rank": 1360, "german_rank": 62, "type": "UAS (Applied Sciences)"},
    "Coburg University of Applied Sciences and Arts": {"qs_rank": 1370, "german_rank": 63, "type": "UAS (Applied Sciences)"},
    "Fulda University of Applied Sciences": {"qs_rank": 1380, "german_rank": 64, "type": "UAS (Applied Sciences)"},
    "Furtwangen University": {"qs_rank": 1390, "german_rank": 65, "type": "Top CS UAS"},
    "Kiel University of Applied Sciences": {"qs_rank": 1400, "german_rank": 66, "type": "UAS (Applied Sciences)"},
    "Ulm University of Applied Sciences": {"qs_rank": 1410, "german_rank": 67, "type": "UAS (Applied Sciences)"},
    "OWL University of Applied Sciences and Arts": {"qs_rank": 1420, "german_rank": 68, "type": "UAS (Applied Sciences)"},
    "Ostbayerische Technische Hochschule Amberg-Weiden (OTH)": {"qs_rank": 1430, "german_rank": 69, "type": "UAS (Applied Sciences)"},
    "South Westphalia University of Applied Sciences": {"qs_rank": 1440, "german_rank": 70, "type": "UAS (Applied Sciences)"},
    "Bremerhaven University of Applied Sciences": {"qs_rank": 1450, "german_rank": 71, "type": "UAS (Applied Sciences)"},
    "Stralsund University of Applied Sciences": {"qs_rank": 1460, "german_rank": 72, "type": "UAS (Applied Sciences)"},
    "University of Applied Sciences Emden/Leer": {"qs_rank": 1470, "german_rank": 73, "type": "UAS (Applied Sciences)"},
    "Albstadt-Sigmaringen University": {"qs_rank": 1480, "german_rank": 74, "type": "UAS (Applied Sciences)"},
    "Nordhausen University of Applied Sciences": {"qs_rank": 1490, "german_rank": 75, "type": "UAS (Applied Sciences)"},
    "Fachhochschule Wedel University of Applied Sciences": {"qs_rank": 1500, "german_rank": 76, "type": "Private UAS"},
    "SRH University": {"qs_rank": 1510, "german_rank": 77, "type": "Private University"},
    "Hochschule Fresenius - University of Applied Sciences": {"qs_rank": 1520, "german_rank": 78, "type": "Private UAS"},
    "Bavarian University of Business and Technology (HDBW)": {"qs_rank": 1530, "german_rank": 79, "type": "Private UAS"},
}


# =================================================================
# 3. APPLICATION OPENING DATES (researched manually, October 2026)
# =================================================================
# DAAD often lists only the deadline ("until 30 November"), never when the
# portal opens. These were looked up on official university pages. Used only
# when DAAD gives no start date. "program" = None applies to all programmes of
# that university. Re-check each source before relying on it.
KNOWN_APPLICATION_OPENINGS = [
    {"university": "Technical University of Munich", "program": None,
     "start": "1 October 2026", "deadline": "30 November 2026",
     "source": "https://www.cit.tum.de/en/cit/studies/degree-programs/master-informatics/",
     "note": "TUM CIT summer window 1 Oct - 30 Nov (verified on the Informatics page)"},
    {"university": "RWTH Aachen University", "program": "Data Science",
     "start": "June 2026 (approx.)", "deadline": "1 September 2026",
     "source": "https://sc.informatik.rwth-aachen.de/de/?p=14325",
     "note": "Non-EU: June to 1 September; central RWTH page takes precedence"},
    {"university": "University of Bonn", "program": None,
     "start": "1 October 2026", "deadline": "1 November 2026",
     "source": "https://www.informatik.uni-bonn.de/en/studies/examination-office/deadlines-at-a-glance",
     "note": "2nd period (EEA applicants only): 15 Dec 2026 - 15 Jan 2027"},
    {"university": "University of Göttingen", "program": "Applied Computer Science",
     "start": "Mid-September 2026 (approx.)", "deadline": "15 October 2026",
     "source": "https://www.uni-goettingen.de/en/619514.html",
     "note": "Portal opens ~1 month before the deadline. EU/EEA deadline: 15 Dec 2026"},
    {"university": "University of Tübingen", "program": "Bioinformatics",
     "start": "1 December 2026", "deadline": "15 January 2027",
     "source": "https://uni-tuebingen.de/en/74459",
     "note": "Non-EU deadline 15 Jan; EU/German deadline 15 Mar"},
    {"university": "Technical University of Darmstadt", "program": "Artificial Intelligence",
     "start": "1 December 2026", "deadline": "15 January 2027",
     "source": "https://www.informatik.tu-darmstadt.de/studium_fb20/im_studium/studiengaenge_liste/aim_msc.en.jsp",
     "note": "Summer term: 01.12. - 15.01."},
    {"university": "University of Münster", "program": None,
     "start": "Late September 2026", "deadline": "30 November 2026",
     "source": "https://master-geoinformatics.com/apply",
     "note": "Non-EU deadline 30 Nov; EU deadline 15 Jan"},
    {"university": "Leibniz University Hannover", "program": None,
     "start": "15 October 2026", "deadline": "30 November 2026",
     "source": "https://www.myguide.de/en/international-programmes-master/detail/leibniz-university-hannover-computer-science-master-of-science-8935/?ip-id=8935",
     "note": "Non-EU: 15 Oct - 30 Nov (needs uni-assist VPD first, up to 8 weeks). EU: 1 Dec - 15 Jan"},
    {"university": "University of Bayreuth", "program": None,
     "start": "15 October 2026", "deadline": "15 January 2027",
     "source": "https://www.uni-bayreuth.de/en/master/computer-science",
     "note": "Non-EU: 15 Oct - 15 Jan. EU/German: 15 Oct - 15 Apr"},
    {"university": "University of Augsburg", "program": "Data Science",
     "start": "Mid-September 2026", "deadline": "1 March 2027",
     "source": "https://www.uni-augsburg.de/en/fakultaet/fai/informatik/studienangebot/msc-dsc/",
     "note": "Visa applicants advised to apply by 1 November"},
    {"university": "University of Siegen", "program": "Quantum Science",
     "start": "1 August 2026", "deadline": "31 October 2026",
     "source": "https://www.uni-siegen.de/en/study/master/quantum-science",
     "note": "Non-EU school-leaving cert: 1 Aug - 31 Oct. Others: 1 Oct - 30 Mar"},
    {"university": "Technische Universität Ilmenau", "program": None,
     "start": "1 August 2026", "deadline": "15 November 2026",
     "source": "https://www.tu-ilmenau.de/en/study/in-study/course-of-studies/administrative-guide/deadlines-and-dates/application-periods",
     "note": "Non-EU (third-country) master's applicants"},
    {"university": "Marburg University", "program": None,
     "start": "1 October 2026", "deadline": "15 January 2027",
     "source": "https://www.uni-marburg.de/en/studying/after-your-first-degree/masters-programs/application-for-a-masters-programme/master-application-deadlines",
     "note": "Via uni-assist (allow 4-6 weeks processing)"},
    {"university": "Heilbronn University of Applied Sciences", "program": None,
     "start": "Mid-November 2026", "deadline": None,
     "source": "https://www.hs-heilbronn.de/en/master-application",
     "note": "Portals open mid-November for the summer semester"},
    {"university": "SRH University", "program": None,
     "start": "Rolling (open all year)", "deadline": "Until places are filled",
     "source": "https://www.mygermanuniversity.com/universities/SRH-University/application-deadlines",
     "note": "No fixed deadline; apply early (third-party source, confirm with SRH)"},
    {"university": "RheinMain University of Applied Sciences", "program": None,
     "start": "Early December 2026 (expected)", "deadline": "15 January 2027",
     "source": "https://www.hs-rm.de/en/studying-with-us/application-and-enrollment/international-applicants",
     "note": "uni-assist opened early Dec 2025 for summer 2026; 2027 not yet confirmed"},
    {"university": "Stuttgart Technical University of Applied Sciences", "program": "Software Technology",
     "start": "5 May 2026 (regular phase, closed)", "deadline": "31 August 2026",
     "source": "https://www.hft-stuttgart.de/informatik/master-software-technology",
     "note": "Extra phase 5 Nov - 15 Jan ONLY if places remain"},
    {"university": "Fulda University of Applied Sciences", "program": None,
     "start": "1 November 2026", "deadline": "1 December 2026",
     "source": "https://www.hs-fulda.de/en/studyprogramme/global-software-development-msc",
     "note": "Non-EU with foreign degree. German degree / EU: until 31 March"},
    {"university": "Furtwangen University", "program": "Business Consulting",
     "start": "15 April 2026", "deadline": "15 October 2026",
     "source": "https://www.hs-furtwangen.de/en/programmes/business-consulting-master/",
     "note": "Application period 15 April - 15 October"},
    {"university": "OWL University of Applied Sciences", "program": None,
     "start": "17 November 2026", "deadline": "15 January 2027",
     "source": "https://www.th-owl.de/en/studies/available-courses/degree-programs/detail/information-technology/",
     "note": "International applicants: 17.11. - 15.01."},
]


def get_known_opening(uni_name: str, program_name: str):
    """Returns the researched opening-date entry for a programme, or None."""
    for entry in KNOWN_APPLICATION_OPENINGS:
        if entry["university"].lower() not in (uni_name or "").lower():
            continue
        if entry["program"] and entry["program"].lower() not in (program_name or "").lower():
            continue
        return entry
    return None


def get_ranking_info(uni_name: str) -> tuple:
    """Finds QS rank and German rank for a given university name."""
    if not uni_name:
        return 9999, 999, "Other"
    
    # Exact match
    if uni_name in GERMAN_UNI_RANKS:
        r = GERMAN_UNI_RANKS[uni_name]
        return r["qs_rank"], r["german_rank"], r["type"]
    
    # Normalized search: never match a university against a UAS of the same city
    # (e.g. "Ulm University" vs "Ulm University of Applied Sciences"), and prefer
    # the longest (most specific) matching key.
    def normalize(s):
        return s.lower().replace("universität", "university").replace("–", "-")

    def is_uas(s):
        return any(w in s for w in ("applied sciences", "hochschule", "fachhochschule"))

    norm_uni = normalize(uni_name)
    best = None
    for key, r in GERMAN_UNI_RANKS.items():
        norm_key = normalize(key)
        if is_uas(norm_key) != is_uas(norm_uni):
            continue
        if norm_key in norm_uni or norm_uni in norm_key:
            if best is None or len(norm_key) > len(best[0]):
                best = (norm_key, r)
    if best:
        r = best[1]
        return r["qs_rank"], r["german_rank"], r["type"]

    return 2000, 100, "Applied Sciences / Specialized"


def parse_and_clean_query_params(url: str) -> dict:
    """Parses URL query parameters and sets summer semester filter."""
    parsed = urllib.parse.urlparse(url)
    raw_params = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)
    
    clean_params = {}
    for key, values in raw_params.items():
        non_empty = [v.strip() for v in values if v and v.strip()]
        if non_empty:
            clean_params[key] = non_empty

    # Enforce Summer Semester (bgn[]=2) and remove 10-item limit to get all courses
    clean_params["bgn[]"] = ["2"]
    clean_params["limit"] = ["500"]
    clean_params.pop("offset", None)

    return clean_params


def parse_detail_page(course_id: int, client: primp.Client) -> dict:
    """
    Fetches and parses a DAAD program detail page for application start dates,
    deadlines, requirements, fees, and course links.
    """
    url = f"{BASE_SITE_URL}/deutschland/studienangebote/international-programmes/en/detail/{course_id}/"
    headers = {
        "Referer": "https://www2.daad.de/deutschland/studienangebote/international-programmes/en/result/",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    data = {
        "Summer_App_Period_NonEU": "Please enquire",
        "Summer_App_Period_EU": "Please enquire",
        "Summer_App_Period_All": "Please enquire",
        "Summer_App_Start_Date": "Not specified",
        "Summer_App_Deadline": "Please enquire",
        "Winter_App_Period": "Please enquire",
        "Submit_Application_Via": "University Portal / Website",
        "Academic_Admission_Requirements": "See course website",
        "Language_Requirements": "English",
        "Tuition_Fees_Detail": "None",
        "Semester_Contribution": "Approx. 250-400 EUR / semester",
        "Official_Course_Website": "N/A",
        "Contact_Email": "N/A",
        "Detail_Fetch_Status": "OK"
    }

    # Fetch with retries + backoff so transient failures don't silently become "Please enquire"
    resp = None
    last_error = ""
    for attempt in range(3):
        try:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                break
            last_error = f"HTTP {resp.status_code}"
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
        resp = None
        time.sleep(2 ** attempt)

    if resp is None:
        data["Detail_Fetch_Status"] = f"FAILED ({last_error})"
        return data

    try:
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Parse all DT / DD definitions
        for dt in soup.find_all('dt'):
            dt_title = dt.get_text(strip=True).lower()
            dd = dt.find_next_sibling('dd')
            if not dd:
                continue
            
            if ('application period' in dt_title or 'application deadline' in dt_title) and 'more information' not in dt_title:
                raw_text = dd.get_text("\n", strip=True)
                lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
                joined = " | ".join(lines)
                
                # Check for summer semester parts
                sections = joined.split("The following is valid for applicants from:")
                summer_non_eu = []
                summer_eu = []
                summer_all = []
                winter_all = []
                
                for sec in sections:
                    sec_clean = sec.strip()
                    if not sec_clean:
                        continue
                    if 'summer' in sec_clean.lower():
                        if 'non-eu' in sec_clean.lower():
                            summer_non_eu.append(sec_clean)
                        elif 'eu countries' in sec_clean.lower():
                            summer_eu.append(sec_clean)
                        else:
                            summer_all.append(sec_clean)
                    elif 'winter' in sec_clean.lower():
                        winter_all.append(sec_clean)

                if summer_non_eu:
                    data["Summer_App_Period_NonEU"] = " // ".join(summer_non_eu)
                if summer_eu:
                    data["Summer_App_Period_EU"] = " // ".join(summer_eu)
                if summer_all:
                    data["Summer_App_Period_All"] = " // ".join(summer_all)
                elif not summer_non_eu and not summer_eu and 'winter' not in joined.lower():
                    data["Summer_App_Period_All"] = joined
                    
                if winter_all:
                    data["Winter_App_Period"] = " // ".join(winter_all)

                # Extract start and deadline dates ONLY from summer-semester text,
                # so winter dates are never reported as summer deadlines.
                # Non-EU periods are preferred since they are usually the earliest.
                if summer_non_eu or summer_all or summer_eu:
                    summer_text = " // ".join(summer_non_eu or summer_all or summer_eu)
                elif 'winter' not in joined.lower():
                    summer_text = joined  # no semester labels at all
                else:
                    summer_text = ""  # only winter info present

                # e.g., "15 October 2026 - 15 January 2027" or "until 15 October"
                date_range_match = re.search(r'(\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{1,2}\s+[A-Za-z]+)\s*(?:-|–|to)\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{1,2}\s+[A-Za-z]+)', summer_text)
                if date_range_match:
                    data["Summer_App_Start_Date"] = date_range_match.group(1).strip()
                    data["Summer_App_Deadline"] = date_range_match.group(2).strip()
                else:
                    until_match = re.search(r'until\s+(\d{1,2}\s+[A-Za-z]+(?:\s+\d{4})?)', summer_text, re.I)
                    if until_match:
                        data["Summer_App_Deadline"] = until_match.group(1).strip()
                    by_match = re.search(r'by\s+(\d{1,2}\s+[A-Za-z]+(?:\s+\d{4})?)', summer_text, re.I)
                    if by_match and data["Summer_App_Deadline"] == "Please enquire":
                        data["Summer_App_Deadline"] = by_match.group(1).strip()

            elif 'submit application via' in dt_title or 'application method' in dt_title:
                portal_text = dd.get_text(" ", strip=True)
                data["Submit_Application_Via_Raw"] = portal_text
                links = [a['href'] for a in dd.find_all('a', href=True)]
                if 'uni-assist' in portal_text.lower():
                    data["Submit_Application_Via"] = "uni-assist"
                elif links:
                    data["Submit_Application_Via"] = f"University Portal ({links[0]})"
                else:
                    data["Submit_Application_Via"] = portal_text
                    
            elif 'academic admission requirements' in dt_title or 'admission requirements' in dt_title:
                data["Academic_Admission_Requirements"] = dd.get_text(" ", strip=True)
                
            elif 'language requirements' in dt_title:
                data["Language_Requirements"] = dd.get_text(" ", strip=True)
                
            elif dt_title.startswith('tuition fees per semester'):
                data["Tuition_Fees_Detail"] = dd.get_text(" ", strip=True)
            elif 'tuition fee' in dt_title:
                # e.g. "Description of tuition fees" — keep separately so it doesn't overwrite the amount
                data["Tuition_Fees_Note"] = dd.get_text(" ", strip=True)
                
            elif 'semester contribution' in dt_title:
                data["Semester_Contribution"] = dd.get_text(" ", strip=True)

            elif dt_title.startswith('description/content') or dt_title == 'course organisation':
                text = dd.get_text(" ", strip=True)
                data["Course_Content"] = (data.get("Course_Content", "") + " " + text).strip()

        # 2. Extract Official Course Website Link
        for a in soup.find_all('a', href=re.compile(r'^http')):
            text = a.get_text(strip=True).lower()
            if 'course website' in text or 'programme website' in text:
                data["Official_Course_Website"] = a['href']
                break
        if data["Official_Course_Website"] == "N/A":
            for a in soup.find_all('a', href=re.compile(r'^http')):
                if 'website' in a.get_text(strip=True).lower() and 'daad' not in a['href']:
                    data["Official_Course_Website"] = a['href']
                    break

        # 3. Collect every mention of uni-assist / VPD (pre-check of foreign documents)
        page_text = soup.get_text(" ", strip=True)
        snippets = []
        for m in re.finditer(r"uni-?assist|\bVPD\b|Vorprüfungsdokumentation|preliminary (review )?documentation", page_text, re.I):
            snip = page_text[max(0, m.start() - 150): m.end() + 150]
            if not any(snip[:60] in s for s in snippets):
                snippets.append(snip)
        data["UniAssist_Evidence"] = " || ".join(snippets[:3])

        # 4. Extract Contact Email
        for a in soup.find_all('a', href=re.compile(r'^mailto:')):
            data["Contact_Email"] = a['href'].replace('mailto:', '').strip()
            break

    except Exception as e:
        data["Detail_Fetch_Status"] = f"PARSE ERROR ({type(e).__name__}: {e})"

    return data


def scrape_summer_2027():
    """Main extraction routine for Summer 2027 programmes."""
    print("=" * 80)
    print("       DAAD SUMMER 2027 MASTER'S PROGRAMMES EXTRACTOR")
    print("       Rank-Sorted | Deadlines | Start Dates | Requirements")
    print("=" * 80)
    
    client = primp.Client(impersonate="random", timeout=30)

    # 1. Fetch search list
    api_params = parse_and_clean_query_params(TARGET_URL)
    query_str = urllib.parse.urlencode(api_params, doseq=True)
    full_api_url = f"{SOLR_API_ENDPOINT}?{query_str}"
    
    print("[*] Connecting to DAAD Solr API for Summer Semester programs...")
    headers = {
        "Referer": TARGET_URL,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/plain, */*"
    }
    
    resp = None
    for attempt in range(3):
        try:
            resp = client.get(full_api_url, headers=headers)
            if resp.status_code == 200:
                break
            print(f"[!] Solr API returned HTTP {resp.status_code}, retrying...")
        except Exception as e:
            print(f"[!] Solr API request failed ({e}), retrying...")
        resp = None
        time.sleep(2 ** attempt)
    if resp is None:
        print("[!] Error: could not reach the DAAD Solr API after 3 attempts.")
        return

    solr_data = resp.json()
    courses_raw = solr_data.get("courses", [])
    total_found = solr_data.get("numResults", len(courses_raw))
    print(f"[*] Found {total_found} programmes matching your criteria.")
    if total_found > len(courses_raw):
        print(f"[!] WARNING: API returned only {len(courses_raw)} of {total_found} programmes. "
              f"Raise the 'limit' parameter to get them all.")
    print(f"[*] Fetching deep details (deadlines, start dates, prerequisites) for all {len(courses_raw)} programs...\n")
    
    # 2. Multi-threaded detail fetching
    detailed_results = {}
    
    def fetch_worker(course_item):
        cid = course_item["id"]
        c_client = primp.Client(impersonate="random", timeout=30)
        time.sleep(random.uniform(0.3, 1.0))  # be polite to DAAD's servers
        return cid, parse_detail_page(cid, c_client)

    max_workers = 6
    completed_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_worker, c): c for c in courses_raw}
        for f in as_completed(futures):
            completed_count += 1
            cid, detail = f.result()
            detailed_results[cid] = detail
            if completed_count % 20 == 0 or completed_count == len(courses_raw):
                print(f"    -> Progress: [{completed_count}/{len(courses_raw)}] detail pages processed.")

    print("\n[*] Processing, ranking, and sorting extracted programs...")
    
    # 3. Assemble and rank records
    final_rows = []
    for item in courses_raw:
        cid = item.get("id")
        detail = detailed_results.get(cid, {})
        
        academy = item.get("academy") or "N/A"
        qs_rank, german_rank, uni_type = get_ranking_info(academy)
        
        course_name = item.get("courseName") or item.get("courseNameShort") or "N/A"
        subject = item.get("subject") or "N/A"
        city = item.get("city") or "N/A"
        beginning = item.get("beginning") or "Summer semester"
        duration = item.get("programmeDuration") or "N/A"
        languages = ", ".join(item.get("languages", [])) if item.get("languages") else "English"
        tuition_overview = item.get("tuitionFees") or "None / No tuition fees"
        deadline_overview = item.get("applicationDeadline") or "Please enquire"
        daad_link = f"{BASE_SITE_URL}{item.get('link')}" if item.get('link') else "N/A"
        
        support_services = ""
        if item.get("supportInternationalStudents"):
            support_services = " | ".join(item.get("supportInternationalStudents"))

        # Application start date: DAAD first, then researched university data
        app_start = detail.get("Summer_App_Start_Date", "Not specified")
        app_deadline = detail.get("Summer_App_Deadline", deadline_overview)
        start_source = "DAAD" if app_start != "Not specified" else ""
        app_notes = ""
        known = get_known_opening(academy, course_name)
        if app_start == "Not specified" and known:
            app_start = known["start"]
            start_source = known["source"]
            app_notes = known["note"]
            if app_deadline == "Please enquire" and known["deadline"]:
                app_deadline = known["deadline"]
        elif app_start == "Not specified":
            app_start = "Not published (only deadline listed)" if app_deadline != "Please enquire" else "Not published"
            start_source = "Check Official_Course_Website"

        # QS doesn't rank Universities of Applied Sciences; their values in the
        # table are placeholders for sorting only, so don't present them as ranks.
        qs_display = qs_rank if qs_rank < 1200 else "Not ranked"

        row = {
            "German_Rank": german_rank,
            "QS_World_Rank": qs_display,
            "_qs_sort": qs_rank,
            "University_Type": uni_type,
            "University": academy,
            "Program_Name": course_name,
            "City": city,
            "Subject_Field": subject,
            "Beginning_Semester": beginning,
            "Duration": duration,
            "Teaching_Language": languages,
            "Tuition_Fees_Overview": tuition_overview,
            "Tuition_Fees_Detail": detail.get("Tuition_Fees_Detail", tuition_overview),
            "Tuition_Fees_Note": detail.get("Tuition_Fees_Note", ""),
            "Semester_Contribution": detail.get("Semester_Contribution", "N/A"),
            "Application_Start_Date": app_start,
            "Application_Deadline": app_deadline,
            "Application_Start_Source": start_source,
            "Application_Notes": app_notes,
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
            "Support_Services": support_services,
            "Official_Course_Website": detail.get("Official_Course_Website", "N/A"),
            "DAAD_Link": daad_link,
            "Contact_Email": detail.get("Contact_Email", "N/A"),
            "Detail_Fetch_Status": detail.get("Detail_Fetch_Status", "NOT FETCHED")
        }
        final_rows.append(row)
        
    # 4. Sort ascending by German Rank, then QS World Rank, then University Name
    df = pd.DataFrame(final_rows)
    df.sort_values(by=["German_Rank", "_qs_sort", "University", "Program_Name"], ascending=[True, True, True, True], inplace=True)
    df.drop(columns=["_qs_sort"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # 5. Save to summer_2027.csv
    df.to_csv(OUTPUT_CSV_FILE, index=False, encoding="utf-8-sig")
    
    print("\n" + "=" * 80)
    print(f"[+] SUCCESS! Saved {len(df)} programs to '{OUTPUT_CSV_FILE}' sorted by Rank.")
    failed = df[df["Detail_Fetch_Status"] != "OK"]
    if len(failed):
        print(f"[!] WARNING: {len(failed)} detail pages failed — their deadline/requirement fields are defaults.")
        print("    Filter the 'Detail_Fetch_Status' column in the CSV to see which ones.")
    has_start = ~df["Application_Start_Date"].str.startswith("Not published")
    print(f"[*] Application start date known for {has_start.sum()}/{len(df)} programmes "
          f"(DAAD: {(df['Application_Start_Source'] == 'DAAD').sum()}, "
          f"university websites: {(has_start & (df['Application_Start_Source'] != 'DAAD')).sum()}).")
    print("=" * 80)
    
    # Print Top 10 ranked programs preview
    print("\n--- TOP 10 HIGHEST RANKED UNIVERSITIES (Summer Semester) ---")
    for i, r in df.head(10).iterrows():
        print(f"#{r['German_Rank']} (QS #{r['QS_World_Rank']}) {r['University']} — {r['Program_Name']}")
        print(f"    City: {r['City']} | Opens: {r['Application_Start_Date']} | Deadline: {r['Application_Deadline']}")
        print(f"    App Portal: {r['Application_Method']}")
        print(f"    Website: {r['Official_Course_Website']}")
        print("-" * 75)

    return df


if __name__ == "__main__":
    scrape_summer_2027()
