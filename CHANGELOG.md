# Changelog

## [0.2.0] – 2026-10-10

### Changed
- Restructured into an installable package (`src/germany_masters`) with one command: `python -m germany_masters {scrape,build,all}`.
- Data moved to `data/`, the published dashboard to `docs/`, the page template to `templates/`.
- GitHub Pages now serves from `docs/`.
- Results are sorted by QS World University Rankings 2026.

### Added
- Unit tests for date, fee, semester-fee, uni-assist, skill and focus parsing, and an offline test of the DAAD page parser.
- CI on every push (ruff + pytest on Python 3.10 and 3.12).
- Weekly automatic data refresh via GitHub Actions.
- Issue forms for data corrections and bugs, a pull-request template, `CONTRIBUTING.md`.

### Removed
- The invented "German rank" table and its placeholder QS numbers. Only verified QS 2026 ranks remain.
- The duplicate list-only scraper (`daad_scrapper.py`) and its CSV.

## [0.1.0] – 2026-10-10

### Added
- DAAD scraper for Summer 2027 English-taught master's programmes, including detail pages.
- Researched application opening dates for 33 programmes DAAD lists without one.
- Dashboard grouped by admission status (closing soon / open / opening soon / closed) with QS rank, skills, non-EU cost per semester, uni-assist warnings and a one-line note per programme.
