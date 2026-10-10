"""Builds the dashboard: filters to AI / ML / Robotics / Data programmes and renders the HTML page."""

import datetime as dt
import json
import re

import pandas as pd

from . import config
from .classify import (
    CS_WITH_AI,
    UA_SIBLING,
    focus_for,
    non_eu_fee,
    parse_date,
    semester_contribution,
    shorten,
    skills_for,
    uni_assist_for,
    why_note,
)
from .reference import FEE_OVERRIDES

# Management-style programmes that only mention data in passing
EXCLUDED_NAMES = r"supply chain|project management|\bsap\b|business information systems|business intelligence"
EXCLUDED_SUBJECTS = {"Music", "Political Science", "Biology", "Molecular Biology", "Psychology",
                     "Geography", "Marketing, Distribution", "Business Administration",
                     "Media Design", "Multimedia Design", "Neuropsychology"}
# General CS degrees whose short DAAD text hides strong AI/ML options at the university
FORCE_INCLUDE = {("University of Bonn", "Computer Science"), ("Saarland University", "Computer Science (MSc)")}

PAGE_HEAD = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    "<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n"
    "</head>\n<body>\n"
)
PAGE_TAIL = "\n</body>\n</html>\n"


def programme(r: pd.Series) -> dict | None:
    """Dashboard record for one CSV row, or None if the programme is out of scope."""
    if r["Subject_Field"] in EXCLUDED_SUBJECTS or re.search(EXCLUDED_NAMES, r["Program_Name"], re.I):
        return None
    skills = skills_for(f"{r['Program_Name']} {r['Course_Content']}")
    focus = focus_for(r["Program_Name"], r["Subject_Field"], skills)
    if (r["University"], r["Program_Name"]) in FORCE_INCLUDE:
        focus = focus or CS_WITH_AI
    if not focus:
        return None

    deadline = parse_date(r["Application_Deadline"], "deadline")
    start = parse_date(r["Application_Start_Date"], "start", deadline)
    fee = non_eu_fee(r["Tuition_Fees_Detail"], r["Tuition_Fees_Overview"])
    fee_note = ""
    for (university, name), (value, note) in FEE_OVERRIDES.items():
        if fee is None and university == r["University"] and name.lower() in r["Program_Name"].lower():
            fee, fee_note = value, note
    ua_level, ua_label = uni_assist_for(r["University"], r["Application_Method_Raw"], r["UniAssist_Evidence"])
    website = str(r["Official_Course_Website"])

    return {
        "university": r["University"],
        "program": r["Program_Name"],
        "city": r["City"],
        "focus": focus,
        "qs": str(r["QS_2026_Rank"]),
        "skills": skills,
        "why": why_note(r["University"], skills, focus, fee == 0),
        "start": start.isoformat() if start else None,
        "deadline": deadline.isoformat() if deadline else None,
        "startText": r["Application_Start_Date"],
        "deadlineText": r["Application_Deadline"],
        "rolling": str(r["Application_Start_Date"]).lower().startswith("rolling"),
        "approx": bool(re.search(r"approx|mid|late|early|expected", str(r["Application_Start_Date"]), re.I)),
        "notes": r["Application_Notes"],
        "startSource": r["Application_Start_Source"],
        "fee": fee,
        "feeNote": fee_note,
        "contribution": semester_contribution(r["Semester_Contribution"]),
        "free": fee == 0,
        "uniAssist": ua_level,
        "uniAssistLabel": ua_label,
        "duration": r["Duration"],
        "language": r["Teaching_Language"],
        "langReq": shorten(r["Language_Requirements"], 180),
        "website": website if website.startswith("http") else "",
        "daad": r["DAAD_Link"],
    }


def programmes(df: pd.DataFrame) -> list[dict]:
    rows = [p for _, r in df.iterrows() if (p := programme(r))]
    # uni-assist rules are usually university-wide: flag siblings of programmes that need it
    needs_ua = {p["university"] for p in rows if p["uniAssist"] in ("full", "vpd")}
    for p in rows:
        if p["uniAssist"] == "none" and p["university"] in needs_ua:
            p["uniAssist"], p["uniAssistLabel"] = "maybe", UA_SIBLING
    return rows


def render(rows: list[dict], built: dt.date) -> str:
    """Page body (no <html>/<head>) with the data embedded."""
    template = config.TEMPLATE_HTML.read_text(encoding="utf-8")
    payload = json.dumps({"built": built.isoformat(), "programmes": rows}, ensure_ascii=False)
    return template.replace("/*__DATA__*/null", payload.replace("</", "<\\/"))


def run(source=config.DATA_CSV) -> list[dict]:
    df = pd.read_csv(source, dtype=str).fillna("")
    rows = programmes(df)
    body = render(rows, dt.date.today())

    config.SITE_HTML.parent.mkdir(parents=True, exist_ok=True)
    config.SITE_HTML.write_text(PAGE_HEAD + body + PAGE_TAIL, encoding="utf-8", newline="\n")
    config.FRAGMENT_HTML.parent.mkdir(parents=True, exist_ok=True)
    config.FRAGMENT_HTML.write_text(body, encoding="utf-8", newline="\n")

    print(f"[*] {len(rows)} AI / ML / Robotics / Data programmes selected out of {len(df)}")
    print(f"[+] Wrote {config.SITE_HTML.relative_to(config.ROOT)}")
    return rows
