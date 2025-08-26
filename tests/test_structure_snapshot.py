from __future__ import annotations

import json
from pathlib import Path

from ingest.structure_extractor import extract_minutes_structure


def test_structure_snapshot() -> None:
    rec_path = Path("tests/fixtures/sample_minutes_01.json")
    snap_path = Path("tests/fixtures/snapshots/structure_sample01.json")
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    ms = extract_minutes_structure(rec)
    current = ms.model_dump()
    expected = json.loads(snap_path.read_text(encoding="utf-8"))
    assert current == expected

