from datetime import date, timedelta

from hansard_pm_extraction.contributions import daterange_chunks


def test_daterange_chunks_covers_full_range_without_gaps_or_overlap():
    chunks = list(daterange_chunks("2022-01-01", "2022-03-15", chunk_days=30))
    for (_, prev_end), (next_start, _) in zip(chunks, chunks[1:], strict=False):
        assert date.fromisoformat(next_start) == date.fromisoformat(prev_end) + timedelta(days=1)
    assert chunks[0][0] == "2022-01-01"
    assert chunks[-1][1] == "2022-03-15"


def test_daterange_chunks_single_day_range():
    assert list(daterange_chunks("2022-01-01", "2022-01-01", chunk_days=30)) == [
        ("2022-01-01", "2022-01-01")
    ]


def test_daterange_chunks_exact_multiple_of_chunk_size():
    chunks = list(daterange_chunks("2022-01-01", "2022-01-30", chunk_days=30))
    assert chunks == [("2022-01-01", "2022-01-30")]


def test_daterange_chunks_respects_chunk_days():
    chunks = list(daterange_chunks("2022-01-01", "2022-02-01", chunk_days=10))
    assert all(
        (date.fromisoformat(end) - date.fromisoformat(start)).days <= 9 for start, end in chunks
    )
