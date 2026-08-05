"""Centralized configuration: paths, API parameters, and the PM name list.

PM tenure windows are never hardcoded here. They are resolved at run time from
the Members API (see pm_tenures.py) and joined against speeches temporally,
per CLAUDE.md §9 - static lookups would silently misattribute speeches around
transition dates.
"""

from pathlib import Path

HANSARD_API_BASE = "https://hansard-api.parliament.uk"
CONTRIBUTIONS_ENDPOINT = f"{HANSARD_API_BASE}/search/contributions/{{contribution_type}}.json"

MEMBERS_API_BASE = "https://members-api.parliament.uk/api"
MEMBERS_SEARCH_ENDPOINT = f"{MEMBERS_API_BASE}/Members/Search"
BIOGRAPHY_ENDPOINT = f"{MEMBERS_API_BASE}/Members/{{member_id}}/Biography"

# Member ids are looked up at run time (not hardcoded) so there's no risk of
# a stale id. Keyed by the commonly known name; the search_name is what the
# Members API actually indexes when it differs (e.g. Liz Truss is registered
# as "Elizabeth Truss").
PM_NAMES: dict[str, str] = {
    "Boris Johnson": "Boris Johnson",
    "Liz Truss": "Elizabeth Truss",
    "Rishi Sunak": "Rishi Sunak",
    "Keir Starmer": "Keir Starmer",
    "Andy Burnham": "Andy Burnham",
}

MAX_PAGE_SIZE = 100  # API silently errors above ~100-140, see CLAUDE.md §9
PAGE_SIZE = MAX_PAGE_SIZE
REQUEST_DELAY_SECONDS = 0.3
DEFAULT_CONCURRENCY = 5

RETRYABLE_STATUS_CODES = frozenset({408, 425, 429, 500, 502, 503, 504})

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CORPUS_DIR = DATA_DIR / "corpus"
LOGS_DIR = PROJECT_ROOT / "logs"

CONTRIBUTION_TYPE = "Spoken"
HOUSE = "Commons"
