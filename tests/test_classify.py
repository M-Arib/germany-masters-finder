import datetime as dt

import pytest

from germany_masters import classify


@pytest.mark.parametrize(("text", "expected"), [
    ("30 November", dt.date(2026, 11, 30)),       # autumn deadline: first year of the cycle
    ("15 January", dt.date(2027, 1, 15)),         # winter deadline: following year
    ("15 January 2027", dt.date(2027, 1, 15)),
    ("1 March 2027", dt.date(2027, 3, 1)),
    ("Please enquire", None),
    ("Until places are filled", None),
    ("", None),
])
def test_parse_deadline(text, expected):
    assert classify.parse_date(text, "deadline") == expected


@pytest.mark.parametrize(("text", "expected"), [
    ("Mid-November 2026", dt.date(2026, 11, 15)),
    ("Late September 2026", dt.date(2026, 9, 25)),
    ("Early December 2026 (expected)", dt.date(2026, 12, 5)),
    ("June 2026 (approx.)", dt.date(2026, 6, 1)),
    ("Rolling (open all year)", None),
    ("Not published (only deadline listed)", None),
])
def test_parse_vague_start_dates(text, expected):
    assert classify.parse_date(text, "start") == expected


def test_start_without_year_falls_before_deadline():
    deadline = dt.date(2027, 1, 15)
    assert classify.parse_date("1 December", "start", deadline) == dt.date(2026, 12, 1)
    assert classify.parse_date("1 January", "start", deadline) == dt.date(2027, 1, 1)


@pytest.mark.parametrize(("detail", "overview", "expected"), [
    ("None", "", 0),
    ("", "No tuition fees", 0),
    ("The following tuition fees apply for applicants from: non-EU countries 1,500 EUR", "", 1500),
    ("non-EU countries Switzerland United Kingdom 500 EUR EU countries 0 EUR", "", 500),
    ("The following tuition fees apply for applicants from: all countries 2,975 EUR", "", 2975),
    ("EU countries 4,500 EUR non-EU countries 6,950 EUR", "", 6950),
    ("Varied", "Tuition varies", None),
])
def test_non_eu_fee(detail, overview, expected):
    assert classify.non_eu_fee(detail, overview) == expected


@pytest.mark.parametrize(("text", "expected"), [
    ("Approx. 360 EUR", 360),
    ("Students have to pay an administrative fee of 394.30 EUR per semester", 394),
    ("None. Students may purchase a discounted semester ticket", 0),
    ("For more information, refer to: https://www.tum.de/en/studies/fees", None),
])
def test_semester_contribution(text, expected):
    assert classify.semester_contribution(text) == expected


@pytest.mark.parametrize(("raw_via", "evidence", "level"), [
    ("Please apply via uni-assist .", "", "full"),
    ("• uni-assist • Website", "", "full"),
    ("Please check this website .", "you must submit a preliminary documentation (VPD) from uni-assist", "vpd"),
    ("Please check this website .", "must have their documents checked by uni-assist in advance", "vpd"),
    ("Please check this website .", "check the uni-assist English proficiency framework", "maybe"),
    ("Please check this website .", "", "none"),
])
def test_uni_assist_levels(raw_via, evidence, level):
    assert classify.uni_assist_for("Some University", raw_via, evidence)[0] == level


def test_uni_assist_override_wins():
    assert classify.uni_assist_for("Leibniz University Hannover", "Please check this website .", "")[0] == "vpd"


def test_skills_and_focus():
    skills = classify.skills_for("Modules: deep learning, computer vision and robot manipulation")
    assert {"Deep Learning", "Computer Vision", "Robotics"} <= set(skills)
    assert classify.focus_for("Robotics, MEng", "Mechatronics", skills) == "Robotics"
    assert classify.focus_for("Data Science (MSc)", "Artificial Intelligence", []) == "Data Science"
    assert classify.focus_for("Computer Science", "Computer Science", skills) == classify.CS_WITH_AI
    assert classify.focus_for("Software Engineering", "Software Engineering", ["Security"]) is None


def test_applied_sciences_detection():
    assert classify.is_applied_sciences("Ulm University of Applied Sciences")
    assert classify.is_applied_sciences("Deggendorf Institute of Technology")
    assert not classify.is_applied_sciences("Ulm University")


def test_why_note_uses_university_fact_and_fees():
    note = classify.why_note("University of Bonn", ["Machine Learning"], "AI & ML", free=True)
    assert note.startswith("Home of the Lamarr Institute")
    assert note.endswith("no tuition fees.")
    generic = classify.why_note("Example University of Applied Sciences", [], "Robotics", free=False)
    assert generic.startswith("A dedicated Robotics degree at an applied-sciences university")
