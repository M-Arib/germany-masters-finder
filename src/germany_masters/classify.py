"""Turns raw DAAD text into structured facts: dates, fees, skills, focus and uni-assist status."""

import datetime as dt
import re

from . import config
from .reference import APPLIED_SCIENCES_NAMES, UNI_ASSIST_OVERRIDES, UNI_FACTS

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
CORE_SKILLS = {"Machine Learning", "Deep Learning", "Computer Vision", "NLP", "Reinforcement Learning",
               "Robotics", "Autonomous Systems", "Data Science", "Data Mining", "Big Data & Cloud"}

# Name/subject words that make a programme clearly AI / ML / Robotics / Data
FOCUS_PATTERNS = [
    ("Robotics", r"robot|mechatron|autonomous|intelligent mechatronic"),
    ("AI & ML", r"artificial intelligence|\bai\b|machine learning|intelligent systems|cognitive|visual computing"),
    ("Data Science", r"\bdata\b|analytics"),
]
CS_WITH_AI = "CS with AI track"

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

UA_FULL_VIA_UNI_ASSIST = "Apply through uni-assist; it checks your documents and forwards them to the university"
UA_FULL_FOREIGN_DEGREES = ("Applicants with foreign degrees apply through uni-assist; "
                           "others apply on the university website")
UA_VPD = "uni-assist must pre-check your documents (VPD) before you apply on the university portal"
UA_MAYBE = "DAAD mentions uni-assist for this programme. Check the website for whether you need it"
UA_SIBLING = ("Other programmes at this university require uni-assist for foreign degrees, "
              "so it likely applies here too. Check the website")
UA_NONE = "Apply directly on the university portal (no uni-assist mentioned on DAAD)"


def is_applied_sciences(university: str) -> bool:
    name = university or ""
    return name in APPLIED_SCIENCES_NAMES or bool(
        re.search(r"applied sciences|hochschule|fachhochschule|SRH", name, re.I))


def skills_for(text: str) -> list[str]:
    return [label for label, pattern in SKILLS if re.search(pattern, text, re.I)]


def focus_for(name: str, subject: str, skills: list[str]):
    """AI & ML / Robotics / Data Science / CS with AI track, or None if not relevant."""
    for haystack in (name, subject):  # the programme name decides first
        for label, pattern in FOCUS_PATTERNS:
            if re.search(pattern, haystack, re.I):
                return label
    if len([s for s in skills if s in CORE_SKILLS]) >= 3:
        return CS_WITH_AI
    return None


def parse_date(text, role: str, deadline: dt.date | None = None) -> dt.date | None:
    """Parses '15 January', '1 October 2026', 'Mid-November 2026', 'June 2026 (approx.)'.

    Missing years are inferred from the intake's application cycle (see config).
    A start date without a year is placed on or before its deadline.
    """
    if not isinstance(text, str):
        return None
    t = text.replace(" ", " ").strip()
    if not t or t.lower().startswith(("not ", "please", "rolling", "until places")):
        return None

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
    elif role == "start" and deadline:
        year = deadline.year if month <= deadline.month else deadline.year - 1
    else:
        year = config.CYCLE_FIRST_YEAR if month >= config.CYCLE_SPLIT_MONTH else config.CYCLE_FIRST_YEAR + 1
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def non_eu_fee(detail, overview) -> int | None:
    """Tuition per semester for non-EU applicants in EUR, or None if unknown."""
    d = re.sub(r"\s+", " ", str(detail))
    if d.strip().lower().startswith("none") or str(overview).lower().startswith("no tuition"):
        return 0
    for pattern in (r"non-EU countries[^0-9]*?([\d,]+) EUR", r"all countries[^0-9]*?([\d,]+) EUR"):
        if m := re.search(pattern, d):
            return int(m.group(1).replace(",", ""))
    return None


def semester_contribution(text) -> int | None:
    t = str(text)
    if t.strip().lower().startswith("none"):
        return 0
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*EUR", t)
    return round(float(m.group(1).replace(",", ""))) if m else None


def uni_assist_for(university: str, raw_via, evidence) -> tuple[str, str]:
    """Returns (level, explanation). level: full | vpd | maybe | none."""
    if university in UNI_ASSIST_OVERRIDES:
        return UNI_ASSIST_OVERRIDES[university]
    raw, ev = str(raw_via).lower(), str(evidence).lower()
    if "apply via uni-assist" in raw:
        return "full", UA_FULL_VIA_UNI_ASSIST
    if "uni-assist" in raw:
        return "full", UA_FULL_FOREIGN_DEGREES
    if re.search(r"vpd|vorprüfungsdokumentation|preliminary (review )?documentation|checked by uni-assist|verified by",
                 ev):
        return "vpd", UA_VPD
    if "uni-assist" in ev:
        return "maybe", UA_MAYBE
    return "none", UA_NONE


def why_note(university: str, skills: list[str], focus: str, free: bool) -> str:
    """One sentence on why to pick this programme over others."""
    top = [s for s in skills if s in CORE_SKILLS][:2]
    angle = (f"the curriculum covers {' and '.join(top)}" if top
             else "it gives a broad computer-science base you can steer toward AI electives")
    cost = ", and there are no tuition fees" if free else ""
    if fact := UNI_FACTS.get(university):
        return f"{fact[0].upper()}{fact[1:]}; {angle}{cost}."
    kind = "an applied-sciences" if is_applied_sciences(university) else "a research"
    if focus == CS_WITH_AI:
        return f"A computer-science degree at {kind} university; {angle}{cost}."
    return f"A dedicated {focus} degree at {kind} university; {angle}{cost}."


def shorten(text, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"
