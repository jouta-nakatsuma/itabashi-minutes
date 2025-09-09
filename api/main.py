from __future__ import annotations

import argparse
import sqlite3
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import uvicorn
import re

DB_PATH: Optional[Path] = None


def get_conn():
    if DB_PATH is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        yield conn
    finally:
        conn.close()


def normalize_fts_query(q: str) -> str:
    """
    Normalize free-text input into FTS5 MATCH expression.
    - If user includes explicit quotes or OR, keep as-is (except escape quotes).
    - Otherwise, split by whitespace (including full-width) and AND-join tokens.
    - Escape double quotes by doubling them.
    """
    raw = q.strip()
    if not raw:
        return raw
    # escape quotes
    safe = raw.replace('"', '""')
    # if OR is present, respect it but normalize whitespace
    if re.search(r"\bOR\b", safe, flags=re.IGNORECASE):
        return re.sub(r"\s+", " ", safe)
    # remove explicit AND operators (treat as implicit AND via whitespace)
    safe = re.sub(r"\bAND\b", " ", safe, flags=re.IGNORECASE)
    # split on ASCII/Full-width spaces and collapse
    tokens = re.split(r"[\s\u3000]+", safe)
    tokens = [t for t in tokens if t]
    return " ".join(tokens)


# CJK detection and FTS query shaping (for Japanese search)
_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")

def is_cjk_query(q: str) -> bool:
    return bool(_CJK_RE.search(q or ""))

def to_fts_query(q: str, cjk: bool) -> str:
    if not q:
        return ""
    if not cjk:
        return q  # keep current behavior for non-CJK
    terms = [t for t in re.split(r"[\s\u3000]+", q) if t]
    if not terms:
        return q + "*"
    return " AND ".join(f"{t}*" for t in terms)


class SearchItem(BaseModel):
    id: int
    meeting_date: Optional[str] = None
    committee: Optional[str] = None
    title: Optional[str] = None
    hit_count: int = 0
    snippet: str = ""


class SearchResponse(BaseModel):
    items: List[SearchItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    page: int
    has_next: bool


class SpeechDTO(BaseModel):
    speaker: Optional[str] = None
    role: Optional[str] = None
    paragraphs: List[str] = Field(default_factory=list)


class AgendaItemDTO(BaseModel):
    order_no: int
    title: str
    speeches: List[SpeechDTO] = Field(default_factory=list)


class DocumentResponse(BaseModel):
    id: int
    meeting_date: Optional[str] = None
    committee: Optional[str] = None
    title: Optional[str] = None
    page_url: Optional[str] = None
    pdf_url: Optional[str] = None
    agenda_items: List[AgendaItemDTO] = Field(default_factory=list)


def create_app(db_path: str) -> FastAPI:
    global DB_PATH
    DB_PATH = Path(db_path)
    app = FastAPI(title="Itabashi Minutes API")

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/search", response_model=SearchResponse)
    def search(
        q: Optional[str] = Query(default=None),
        committee: Optional[str] = Query(default=None),
        date_from: Optional[date] = Query(default=None),
        date_to: Optional[date] = Query(default=None),
        limit: int = Query(default=10, ge=1, le=100),
        offset: int = Query(default=0, ge=0, le=10000),
        order_by: Literal["relevance", "date", "committee"] = Query(default="date"),
        order: Literal["asc", "desc"] = Query(default="desc"),
        conn: sqlite3.Connection = Depends(get_conn),
    ):
        params = {
            "committee": committee,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "limit": limit,
            "offset": offset,
        }

        items: List[SearchItem] = []
        total = 0
        order_dir = "ASC" if order.lower() == "asc" else "DESC"

        if q:
            norm_q = normalize_fts_query(q)
            cjk = is_cjk_query(norm_q)
            if cjk:
                # CJK: wildcard + LIKE fallback; merge and dedupe
                fts_q = to_fts_query(norm_q, cjk=True)
                params_q = dict(params)
                params_q["fts_query"] = fts_q
                params_q["use_like"] = 1
<<<<<<< HEAD
                params_q["like_pattern"] = f"%{q}%"  # use raw q for LIKE (per review)
=======
                params_q["like_pattern"] = f"%{q}%"  # use raw q for LIKE
                # ORDER BY (safe whitelist)
>>>>>>> 44ad7f9 (feat(api): CJK search fallback (FTS wildcard + LIKE) + tests + docs)
                if order_by == "relevance":
                    order_clause = f"COALESCE(f.hits, 0) {order_dir}, mn.meeting_date DESC, mn.id DESC"
                elif order_by == "committee":
                    order_clause = f"mn.committee COLLATE NOCASE {order_dir}, mn.meeting_date DESC, mn.id DESC"
                else:  # date
                    order_clause = f"mn.meeting_date {order_dir}, mn.id DESC"

                total_sql = """
                WITH f AS (
                  SELECT sp.minutes_id AS mid, COUNT(*) AS hits
                  FROM speeches_fts
                  JOIN speeches sp ON speeches_fts.rowid = sp.id
                  WHERE speeches_fts MATCH :fts_query
                  GROUP BY sp.minutes_id
                ),
                l AS (
                  SELECT sp.minutes_id AS mid
                  FROM speeches sp
                  WHERE (:use_like = 1) AND sp.speech_text LIKE :like_pattern ESCAPE '\\'
                ),
                u AS (
                  SELECT mid FROM f
                  UNION ALL
                  SELECT mid FROM l
                ),
                mset AS (
                  SELECT DISTINCT mid FROM u
                )
                SELECT COUNT(*) AS cnt
                FROM minutes mn
                JOIN mset ms ON ms.mid = mn.id
                WHERE (:committee IS NULL OR mn.committee = :committee)
                  AND (:date_from IS NULL OR mn.meeting_date >= :date_from)
                  AND (:date_to   IS NULL OR mn.meeting_date <= :date_to)
                """
                cur = conn.execute(total_sql, params_q)
                total = int(cur.fetchone()[0])

                sql = f"""
                WITH f AS (
                  SELECT sp.minutes_id AS mid, COUNT(*) AS hits
                  FROM speeches_fts
                  JOIN speeches sp ON speeches_fts.rowid = sp.id
                  WHERE speeches_fts MATCH :fts_query
                  GROUP BY sp.minutes_id
                ),
                l AS (
                  SELECT sp.minutes_id AS mid
                  FROM speeches sp
                  WHERE (:use_like = 1) AND sp.speech_text LIKE :like_pattern ESCAPE '\\'
                ),
                u AS (
                  SELECT mid FROM f
                  UNION ALL
                  SELECT mid FROM l
                ),
                mset AS (
                  SELECT DISTINCT mid FROM u
                )
                SELECT
                  mn.id,
                  mn.meeting_date,
                  mn.committee,
                  mn.title,
                  COALESCE(f.hits, 0) AS hit_count,
                  COALESCE(
                    (
                      SELECT snippet(speeches_fts, -1, '<em>', '</em>', '…', 10)
                      FROM speeches_fts
                      JOIN speeches sp2 ON sp2.id = speeches_fts.rowid
                      WHERE speeches_fts MATCH :fts_query
                        AND sp2.minutes_id = mn.id
                      ORDER BY sp2.id ASC
                      LIMIT 1
                    ),
                    (
                      SELECT substr(sp3.speech_text, 1, 120)
                      FROM speeches sp3
                      WHERE (:use_like = 1)
                        AND sp3.minutes_id = mn.id
                        AND sp3.speech_text LIKE :like_pattern ESCAPE '\\'
                      ORDER BY sp3.id ASC
                      LIMIT 1
                    ),
                    (
                      SELECT substr(sp4.speech_text, 1, 120)
                      FROM speeches sp4
                      WHERE sp4.minutes_id = mn.id
                      ORDER BY sp4.id ASC
                      LIMIT 1
                    )
                  ) AS snippet
                FROM minutes mn
                JOIN mset ms ON ms.mid = mn.id
                LEFT JOIN f ON f.mid = mn.id
                WHERE (:committee IS NULL OR mn.committee = :committee)
                  AND (:date_from IS NULL OR mn.meeting_date >= :date_from)
                  AND (:date_to   IS NULL OR mn.meeting_date <= :date_to)
                ORDER BY {order_clause}
                LIMIT :limit OFFSET :offset
                """
                cur = conn.execute(sql, params_q)
                for row in cur.fetchall():
                    items.append(
                        SearchItem(
                            id=row["id"],
                            meeting_date=row["meeting_date"],
                            committee=row["committee"],
                            title=row["title"],
                            hit_count=row["hit_count"] or 0,
                            snippet=(row["snippet"] or ""),
                        )
                    )
            else:
                params_q = dict(params)
                params_q["q"] = norm_q
                # ORDER BY (safe whitelist)
                if order_by == "relevance":
                    order_clause = f"m.hits {order_dir}, mn.meeting_date DESC, mn.id DESC"
                elif order_by == "committee":
                    order_clause = f"mn.committee COLLATE NOCASE {order_dir}, mn.meeting_date DESC, mn.id DESC"
                else:  # date
                    order_clause = f"mn.meeting_date {order_dir}, mn.id DESC"

                # total
                total_sql = """
                WITH matched AS (
                  SELECT sp.minutes_id AS mid
                  FROM speeches_fts
                  JOIN speeches sp ON sp.id = speeches_fts.rowid
                  WHERE speeches_fts MATCH :q
                  GROUP BY sp.minutes_id
                )
                SELECT COUNT(*) AS cnt
                FROM minutes mn
                JOIN matched m ON m.mid = mn.id
                WHERE (:committee IS NULL OR mn.committee = :committee)
                  AND (:date_from IS NULL OR mn.meeting_date >= :date_from)
                  AND (:date_to   IS NULL OR mn.meeting_date <= :date_to)
                """
                cur = conn.execute(total_sql, params_q)
                total = int(cur.fetchone()[0])

                sql = f"""
                WITH matched AS (
                  SELECT sp.minutes_id AS mid,
                         COUNT(*) AS hits
                  FROM speeches_fts
                  JOIN speeches sp ON sp.id = speeches_fts.rowid
                  WHERE speeches_fts MATCH :q
                  GROUP BY sp.minutes_id
                )
                SELECT mn.id, mn.meeting_date, mn.committee, mn.title,
                       m.hits AS hit_count,
                       (
                         SELECT snippet(speeches_fts, -1, '<em>', '</em>', '…', 10)
                         FROM speeches_fts
                         JOIN speeches sp2 ON sp2.id = speeches_fts.rowid
                         WHERE speeches_fts MATCH :q
                           AND sp2.minutes_id = mn.id
                         ORDER BY sp2.id ASC
                         LIMIT 1
                       ) AS snippet
                FROM minutes mn
                JOIN matched m ON m.mid = mn.id
                WHERE (:committee IS NULL OR mn.committee = :committee)
                  AND (:date_from IS NULL OR mn.meeting_date >= :date_from)
                  AND (:date_to   IS NULL OR mn.meeting_date <= :date_to)
                ORDER BY {order_clause}
                LIMIT :limit OFFSET :offset
                """
                cur = conn.execute(sql, params_q)
                for row in cur.fetchall():
                    items.append(
                        SearchItem(
                            id=row["id"],
                            meeting_date=row["meeting_date"],
                            committee=row["committee"],
                            title=row["title"],
                            hit_count=row["hit_count"] or 0,
                            snippet=(row["snippet"] or ""),
                        )
                    )
        else:
            # ORDER BY without query (relevance -> fallback to date)
            if order_by == "committee":
                order_clause = f"mn.committee COLLATE NOCASE {order_dir}, mn.meeting_date DESC, mn.id DESC"
            else:
                order_clause = f"mn.meeting_date {order_dir}, mn.id DESC"
            # total
            total_sql = """
            SELECT COUNT(*) AS cnt
            FROM minutes mn
            WHERE (:committee IS NULL OR mn.committee = :committee)
              AND (:date_from IS NULL OR mn.meeting_date >= :date_from)
              AND (:date_to   IS NULL OR mn.meeting_date <= :date_to)
            """
            cur = conn.execute(total_sql, params)
            total = int(cur.fetchone()[0])

            sql = f"""
            SELECT mn.id, mn.meeting_date, mn.committee, mn.title,
                   0 AS hit_count,
                   substr((SELECT speech_text
                           FROM speeches
                           WHERE minutes_id = mn.id
                           ORDER BY id ASC LIMIT 1), 1, 120) AS snippet
            FROM minutes mn
            WHERE (:committee IS NULL OR mn.committee = :committee)
              AND (:date_from IS NULL OR mn.meeting_date >= :date_from)
              AND (:date_to   IS NULL OR mn.meeting_date <= :date_to)
            ORDER BY {order_clause}
            LIMIT :limit OFFSET :offset
            """
            cur = conn.execute(sql, params)
            for row in cur.fetchall():
                items.append(
                    SearchItem(
                        id=row["id"],
                        meeting_date=row["meeting_date"],
                        committee=row["committee"],
                        title=row["title"],
                        hit_count=0,
                        snippet=(row["snippet"] or ""),
                    )
                )
        page = (offset // limit) + 1 if limit > 0 else 1
        has_next = (offset + len(items)) < total
        return SearchResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            page=page,
            has_next=has_next,
        )

    @app.get("/document/{doc_id}", response_model=DocumentResponse)
    def get_document(doc_id: int, conn: sqlite3.Connection = Depends(get_conn)):
        cur = conn.execute(
            "SELECT id, meeting_date, committee, title, page_url, pdf_url FROM minutes WHERE id = ?",
            (doc_id,),
        )
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="document not found")
        doc = DocumentResponse(
            id=r["id"],
            meeting_date=r["meeting_date"],
            committee=r["committee"],
            title=r["title"],
            page_url=r["page_url"],
            pdf_url=r["pdf_url"],
            agenda_items=[],
        )
        # agenda_items
        cur = conn.execute(
            "SELECT id, order_no, agenda_item FROM agenda_items WHERE minutes_id = ? ORDER BY order_no ASC",
            (doc_id,),
        )
        agenda_rows = cur.fetchall()
        id_to_agenda: dict[int, AgendaItemDTO] = {}
        for ar in agenda_rows:
            ai = AgendaItemDTO(order_no=ar["order_no"], title=ar["agenda_item"], speeches=[])
            doc.agenda_items.append(ai)
            id_to_agenda[int(ar["id"])] = ai

        # speeches: one-shot then group by agenda_item_id
        cur = conn.execute(
            """
            SELECT agenda_item_id, speaker, role, speech_text
            FROM speeches
            WHERE minutes_id = ?
            ORDER BY agenda_item_id ASC, id ASC
            """,
            (doc_id,),
        )
        for sp in cur.fetchall():
            paragraphs = [p.strip() for p in (sp["speech_text"] or "").split("\n") if p.strip()]
            s = SpeechDTO(speaker=sp["speaker"], role=sp["role"], paragraphs=paragraphs)
            ag_id = int(sp["agenda_item_id"])
            if ag_id in id_to_agenda:
                id_to_agenda[ag_id].speeches.append(s)

        return doc

    return app


def serve(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Serve Itabashi Minutes API")
    parser.add_argument("--db", default="var/minutes.db", help="SQLite DB path")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(list(argv) if argv is not None else None)

    app = create_app(args.db)
    uvicorn.run(app, host=args.host, port=args.port)


__all__ = ["create_app", "serve"]
