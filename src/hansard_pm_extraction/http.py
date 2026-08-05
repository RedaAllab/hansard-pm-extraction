"""Shared async HTTP client helpers: bounded concurrency, retry, and the API's
own soft-error handling (HTTP 200 with an error body instead of a real status).
"""

import asyncio
import datetime as dt
import logging
from pathlib import Path

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from hansard_pm_extraction.config import (
    MAX_PAGE_SIZE,
    REQUEST_DELAY_SECONDS,
    RETRYABLE_STATUS_CODES,
)

log = logging.getLogger("hansard_pm_extraction")


class TransientAPIError(Exception):
    """The API reported a failure inside an HTTP 200 body. Worth retrying."""


class PermanentAPIError(Exception):
    """The request itself is invalid. Retrying cannot fix it."""


def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    return isinstance(exc, (httpx.TransportError, TransientAPIError))


@retry(
    retry=retry_if_exception(is_retryable),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(6),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
async def get_search(
    client: httpx.AsyncClient, semaphore: asyncio.Semaphore, url: str, params: dict
) -> dict:
    """GET a hansard-api search endpoint. Expects a `Results` list in the body."""
    take = params.get("take")
    if take is not None and take > MAX_PAGE_SIZE:
        raise PermanentAPIError(f"take={take} exceeds the API cap of {MAX_PAGE_SIZE}")

    async with semaphore:
        resp = await client.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        await asyncio.sleep(REQUEST_DELAY_SECONDS)
    if "Results" not in payload:
        raise TransientAPIError(f"API returned no Results for {url} params={params}: {payload}")
    return payload


@retry(
    retry=retry_if_exception(is_retryable),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(6),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
async def get_json(
    client: httpx.AsyncClient, semaphore: asyncio.Semaphore, url: str, params: dict | None = None
) -> dict:
    """GET any other endpoint returning a JSON object (no `Results` shape check)."""
    async with semaphore:
        resp = await client.get(url, params=params or {}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        await asyncio.sleep(REQUEST_DELAY_SECONDS)
    return payload


def configure_logging(logs_dir: Path) -> Path:
    """Log to stdout and to a timestamped file, one file per run (see CLAUDE.md §9:
    overwriting a single log file destroys the record of a killed run's progress).
    """
    logs_dir = Path(logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    run_id = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H-%M-%S")
    log_path = logs_dir / f"run_{run_id}.log"

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[stream_handler, file_handler], force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    return log_path
