"""Search target, intake cycle and file locations."""

from pathlib import Path

# --- Search ------------------------------------------------------------------
# Set up a search on the DAAD website and paste the result URL here.
# Empty parameters are dropped; the semester and page size are enforced below.
TARGET_URL = (
    "https://www2.daad.de/deutschland/studienangebote/international-programmes/en/result/"
    "?q=&degree%5B%5D=2&lang%5B%5D=2&subjectGroup%5B%5D=193&cert=&admReq=&langExamPC=&langExamLC="
    "&langExamSC=&fos%5B%5D=226&langDeAvailable=&langEnAvailable=&lvlEn%5B%5D=&modStd%5B%5D="
    "&cit%5B%5D=&tyi%5B%5D=&ins%5B%5D=&fee=&bgn%5B%5D=2&dat%5B%5D=&prep_subj%5B%5D="
    "&prep_degree%5B%5D=&sort=4&dur=&subjects%5B%5D=226&subjects%5B%5D=229&subjects%5B%5D=232"
    "&subjects%5B%5D=233&subjects%5B%5D=236&subjects%5B%5D=547&subjects%5B%5D=548&limit=10&offset=&display=list"
)

DAAD_BASE_URL = "https://www2.daad.de"
SEARCH_API_URL = f"{DAAD_BASE_URL}/deutschland/studienangebote/international-programmes/api/solr/en/search.json"
DETAIL_URL = f"{DAAD_BASE_URL}/deutschland/studienangebote/international-programmes/en/detail/{{course_id}}/"
RESULT_PAGE_URL = f"{DAAD_BASE_URL}/deutschland/studienangebote/international-programmes/en/result/"

# --- Intake cycle --------------------------------------------------------------
INTAKE_NAME = "Summer 2027"
SEMESTER_CODE = "2"  # DAAD "bgn[]": 1 = winter semester, 2 = summer semester
# Deadlines without a year are placed in the application season of this intake:
# months >= CYCLE_SPLIT_MONTH belong to CYCLE_FIRST_YEAR, earlier months to the year after.
CYCLE_FIRST_YEAR = 2026
CYCLE_SPLIT_MONTH = 5

# --- Scraping ------------------------------------------------------------------
PAGE_SIZE = 500
MAX_WORKERS = 6
REQUEST_TIMEOUT = 30
RETRIES = 3

# --- Files -----------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_CSV = ROOT / "data" / "summer_2027.csv"
TEMPLATE_HTML = ROOT / "templates" / "dashboard.html"
SITE_HTML = ROOT / "docs" / "index.html"  # served by GitHub Pages
FRAGMENT_HTML = ROOT / "build" / "dashboard_fragment.html"  # page body without <html>/<head>, for embedding
