# Germany Masters Finder

A tracker for English-taught **AI, Machine Learning, Robotics and Data Science** master's programmes in Germany, built for **non-EU applicants**. Currently covers the **Summer 2027** intake (starting April 2027).

**Live dashboard:** see the GitHub Pages link in this repository's About section.

## Why this exists

The official [DAAD International Programmes](https://www2.daad.de/deutschland/studienangebote/international-programmes/en/) database is the best source, but it doesn't answer the questions applicants actually ask:

| Question | DAAD | This tracker |
|---|---|---|
| Can I apply **right now**? | ✗ | Programmes grouped into *Closing soon / Open now / Opening soon / Closed*, based on today's date |
| When does the application **open**? | Often missing | Researched from university websites, with a source link for each |
| What will it **cost me** as a non-EU student? | Spread over several fields | Tuition + semester fee per semester in one number |
| Do I need **uni-assist**? | Buried in the text | Red warning badge on every programme that needs it |
| How is the university **ranked**? | ✗ | QS World University Rankings 2026 |
| What **skills** will I learn? | Long text | Skill tags (ML, Deep Learning, Computer Vision, Robotics…) |

## How it works

```
summer_2027.py        →  summer_2027.csv          →  build_dashboard.py  →  index.html
(scrapes DAAD API +      (all 143 matching            (filters to AI/ML/       (the dashboard,
 every detail page)       programmes, ~40 fields)      Robotics/Data, adds      single static file)
                                                       ranks, costs, status)
```

- **`summer_2027.py`**: queries DAAD's search API, then fetches every programme's detail page for application periods, fees, requirements, course content and uni-assist mentions. It also holds a table of application **opening dates** researched by hand on university websites (`KNOWN_APPLICATION_OPENINGS`).
- **`build_dashboard.py`**: picks the AI / ML / Robotics / Data programmes, extracts skills, parses dates, works out non-EU costs and uni-assist status, and writes the data into `dashboard_template.html`.
- **`daad_scrapper.py`**: a simpler, list-only scraper (writes `Final_DAAD_List.csv`).

## Run it yourself

```bash
pip install -r requirements.txt
python summer_2027.py
python build_dashboard.py
```

Then open `index.html` in a browser. Admission status is calculated in the browser from today's date, so it stays current between data refreshes.

To change the search (other subjects, winter intake, other degree types), set up your search on the DAAD website and paste the result URL into `TARGET_URL` in `summer_2027.py`.

## ⚠️ Accuracy disclaimer

Deadlines, fees and requirements change every year, and some values here are estimates (marked "approx." or "expected"). **Always confirm on the official programme page before applying.** Every programme links to its DAAD listing and official website, and every researched opening date links to its source.

- Deadlines shown are for **non-EU applicants** where universities list them separately.
- "Direct application" (green) only means DAAD doesn't mention uni-assist. Check the programme website.
- Skills come from the DAAD course description; a programme may teach more than its tags show.

## Data sources

- [DAAD International Programmes](https://www2.daad.de/deutschland/studienangebote/international-programmes/en/): programme data © DAAD
- University websites: application opening dates (linked per programme)
- [QS World University Rankings 2026](https://www.topuniversities.com/world-university-rankings), via [learngermanonline.org](https://www.learngermanonline.org/top-german-universities/)

This project is not affiliated with DAAD, uni-assist or any university.

## Contributing

Found a wrong date or fee? Open an issue with a link to the official page. Corrections to opening dates go in `KNOWN_APPLICATION_OPENINGS` in `summer_2027.py`.

## License

Code: MIT. Programme data belongs to DAAD and the respective universities.
