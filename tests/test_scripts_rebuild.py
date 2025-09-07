from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.rebuild_catalog import run


def _counts(db: Path) -> tuple[int, int, int, int]:
    with sqlite3.connect(db) as conn:
        def c(q: str) -> int:
            return int(conn.execute(q).fetchone()[0])
        minutes = c("SELECT COUNT(*) FROM minutes")
        agenda = c("SELECT COUNT(*) FROM agenda_items")
        speeches = c("SELECT COUNT(*) FROM speeches")
        fts_hits = c("SELECT COUNT(*) FROM speeches_fts WHERE speeches_fts MATCH '教育長 OR 給食'")
        return minutes, agenda, speeches, fts_hits


def test_rebuild_catalog_e2e(tmp_path: Path) -> None:
    db = tmp_path / "minutes.db"
    total, inserted, skipped = run(db, Path("tests/fixtures"), fresh=True, analyze=False, vacuum=False, verbose=True)
    assert inserted > 0
    minutes, agenda, speeches, fts_hits = _counts(db)
    assert minutes == 1
    assert agenda >= 2
    assert speeches >= 4
    assert fts_hits >= 2

    # re-run without fresh should still succeed
    total2, inserted2, skipped2 = run(db, Path("tests/fixtures"), fresh=False, analyze=False, vacuum=False, verbose=True)
    assert total2 >= 1
    assert inserted2 >= 0

