"""Fetch each PM's Commons Spoken contributions, bounded by their own tenure
window (temporal join at fetch time, not a static date range shared across
PMs - see CLAUDE.md §9).

Usage:
    python -m hansard_pm_extraction.contributions
"""

import argparse
import asyncio
import datetime as dt
import logging
from pathlib import Path

import httpx

from hansard_pm_extraction.config import (
    CONTRIBUTION_TYPE,
    CONTRIBUTIONS_ENDPOINT,
    DEFAULT_CONCURRENCY,
    HOUSE,
    LOGS_DIR,
    PAGE_SIZE,
    RAW_DIR,
)
from hansard_pm_extraction.http import configure_logging, get_search
from hansard_pm_extraction.io_utils import read_ndjson, write_ndjson_atomic

log = logging.getLogger("hansard_pm_extraction.contributions")

PM_TENURES_PATH = RAW_DIR / "pm_tenures.ndjson"
CONTRIBUTIONS_DIR = RAW_DIR / "contributions"


def daterange_chunks(start_date: str, end_date: str, chunk_days: int = 30):
    """Yield (chunk_start, chunk_end) date strings to keep individual requests small."""
    start = dt.date.fromisoformat(start_date)
    end = dt.date.fromisoformat(end_date)
    cur = start
    while cur <= end:
        chunk_end = min(cur + dt.timedelta(days=chunk_days - 1), end)
        yield cur.isoformat(), chunk_end.isoformat()
        cur = chunk_end + dt.timedelta(days=1)


async def fetch_member_contributions_chunk(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    member_id: int,
    start_date: str,
    end_date: str,
) -> list[dict]:
    """Fetch all Spoken Commons contributions for one member within one date chunk,
    paginating concurrently once the total result count is known.
    """
    url = CONTRIBUTIONS_ENDPOINT.format(contribution_type=CONTRIBUTION_TYPE)

    def base_params(skip: int) -> dict:
        return {
            "house": HOUSE,
            "memberId": member_id,
            "startDate": start_date,
            "endDate": end_date,
            "skip": skip,
            "take": PAGE_SIZE,
            "orderBy": "SittingDateAsc",
        }

    first_payload = await get_search(client, semaphore, url, base_params(0))
    total = first_payload.get("TotalResultCount", 0)
    all_results = list(first_payload.get("Results", []))
    if not all_results:
        return []

    remaining_skips = list(range(PAGE_SIZE, total, PAGE_SIZE))
    if remaining_skips:
        pages = await asyncio.gather(
            *[get_search(client, semaphore, url, base_params(skip)) for skip in remaining_skips],
            return_exceptions=True,
        )
        for page in pages:
            if isinstance(page, Exception):
                log.error(
                    "Failed page for member %s %s-%s: %s", member_id, start_date, end_date, page
                )
                continue
            all_results.extend(page.get("Results", []))

    return all_results


async def fetch_pm_contributions(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    pm: dict,
    cutoff_date: str,
    chunk_days: int,
    out_dir: Path,
) -> int:
    out_path = out_dir / f"{pm['pm_name'].replace(' ', '_')}.ndjson"
    if out_path.exists():
        log.info("Skipping (already ingested): %s", out_path.name)
        return 0

    start_date = pm["tenure_start"][:10]
    end_date = min(pm["tenure_end"][:10] if pm["tenure_end"] else cutoff_date, cutoff_date)

    chunk_results = await asyncio.gather(
        *[
            fetch_member_contributions_chunk(client, semaphore, pm["member_id"], c_start, c_end)
            for c_start, c_end in daterange_chunks(start_date, end_date, chunk_days)
        ],
        return_exceptions=True,
    )

    all_results = []
    for chunk in chunk_results:
        if isinstance(chunk, Exception):
            log.error("Failed chunk for %s: %s", pm["pm_name"], chunk)
            continue
        all_results.extend(chunk)

    ingested_at = dt.datetime.now(dt.UTC).isoformat()
    for r in all_results:
        r["_ingested_at"] = ingested_at
        r["_pm_name"] = pm["pm_name"]
        r["_pm_party"] = pm["party"]

    write_ndjson_atomic(out_path, all_results)
    log.info("%s: %d contributions -> %s", pm["pm_name"], len(all_results), out_path.name)
    return len(all_results)


async def async_main(cutoff_date: str, chunk_days: int, concurrency: int) -> None:
    pm_tenures = read_ndjson(PM_TENURES_PATH)
    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[
                fetch_pm_contributions(
                    client, semaphore, pm, cutoff_date, chunk_days, CONTRIBUTIONS_DIR
                )
                for pm in pm_tenures
            ],
            return_exceptions=True,
        )
    for pm, result in zip(pm_tenures, results, strict=True):
        if isinstance(result, Exception):
            log.error("Failed to fetch contributions for %s: %s", pm["pm_name"], result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cutoff-date",
        default=dt.date.today().isoformat(),
        help="Corpus cutoff date (defaults to today; documented in data_README.md at export time)",
    )
    parser.add_argument("--chunk-days", type=int, default=30)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    args = parser.parse_args()

    configure_logging(LOGS_DIR)
    asyncio.run(async_main(args.cutoff_date, args.chunk_days, args.concurrency))


if __name__ == "__main__":
    main()
