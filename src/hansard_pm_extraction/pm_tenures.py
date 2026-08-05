"""Resolve each PM's member id and Prime Minister tenure window(s) via the
Members API, rather than hardcoding dates. A PM's identity is time-bound, so
every downstream join against speeches must use these windows (CLAUDE.md §9).

Usage:
    python -m hansard_pm_extraction.pm_tenures
"""

import asyncio
import logging

import httpx

from hansard_pm_extraction.config import (
    BIOGRAPHY_ENDPOINT,
    DEFAULT_CONCURRENCY,
    MEMBERS_SEARCH_ENDPOINT,
    PM_NAMES,
    RAW_DIR,
)
from hansard_pm_extraction.http import configure_logging, get_json
from hansard_pm_extraction.io_utils import write_ndjson_atomic

log = logging.getLogger("hansard_pm_extraction.pm_tenures")

OUT_PATH = RAW_DIR / "pm_tenures.ndjson"


class MemberNotFoundError(Exception):
    """A configured PM name returned no or ambiguous results from Members API search."""


async def _resolve_member(
    client: httpx.AsyncClient, semaphore: asyncio.Semaphore, search_name: str
) -> dict:
    payload = await get_json(client, semaphore, MEMBERS_SEARCH_ENDPOINT, {"Name": search_name})
    items = payload.get("items", [])
    if not items:
        raise MemberNotFoundError(f"No Members API result for {search_name!r}")
    if len(items) > 1:
        log.warning("Multiple Members API results for %r, using the first: %s", search_name, items)
    return items[0]["value"]


def _prime_minister_posts(government_posts: list[dict]) -> list[dict]:
    """Filter governmentPosts entries whose title starts with 'Prime Minister'.

    Matches "Prime Minister, First Lord of the Treasury..." style variants as
    well as the plain title, without matching unrelated posts that merely
    mention the office (e.g. "Parliamentary Under-Secretary to the Prime
    Minister").
    """
    return [p for p in government_posts if p["name"].startswith("Prime Minister")]


async def resolve_pm_tenure(
    client: httpx.AsyncClient, semaphore: asyncio.Semaphore, name: str, search_name: str
) -> dict:
    member = await _resolve_member(client, semaphore, search_name)
    member_id = member["id"]

    bio_url = BIOGRAPHY_ENDPOINT.format(member_id=member_id)
    bio_payload = await get_json(client, semaphore, bio_url)
    posts = _prime_minister_posts(bio_payload["value"].get("governmentPosts", []))
    if not posts:
        raise MemberNotFoundError(f"{name!r} (member id {member_id}) has no 'Prime Minister' post")
    if len(posts) > 1:
        # Not expected among the five PMs in scope, but a returning PM (e.g. a
        # future second term) would produce this - fail loudly rather than
        # silently picking one window.
        raise ValueError(f"{name!r} has {len(posts)} 'Prime Minister' tenure windows: {posts}")

    post = posts[0]
    return {
        "pm_name": name,
        "member_id": member_id,
        "party": member.get("latestParty", {}).get("name"),
        "tenure_start": post["startDate"],
        "tenure_end": post["endDate"],
    }


async def resolve_all_pm_tenures(concurrency: int = DEFAULT_CONCURRENCY) -> list[dict]:
    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[
                resolve_pm_tenure(client, semaphore, name, search_name)
                for name, search_name in PM_NAMES.items()
            ],
            return_exceptions=True,
        )

    tenures = []
    for name, result in zip(PM_NAMES, results, strict=True):
        if isinstance(result, Exception):
            log.error("Failed to resolve tenure for %r: %s", name, result)
            continue
        tenures.append(result)
    return tenures


def main() -> None:
    configure_logging(RAW_DIR.parent.parent / "logs")
    tenures = asyncio.run(resolve_all_pm_tenures())
    write_ndjson_atomic(OUT_PATH, tenures)
    log.info("Resolved %d/%d PM tenures -> %s", len(tenures), len(PM_NAMES), OUT_PATH)


if __name__ == "__main__":
    main()
