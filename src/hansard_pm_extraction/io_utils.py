"""Atomic NDJSON writes: write to a `.part` file, fsync, then os.replace onto
the final path, so a killed process never leaves a truncated file mistaken
for a complete one (see CLAUDE.md §9).
"""

import json
import os
from pathlib import Path


def write_ndjson_atomic(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part_path = path.with_suffix(path.suffix + ".part")
    part_path.unlink(missing_ok=True)
    with open(part_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(part_path, path)


def read_ndjson(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]
