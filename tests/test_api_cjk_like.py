from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any, Dict

from fastapi.testclient import TestClient

from api.main import create_app


def setup_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "minutes.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sql = Path("catalog/schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)
        # minutes
        conn.execute(
            "INSERT INTO minutes(id, meeting_date, committee, title, page_url, pdf_url) VALUES (12, '2025-04-01', 'その他', '令和7年度 議会交際費', 'p12', 'pdf12')"
        )
        conn.execute(
            "INSERT INTO minutes(id, meeting_date, committee, title, page_url, pdf_url) VALUES (6, '2025-05-01', 'その他', '行政視察受入れのご案内', 'p6', 'pdf6')"
        )
        conn.execute(
            "INSERT INTO minutes(id, meeting_date, committee, title, page_url, pdf_url) VALUES (3, '2025-07-01', 'その他', '議会報告会', 'p3', 'pdf3')"
        )
        # agenda items
        conn.execute("INSERT INTO agenda_items(id, minutes_id, agenda_item, order_no) VALUES (101, 12, '（案件）', 1)")
        conn.execute("INSERT INTO agenda_items(id, minutes_id, agenda_item, order_no) VALUES (102, 6, '（案件）', 1)")
        conn.execute("INSERT INTO agenda_items(id, minutes_id, agenda_item, order_no) VALUES (103, 3, '（案件）', 1)")
        # speeches (external content FTS)
        conn.execute(
            "INSERT INTO speeches(id, minutes_id, agenda_item_id, speaker, role, speech_text) VALUES (1001, 12, 101, '事務局', '説明', 'その他 令和7年度 議会交際費')"
        )
        conn.execute(
            "INSERT INTO speeches(id, minutes_id, agenda_item_id, speaker, role, speech_text) VALUES (1002, 6, 102, '事務局', '説明', 'その他 行政視察受入れのご案内')"
        )
        conn.execute(
            "INSERT INTO speeches(id, minutes_id, agenda_item_id, speaker, role, speech_text) VALUES (1003, 3, 103, '事務局', '説明', 'その他 議会報告会')"
        )
        # Rebuild FTS explicitly (do not rely on triggers)
        conn.execute("INSERT INTO speeches_fts(speeches_fts) VALUES('rebuild');")
        conn.commit()
    return db_path


def test_cjk_like_fallback_hits(tmp_path: Path) -> None:
    db_path = setup_db(tmp_path)
    app = create_app(str(db_path))
    client = TestClient(app)

    # 完全語（FTSヒット）
    r = client.get("/search", params={"q": "議会交際費"})
    assert r.status_code == 200
    data: Dict[str, Any] = r.json()
    assert data["total"] >= 1
    assert any(it["id"] == 12 for it in data["items"])

    # 部分語（LIKEフォールバックで拾う）
    r = client.get("/search", params={"q": "交際費"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(it["id"] == 12 for it in data["items"])

    # 別語（LIKEフォールバックで拾う）
    r = client.get("/search", params={"q": "行政視察"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(it["id"] == 6 for it in data["items"])

    # 既存ケース
    r = client.get("/search", params={"q": "議会報告会"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(it["id"] == 3 for it in data["items"])

    # ヒットなしは空JSON
    r = client.get("/search", params={"q": "test"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []

