# Contributing

Thanks for helping. Most useful contributions are **data corrections**: a wrong deadline can cost an applicant a whole semester.

## Reporting wrong data

Open a [data correction issue](https://github.com/M-Arib/germany-masters-finder/issues/new?template=data-correction.yml) with a link to the **official** university or DAAD page. Third-party sites (aggregators, agents, forums) often disagree with each other, so they can't be used as the only source.

## Development setup

```bash
git clone https://github.com/M-Arib/germany-masters-finder.git
cd germany-masters-finder
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -e ".[dev]"
```

Run the checks before opening a pull request:

```bash
ruff check .
pytest
```

## Where things live

| Change | File |
|---|---|
| Application opening dates, QS ranks, university facts, fee and uni-assist overrides | `src/germany_masters/reference.py` |
| Which programmes count as AI / ML / Robotics / Data, skill tags | `src/germany_masters/classify.py`, `dashboard.py` |
| Reading DAAD pages | `src/germany_masters/daad.py` (add a test with a trimmed page in `tests/fixtures/`) |
| Search, intake semester, year | `src/germany_masters/config.py` |
| Dashboard layout and behaviour | `templates/dashboard.html` |

`data/` and `docs/index.html` are generated. Don't edit them by hand; run `python -m germany_masters all` (or `build`) instead. Maintainers publish fresh data with `.\scripts\refresh.ps1`.

## Adding an opening date

Add an entry to `KNOWN_APPLICATION_OPENINGS` in `reference.py`:

```python
{"university": "University of Example", "program": "Data Science",   # program=None: all programmes
 "start": "1 November 2026", "deadline": "15 January 2027",
 "source": "https://www.uni-example.de/master/application",          # official page
 "note": "Non-EU applicants; EU deadline is 15 March"},
```

Use "approx.", "Mid-", "Early" or "expected" in `start` when the university doesn't give an exact day; the dashboard marks those with "≈".

## Style

- Python 3.10+, formatted to pass `ruff check` (line length 120).
- Keep user-facing text plain and specific. Don't state anything about a university that you can't link to a source.
