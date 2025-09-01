from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict

from fastapi.testclient import TestClient

from api.main import create_app
from catalog.load import load_directory


def setup_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "minutes.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # apply schema
    sql = Path("catalog/schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)
    # load fixtures (Step1 sample)
    load_directory(db_path, Path("tests/fixtures"))
    return db_path


def test_health_and_search_and_document(tmp_path: Path) -> None:
    db_path = setup_db(tmp_path)
    app = create_app(str(db_path))
    client = TestClient(app)

    # health
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    # search with q
    r = client.get("/search", params={"q": "給食", "limit": 5})
    assert r.status_code == 200
    data: Dict[str, Any] = r.json()
    assert "items" in data and isinstance(data["items"], list)
    assert data["total"] >= 1
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert len(data["items"]) >= 1
    first = data["items"][0]
    for k in ["id", "meeting_date", "committee", "title", "hit_count", "snippet"]:
        assert k in first
    assert first["hit_count"] >= 1

    # search with filters only
    r = client.get(
        "/search",
        params={
            "committee": "文教児童委員会",
            "date_from": "2025-08-01",
            "date_to": "2025-08-31",
            "limit": 5,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1

    # pick an id for document
    doc_id = first["id"]
    r = client.get(f"/document/{doc_id}")
    assert r.status_code == 200
    doc = r.json()
    assert isinstance(doc.get("agenda_items"), list)
    assert len(doc["agenda_items"]) >= 2
    # somewhere speaker == 教育長
    found_kyou = any(
        any(sp.get("speaker") == "教育長" for sp in ai.get("speeches", []))
        for ai in doc["agenda_items"]
    )
    assert found_kyou

    # not found
    r = client.get("/document/99999999")
    assert r.status_code == 404


def test_search_query_normalization(tmp_path: Path) -> None:
    db_path = setup_db(tmp_path)
    app = create_app(str(db_path))
    client = TestClient(app)

    # "学校 給食" should behave like "学校 AND 給食"
    r1 = client.get("/search", params={"q": "学校 給食"})
    r2 = client.get("/search", params={"q": "学校 AND 給食"})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["total"] == r2.json()["total"]


def test_search_validation(tmp_path: Path) -> None:
    db_path = setup_db(tmp_path)
    app = create_app(str(db_path))
    client = TestClient(app)

    # invalid limit -> 422
    r = client.get("/search", params={"limit": 0})
    assert r.status_code == 422
    r = client.get("/search", params={"limit": 200})
    assert r.status_code == 422
    # invalid offset -> 422
    r = client.get("/search", params={"offset": -1})
    assert r.status_code == 422

