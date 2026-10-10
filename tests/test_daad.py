from pathlib import Path

from germany_masters import config, daad

FIXTURE = (Path(__file__).parent / "fixtures" / "detail_page.html").read_text(encoding="utf-8")


def test_summer_dates_ignore_winter_period():
    data = daad.parse_detail_html(FIXTURE)
    assert data["Summer_App_Start_Date"] == "15 May"
    assert data["Summer_App_Deadline"] == "15 July"
    assert "winter" in data["Winter_App_Period"].lower()
    assert "non-EU" in data["Summer_App_Period_NonEU"]


def test_more_information_field_does_not_overwrite_periods():
    data = daad.parse_detail_html(FIXTURE)
    assert "Please find more details" not in data["Summer_App_Period_NonEU"]


def test_tuition_amount_survives_description_field():
    data = daad.parse_detail_html(FIXTURE)
    assert "1,500 EUR" in data["Tuition_Fees_Detail"]
    assert data["Tuition_Fees_Note"].startswith("Please find")


def test_course_content_combines_description_and_organisation():
    data = daad.parse_detail_html(FIXTURE)
    assert "machine learning" in data["Course_Content"]
    assert "reinforcement learning" in data["Course_Content"]


def test_links_and_uni_assist_evidence():
    data = daad.parse_detail_html(FIXTURE)
    assert data["Official_Course_Website"] == "https://example-university.de/msc-ai"
    assert data["Contact_Email"] == "master@example-university.de"
    assert data["Submit_Application_Via"] == "uni-assist"
    assert "VPD" in data["UniAssist_Evidence"]


def test_until_deadline_without_start():
    html = """<dl><dt>Application periods</dt><dd>The following is valid for applicants from:
              all countries For the summer semester: until 30 November</dd></dl>"""
    data = daad.parse_detail_html(html)
    assert data["Summer_App_Deadline"] == "30 November"
    assert data["Summer_App_Start_Date"] == "Not specified"


def test_search_params_enforce_intake_and_page_size():
    params = daad.search_params(config.TARGET_URL)
    assert params["bgn[]"] == [config.SEMESTER_CODE]
    assert params["limit"] == [str(config.PAGE_SIZE)]
    assert "offset" not in params
    assert all(values for values in params.values())
