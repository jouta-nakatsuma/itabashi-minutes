from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ingest.structure_extractor import extract_minutes_structure


def load_record(name: str) -> dict:
    p = Path("tests/fixtures") / name
    return json.loads(p.read_text(encoding="utf-8"))


def test_structure_minimum_counts() -> None:
    rec = load_record("sample_minutes_01.json")
    ms = extract_minutes_structure(rec)
    assert len(ms.agenda_items) >= 2
    total_speeches = sum(len(ai.speeches) for ai in ms.agenda_items)
    assert total_speeches >= 3


def test_first_speakers_prefix_match() -> None:
    rec = load_record("sample_minutes_01.json")
    ms = extract_minutes_structure(rec)
    speakers: List[str] = []
    for ai in ms.agenda_items:
        for sp in ai.speeches:
            speakers.append(sp.speaker)
    expected_prefix = ["中妻穣太", "教育長", "理事者", "田中太郎"]
    assert speakers[: len(expected_prefix)] == expected_prefix

