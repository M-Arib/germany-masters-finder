"""
Builds master_programmes.html from summer_2027.csv:
filters to AI / ML / Robotics / Data programmes, extracts the skills taught,
parses application dates and writes a one-line "why choose it" note.

Run after summer_2027.py:  python build_dashboard.py
"""
import re
import sys
import json
import datetime as dt
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

INPUT_CSV = "summer_2027.csv"
TEMPLATE = "dashboard_template.html"
OUTPUT_HTML = "master_programmes.html"

# QS World University Rankings 2026, as listed at
# https://www.learngermanonline.org/top-german-universities/ (checked Oct 2026).
# Universities missing here are not in the QS 2026 table.
QS_2026 = {
    "Technical University of Munich": "22",
    "RWTH Aachen University": "105",
    "University of Freiburg": "201",
    "University of Bonn": "207",
    "University of Tübingen": "215",
    "Dresden University of Technology": "218",
    "TUD Dresden University of Technology": "218",
    "University of Göttingen": "243",
    "Technical University of Darmstadt": "253",
    "University of Stuttgart": "310",
    "University of Münster": "350",
    "Julius-Maximilians-Universität Würzburg": "416",
    "Leibniz University Hannover": "433",
    "University of Konstanz": "440",
    "University of Bayreuth": "448",
    "University of Potsdam": "477",
    "Ulm University": "546",
    "Kiel University": "618",
    "Saarland University": "635",
    "TU Dortmund University": "673",
    "University of Regensburg": "691",
    "Technische Universität Braunschweig": "711-720",
    "Marburg University": "771-780",
    "University of Rostock": "851-900",
    "RPTU University Kaiserslautern-Landau": "1201-1400",
    "University of Siegen": "1201-1400",
}

# Skill vocabulary: label -> regex over programme name + DAAD course description
SKILLS = [
    ("Machine Learning", r"machine learning|maschinelles lernen"),
    ("Deep Learning", r"deep learning|neural network"),
    ("Computer Vision", r"computer vision|image (processing|analysis|understanding)|visual computing"),
    ("NLP", r"natural language|\bnlp\b|language technolog|text mining|large language model|\bllms?\b"),
    ("Reinforcement Learning", r"reinforcement learning"),
    ("Robotics", r"robot"),
    ("Autonomous Systems", r"autonomous|self-driving|automated driving"),
    ("Data Science", r"data science|data analy|analytics"),
    ("Big Data & Cloud", r"big data|data engineering|distributed (systems|computing)|cloud|high.performance computing"),
    ("Data Mining", r"data mining|knowledge discovery"),
    ("Statistics", r"statistic|probabilit|stochastic"),
    ("Optimization", r"optimi[sz]ation"),
    ("Embedded & IoT", r"embedded|internet of things|\biot\b|cyber.physical"),
    ("Control & Automation", r"control (theory|engineering|systems)|automation"),
    ("Signal Processing", r"signal processing|sensor"),
    ("HCI", r"human.computer|\bhci\b|human.machine"),
    ("Cognitive Science", r"cognitive|neuroscien"),
    ("Security", r"security|cryptograph"),
    ("Bioinformatics", r"bioinformatic|genom"),
    ("Quantum", r"quantum"),
    ("Software Engineering", r"software engineering|software development"),
    ("Algorithms & Theory", r"algorithm|theoretical computer"),
]
CORE = {"Machine Learning", "Deep Learning", "Computer Vision", "NLP", "Reinforcement Learning",
        "Robotics", "Autonomous Systems", "Data Science", "Data Mining", "Big Data & Cloud"}

# Name/subject words that make a programme clearly AI / ML / Robotics / Data
FOCUS_PATTERNS = [
    ("Robotics", r"robot|mechatron|autonomous|intelligent mechatronic"),
    ("AI & ML", r"artificial intelligence|\bai\b|machine learning|intelligent systems|cognitive|visual computing"),
    ("Data Science", r"\bdata\b|analytics"),
]
# Management-style programmes that only mention data in passing
EXCLUDED_NAMES = r"supply chain|project management|\bsap\b|business information systems|business intelligence"

# General CS degrees whose short DAAD text hides strong AI/ML options at the university
FORCE_INCLUDE = {("University of Bonn", "Computer Science"), ("Saarland University", "Computer Science (MSc)")}

EXCLUDED_SUBJECTS = {"Music", "Political Science", "Biology", "Molecular Biology", "Psychology",
                     "Geography", "Marketing, Distribution", "Business Administration",
                     "Media Design", "Multimedia Design", "Neuropsychology"}

# One-line context per university. Only well-established facts.
UNI_FACTS = {
    "Technical University of Munich": "Germany's highest-ranked university (QS #22), home to the Munich Institute of Robotics and Machine Intelligence (MIRMI)",
    "RWTH Aachen University": "Germany's flagship engineering university with deep industry and automation ties",
    "University of Bonn": "home of the Lamarr Institute for Machine Learning and AI, one of Germany's national AI centres",
    "TU Dortmund University": "co-host of the Lamarr Institute for Machine Learning and AI, one of Germany's national AI centres",
    "University of Tübingen": "part of Cyber Valley and the Tübingen AI Center, among Europe's strongest machine-learning clusters",
    "University of Stuttgart": "part of Cyber Valley, one of Europe's largest AI research consortia, next to a major automotive industry",
    "Technical University of Darmstadt": "a founding member of hessian.AI, the state AI centre of Hesse",
    "University of Freiburg": "a leading research university (QS #201) with well-known robotics and machine-learning groups",
    "Saarland University": "on the same campus as DFKI and two Max Planck Institutes for computer science",
    "University of Göttingen": "a top-250 research university with a strong data-science and scientific-computing ecosystem",
    "Leibniz University Hannover": "home of the L3S Research Center for AI and web science",
    "RPTU University Kaiserslautern-Landau": "located next to a DFKI site, Germany's largest AI research institute",
    "University of Potsdam": "closely linked to the Hasso Plattner Institute for digital engineering",
    "Paderborn University": "home of the Heinz Nixdorf Institute for intelligent technical systems",
    "Osnabrück University": "home of one of Germany's first and best-known Cognitive Science institutes",
    "Julius-Maximilians-Universität Würzburg": "home of the CAIDAS centre for AI and data science",
    "Dresden University of Technology": "a TU9 Excellence University and host of the ScaDS.AI centre",
    "Technische Hochschule Ingolstadt": "home of the AImotion Bavaria institute for AI in mobility",
    "Hochschule Bonn-Rhein-Sieg": "an applied-sciences university known for its autonomous-systems and robotics research",
    "SRH University": "a private university with a project-based block teaching model and rolling admission",
}

# DAAD says "Varied" for these; values from the universities' public fee rules
FEE_OVERRIDES = {
    ("Technical University of Munich", "Informatics"): (6000, "TUM non-EU fee; same school as Data Engineering (€6,000). Confirm at tum.de/en/studies/fees"),
    ("University of Stuttgart", "Computer Science"): (1500, "Baden-Württemberg charges non-EU students €1,500 per semester"),
}

# uni-assist requirements found outside DAAD (see KNOWN_APPLICATION_OPENINGS sources in summer_2027.py)
UNI_ASSIST_OVERRIDES = {
    "Leibniz University Hannover": ("vpd", "Non-EU applicants need a uni-assist VPD first (processing up to 8 weeks)"),
}


def non_eu_fee(detail, overview):
    """Tuition per semester for non-EU applicants in EUR, or None if unknown."""
    d = re.sub(r"\s+", " ", str(detail))
    if d.strip().lower().startswith("none") or str(overview).lower().startswith("no tuition"):
        return 0
    for pat in (r"non-EU countries[^0-9]*?([\d,]+) EUR", r"all countries[^0-9]*?([\d,]+) EUR"):
        m = re.search(pat, d)
        if m:
            return int(m.group(1).replace(",", ""))
    return None


def semester_contribution(text):
    t = str(text)
    if t.strip().lower().startswith("none"):
        return 0
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*EUR", t)
    return round(float(m.group(1).replace(",", ""))) if m else None


def uni_assist_for(uni, raw_via, evidence):
    """Returns (level, label). level: full | vpd | maybe | none."""
    if uni in UNI_ASSIST_OVERRIDES:
        lvl, note = UNI_ASSIST_OVERRIDES[uni]
        return lvl, note
    raw, ev = str(raw_via).lower(), str(evidence).lower()
    if "apply via uni-assist" in raw:
        return "full", "Apply through uni-assist; it checks your documents and forwards them to the university"
    if "uni-assist" in raw:
        return "full", "Applicants with foreign degrees apply through uni-assist; others apply on the university website"
    if re.search(r"vpd|vorprüfungsdokumentation|preliminary (review )?documentation|checked by uni-assist|verified by", ev):
        return "vpd", "uni-assist must pre-check your documents (VPD) before you apply on the university portal"
    if "uni-assist" in ev:
        return "maybe", "DAAD mentions uni-assist for this programme. Check the website for whether you need it"
    return "none", "Apply directly on the university portal (no uni-assist mentioned on DAAD)"


TODAY = dt.date.today()
MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def skills_for(text):
    found = []
    for label, pat in SKILLS:
        if re.search(pat, text, re.I):
            found.append(label)
    return found


def focus_for(name, subject, skills):
    # The programme name decides first; DAAD's subject field only as a fallback
    for hay in (name, subject):
        for label, pat in FOCUS_PATTERNS:
            if re.search(pat, hay, re.I):
                return label
    core = [s for s in skills if s in CORE]
    if len(core) >= 3:
        return "CS with AI track"
    return None


def parse_date(text, role, deadline=None):
    """Parses '15 January', '1 October 2026', 'Mid-November 2026', 'June 2026 (approx.)'.
    Missing years are inferred for the Summer 2027 intake cycle."""
    if not isinstance(text, str):
        return None
    t = text.replace(" ", " ").strip()
    if not t or t.lower().startswith(("not ", "please", "rolling", "until places")):
        return None
    day = None
    m = re.search(r"(\d{1,2})\.?\s+([A-Za-z]+)(?:\s+(\d{4}))?", t)
    if m and m.group(2).lower() in MONTHS:
        day, month, year = int(m.group(1)), MONTHS[m.group(2).lower()], m.group(3)
    else:
        m = re.search(r"(early|mid|late)?-?\s*([A-Za-z]+)(?:\s+(\d{4}))?", t, re.I)
        if not m or m.group(2).lower() not in MONTHS:
            return None
        day = {"early": 5, "mid": 15, "late": 25}.get((m.group(1) or "").lower(), 1)
        month, year = MONTHS[m.group(2).lower()], m.group(3)
    if year:
        year = int(year)
    elif role == "deadline":
        # Summer 2027 deadlines run from about May 2026 to April 2027
        year = 2026 if month >= 5 else 2027
    elif deadline:
        year = deadline.year if month <= deadline.month else deadline.year - 1
    else:
        year = 2026 if month >= 5 else 2027
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def why_note(r, skills, focus, free):
    uni = r["University"]
    fact = UNI_FACTS.get(uni)
    top = [s for s in skills if s in CORE][:2]
    angle = (f"the curriculum covers {' and '.join(top)}" if top
             else "it gives a broad computer-science base you can steer toward AI electives")
    cost = ", and there are no tuition fees" if free else ""
    if fact:
        return f"{fact[0].upper()}{fact[1:]}; {angle}{cost}."
    kind = "an applied-sciences" if re.search(r"UAS|Applied", str(r["University_Type"])) else "a research"
    if focus in ("AI & ML", "Robotics", "Data Science"):
        return f"A dedicated {focus} degree at {kind} university; {angle}{cost}."
    return f"A computer-science degree at {kind} university; {angle}{cost}."


def short(text, n=220):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def main():
    df = pd.read_csv(INPUT_CSV).fillna("")
    rows = []
    for _, r in df.iterrows():
        if r["Subject_Field"] in EXCLUDED_SUBJECTS or re.search(EXCLUDED_NAMES, r["Program_Name"], re.I):
            continue
        text = f"{r['Program_Name']} {r['Course_Content']}"
        skills = skills_for(text)
        focus = focus_for(r["Program_Name"], r["Subject_Field"], skills)
        if (r["University"], r["Program_Name"]) in FORCE_INCLUDE:
            focus = focus or "CS with AI track"
        if not focus:
            continue

        deadline = parse_date(r["Application_Deadline"], "deadline")
        start = parse_date(r["Application_Start_Date"], "start", deadline)
        rolling = str(r["Application_Start_Date"]).lower().startswith("rolling")
        fees = str(r["Tuition_Fees_Overview"])
        fee = non_eu_fee(r["Tuition_Fees_Detail"], fees)
        fee_note = ""
        for (u, prog), (val, note) in FEE_OVERRIDES.items():
            if fee is None and u == r["University"] and prog.lower() in r["Program_Name"].lower():
                fee, fee_note = val, note
        contribution = semester_contribution(r["Semester_Contribution"])
        free = fee == 0
        ua_level, ua_label = uni_assist_for(r["University"], r["Application_Method_Raw"], r["UniAssist_Evidence"])

        rows.append({
            "university": r["University"],
            "program": r["Program_Name"],
            "city": r["City"],
            "focus": focus,
            "qs": QS_2026.get(r["University"], ""),
            "uniType": r["University_Type"],
            "skills": skills,
            "why": why_note(r, skills, focus, free),
            "start": start.isoformat() if start else None,
            "deadline": deadline.isoformat() if deadline else None,
            "startText": r["Application_Start_Date"],
            "deadlineText": r["Application_Deadline"],
            "rolling": rolling,
            "approx": bool(re.search(r"approx|mid|late|early|expected", str(r["Application_Start_Date"]), re.I)),
            "notes": r["Application_Notes"],
            "startSource": r["Application_Start_Source"],
            "fees": fees,
            "fee": fee,
            "feeNote": fee_note,
            "contribution": contribution,
            "free": free,
            "uniAssist": ua_level,
            "uniAssistLabel": ua_label,
            "duration": r["Duration"],
            "language": r["Teaching_Language"],
            "langReq": short(r["Language_Requirements"], 180),
            "method": "uni-assist" if "uni-assist" in str(r["Application_Method"]).lower() else "University portal",
            "website": r["Official_Course_Website"] if str(r["Official_Course_Website"]).startswith("http") else "",
            "daad": r["DAAD_Link"],
        })

    # uni-assist rules are usually university-wide: flag siblings of programmes that need it
    ua_unis = {x["university"] for x in rows if x["uniAssist"] in ("full", "vpd")}
    for x in rows:
        if x["uniAssist"] == "none" and x["university"] in ua_unis:
            x["uniAssist"] = "maybe"
            x["uniAssistLabel"] = ("Other programmes at this university require uni-assist for foreign degrees, "
                                   "so it likely applies here too. Check the website")

    missing_qs = sorted({x["university"] for x in rows if not x["qs"]})
    print(f"[*] {len(rows)} AI / ML / Robotics / Data programmes selected out of {len(df)}.")
    print(f"[*] Universities without a QS 2026 rank: {len(missing_qs)}")

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    payload = json.dumps({"built": TODAY.isoformat(), "programmes": rows}, ensure_ascii=False)
    html = html.replace("/*__DATA__*/null", payload.replace("</", "<\\/"))
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    # index.html is the copy GitHub Pages serves; it needs its own document skeleton
    standalone = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
        '</head>\n<body>\n' + html + '\n</body>\n</html>\n'
    )
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(standalone)
    print(f"[+] Wrote {OUTPUT_HTML} and index.html")
    return rows


if __name__ == "__main__":
    main()
