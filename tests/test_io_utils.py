import json

from hansard_pm_extraction.io_utils import read_ndjson, write_ndjson_atomic


def test_write_then_read_roundtrip(tmp_path):
    path = tmp_path / "out.ndjson"
    records = [{"a": 1}, {"a": 2}]
    write_ndjson_atomic(path, records)
    assert read_ndjson(path) == records


def test_write_ndjson_atomic_leaves_no_part_file(tmp_path):
    path = tmp_path / "out.ndjson"
    write_ndjson_atomic(path, [{"a": 1}])
    assert not path.with_suffix(path.suffix + ".part").exists()
    assert path.exists()


def test_write_ndjson_atomic_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "dir" / "out.ndjson"
    write_ndjson_atomic(path, [{"a": 1}])
    assert path.exists()


def test_write_ndjson_atomic_overwrites_cleanly(tmp_path):
    path = tmp_path / "out.ndjson"
    write_ndjson_atomic(path, [{"a": 1}, {"a": 2}])
    write_ndjson_atomic(path, [{"a": 3}])
    assert read_ndjson(path) == [{"a": 3}]


def test_write_ndjson_atomic_discards_stale_part_file(tmp_path):
    path = tmp_path / "out.ndjson"
    part_path = path.with_suffix(path.suffix + ".part")
    part_path.write_text(json.dumps({"stale": True}) + "\n")
    write_ndjson_atomic(path, [{"a": 1}])
    assert read_ndjson(path) == [{"a": 1}]
