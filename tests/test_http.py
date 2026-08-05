import httpx
import pytest

from hansard_pm_extraction.http import PermanentAPIError, TransientAPIError, is_retryable


@pytest.mark.parametrize("status", [408, 425, 429, 500, 502, 503, 504])
def test_is_retryable_retryable_statuses(status):
    request = httpx.Request("GET", "https://example.com")
    response = httpx.Response(status, request=request)
    exc = httpx.HTTPStatusError("boom", request=request, response=response)
    assert is_retryable(exc)


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_is_retryable_non_retryable_statuses(status):
    request = httpx.Request("GET", "https://example.com")
    response = httpx.Response(status, request=request)
    exc = httpx.HTTPStatusError("boom", request=request, response=response)
    assert not is_retryable(exc)


def test_is_retryable_transient_api_error():
    assert is_retryable(TransientAPIError("no Results"))


def test_is_retryable_permanent_api_error_not_retried():
    assert not is_retryable(PermanentAPIError("take too large"))


def test_is_retryable_transport_error():
    assert is_retryable(httpx.ConnectTimeout("timed out"))


def test_is_retryable_unrelated_exception():
    assert not is_retryable(ValueError("unrelated"))
