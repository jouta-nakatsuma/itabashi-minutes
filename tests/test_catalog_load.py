from __future__ import annotations

import sqlite3
from pathlib import Path

from catalog.load import load_directory


def test_catalog_load_e2e(tmp_path: Path) -> None:
    # Prepare temp DB and source
    db_path = tmp_path / "var" / "minutes.db"
    src_dir = Path("tests/fixtures")

    total, inserted, skipped = load_directory(db_path, src_dir)
    assert total >= 1
    assert inserted >= 1

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM minutes")
        assert cur.fetchone()[0] == 1

        cur = conn.execute("SELECT COUNT(*) FROM agenda_items")
        assert cur.fetchone()[0] >= 2

        cur = conn.execute("SELECT COUNT(*) FROM speeches")
        assert cur.fetchone()[0] >= 4

        # FTS
        cur = conn.execute(
            "SELECT COUNT(*) FROM speeches_fts WHERE speeches_fts MATCH '教育長 OR 給食'"
        )
        assert cur.fetchone()[0] >= 2

        # Filters
        cur = conn.execute(
            "SELECT COUNT(*) FROM minutes WHERE meeting_date=? AND committee=?",
            ("2025-08-21", "文教児童委員会"),
        )
        assert cur.fetchone()[0] == 1

