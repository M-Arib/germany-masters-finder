import sys
import time
import json
import urllib.parse
import pandas as pd
import primp

# Ensure terminal stdout handles unicode cleanly on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# =================================================================
# 1. TARGET DAAD URL (Summer Semester)
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
# =================================================================


def parse_and_clean_query_params(url: str, enforce_summer_semester: bool = True) -> dict:
    """
    Parses the DAAD URL parameters and strips empty values so that the Solr API
    matches programs accurately. Also ensures the summer semester parameter (bgn[]=2) is set
    and retrieves all matching programs without pagination cutoff.
    """
    parsed = urllib.parse.urlparse(url)
    raw_params = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)
    
    # Filter out empty parameters
    clean_params = {}
    for key, values in raw_params.items():
        non_empty = [v.strip() for v in values if v and v.strip()]
        if non_empty:
            clean_params[key] = non_empty

    # Enforce Summer Semester if requested (bgn[]=2 represents Summer Semester)
    if enforce_summer_semester:
        clean_params["bgn[]"] = ["2"]

    # Set limit to fetch all matching results
    clean_params["limit"] = ["500"]
    clean_params.pop("offset", None)

    return clean_params


def run_scraper(target_url: str = TARGET_URL, output_csv: str = "Final_DAAD_List.csv"):
    """
    Extracts all matching programmes from the DAAD International Programmes portal.
    Uses browser impersonation to retrieve structured data directly and accurately.
    """
    print("=" * 70)
    print("[DAAD International Programmes Scraper - Summer Semester]")
    print("=" * 70)
    
    client = primp.Client(impersonate="random", timeout=30)
    
    # Prepare API query parameters
    api_params = parse_and_clean_query_params(target_url, enforce_summer_semester=True)
    query_str = urllib.parse.urlencode(api_params, doseq=True)
    full_api_url = f"{SOLR_API_ENDPOINT}?{query_str}"
    
    print("[*] Querying DAAD API for Summer Semester programs...")
    
    headers = {
        "Referer": target_url,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/plain, */*"
    }
    
    try:
        response = None
        for attempt in range(3):
            try:
                response = client.get(full_api_url, headers=headers)
                if response.status_code == 200:
                    break
                print(f"[!] Received HTTP status {response.status_code}, retrying...")
            except Exception as e:
                print(f"[!] Request failed ({e}), retrying...")
            response = None
            time.sleep(2 ** attempt)
        if response is None:
            print("[!] Error: could not reach the DAAD API after 3 attempts.")
            return []

        data = response.json()
        total_results = data.get("numResults", 0)
        courses_raw = data.get("courses", [])

        print(f"[*] Found {total_results} total programs matching criteria.")
        if total_results > len(courses_raw):
            print(f"[!] WARNING: API returned only {len(courses_raw)} of {total_results} programs. "
                  f"Raise the 'limit' parameter to get them all.")
        print(f"[*] Extracting details for {len(courses_raw)} programs...\n")
        
        extracted_data = []
        for idx, item in enumerate(courses_raw, 1):
            academy = item.get("academy") or "N/A"
            course_name = item.get("courseName") or item.get("courseNameShort") or "N/A"
            subject = item.get("subject") or "N/A"
            city = item.get("city") or "N/A"
            beginning = item.get("beginning") or "Summer semester"
            duration = item.get("programmeDuration") or "N/A"
            languages = ", ".join(item.get("languages", [])) if item.get("languages") else "Not specified"
            tuition = item.get("tuitionFees") or "Not specified"
            deadline = item.get("applicationDeadline") or "Please enquire"
            rel_link = item.get("link") or ""
            full_link = f"{BASE_SITE_URL}{rel_link}" if rel_link else "N/A"
            
            support = ""
            if item.get("supportInternationalStudents"):
                support = " | ".join(item.get("supportInternationalStudents"))
                
            details_summary = (
                f"Subject: {subject} | City: {city} | Duration: {duration} | "
                f"Beginning: {beginning} | Tuition: {tuition} | "
                f"Deadline: {deadline} | Languages: {languages}"
            )
            
            record = {
                "University": academy,
                "Program": course_name,
                "City": city,
                "Subject": subject,
                "Beginning_Semester": beginning,
                "Duration": duration,
                "Teaching_Language": languages,
                "Tuition_Fees": tuition,
                "Application_Deadline": deadline,
                "Program_Link": full_link,
                "Support_Services": support,
                "Details": details_summary
            }
            extracted_data.append(record)
            
            if idx <= 5 or idx % 25 == 0 or idx == len(courses_raw):
                print(f"[{idx}/{len(courses_raw)}] {academy} — {course_name} ({city})")

        # Save to CSV
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            df.to_csv(output_csv, index=False, encoding="utf-8-sig")
            print("\n" + "=" * 70)
            print(f"[+] Success! Extracted and saved {len(df)} programs to '{output_csv}'.")
            print("=" * 70)
            return extracted_data
        else:
            print("[!] No program data was extracted.")
            return []

    except Exception as e:
        print(f"[!] Scraper encountered an error: {e}")
        return []


if __name__ == "__main__":
    run_scraper()