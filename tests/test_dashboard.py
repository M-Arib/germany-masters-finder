import datetime as dt
import json
import re

import pandas as pd

from germany_masters import config, dashboard


def _committed_data() -> pd.DataFrame:
    return pd.read_csv(config.DATA_CSV, dtype=str).fillna("")


def test_committed_data_has_expected_columns():
    df = _committed_data()
    for column in ("University", "Program_Name", "QS_2026_Rank", "Application_Deadline",
                   "Tuition_Fees_Detail", "Application_Method_Raw", "UniAssist_Evidence", "Course_Content"):
        assert column in df.columns


def test_programmes_are_in_scope_and_complete():
    rows = dashboard.programmes(_committed_data())
    assert rows, "no programmes selected"
    for p in rows:
        assert p["focus"] in ("AI & ML", "Robotics", "Data Science", "CS with AI track")
        assert p["uniAssist"] in ("full", "vpd", "maybe", "none")
        assert p["daad"].startswith("https://www2.daad.de/")
        assert p["why"].endswith(".")


def test_render_embeds_valid_json():
    rows = dashboard.programmes(_committed_data())
    html = dashboard.render(rows, dt.date(2026, 10, 10))
    payload = re.search(r"const DATA = (.*?);\n", html).group(1).replace("<\\/", "</")
    data = json.loads(payload)
    assert data["built"] == "2026-10-10"
    assert len(data["programmes"]) == len(rows)
    assert "/*__DATA__*/" not in html
