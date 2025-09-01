from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, Tuple
import re

from ingest.structure_extractor import extract_minutes_structure

logger = logging.getLogger(__name__)


def ensure_schema(conn: sqlite3.Connection) -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(sql)


def iter_json_files(src_dir: Path) -> Iterable[Path]:
    for p in sorted(src_dir.glob("*.json")):
        if p.is_file():
            yield p


def upsert_minutes(conn: sqlite3.Connection, record: Dict) -> Tuple[int, bool]:
    """
    Insert minutes row if not exists (by unique page_url). Return (id, created).
    """
    page_url = record.get("page_url")
    cur = conn.execute("SELECT id FROM minutes WHERE page_url = ?", (page_url,))
    row = cur.fetchone()
    if row:
        return int(row[0]), False
    cur = conn.execute(
        """
        INSERT INTO minutes(meeting_date, committee, title, page_url, pdf_url, word_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            record.get("meeting_date"),
            record.get("committee"),
            record.get("title"),
            page_url,
            record.get("pdf_url"),
            int(record.get("word_count") or 0),
        ),
    )
    return int(cur.lastrowid), True


_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9f]+")


def _make_index_text(text: str) -> str:
    """Return text augmented with CJK 2-gram and 3-gram tokens for FTS matching.

    - Keeps original text so exact tokens like "教育長" (before punctuation) can match
      via unicode61 tokenization.
    - Adds 2-grams and 3-grams over contiguous CJK sequences so shorter queries like
      "給食" also match.
    """
    tokens: list[str] = []
    for m in _CJK_RE.finditer(text):
        s = m.group(0)
        # 2-grams
        for i in range(len(s) - 1):
            tokens.append(s[i : i + 2])
        # 3-grams
        for i in range(len(s) - 2):
            tokens.append(s[i : i + 3])
    if tokens:
        return f"{text}\n" + " ".join(tokens)
    return text


def load_file(conn: sqlite3.Connection, path: Path) -> Tuple[bool, bool]:
    """
    Load a single JSON file into DB.
    Returns (inserted, skipped)
    """
    obj = json.loads(path.read_text(encoding="utf-8"))
    ms = extract_minutes_structure(obj)

    # Flatten fields and counts
    total_wc = 0
    total_speeches = 0
    for ai in ms.agenda_items:
        for sp in ai.speeches:
            total_speeches += 1
            total_wc += sum(len(p) for p in (sp.paragraphs or []))
    minutes_row = {
        "meeting_date": ms.meeting_date,
        "committee": ms.committee,
        "title": obj.get("title"),
        "page_url": ms.page_url or obj.get("page_url"),
        "pdf_url": ms.pdf_url or obj.get("pdf_url"),
        "word_count": total_wc,
    }

    conn.execute("BEGIN")
    try:
        minutes_id, created = upsert_minutes(conn, minutes_row)
        if not created:
            # If duplicate exists but current record has speeches, refresh its content
            if total_speeches > 0:
                # purge existing agenda/speeches and update minutes metadata
                conn.execute("DELETE FROM speeches WHERE minutes_id = ?", (minutes_id,))
                conn.execute("DELETE FROM agenda_items WHERE minutes_id = ?", (minutes_id,))
                conn.execute(
                    "UPDATE minutes SET meeting_date=?, committee=?, title=?, pdf_url=?, word_count=? WHERE id=?",
                    (
                        minutes_row["meeting_date"],
                        minutes_row["committee"],
                        minutes_row["title"],
                        minutes_row["pdf_url"],
                        minutes_row["word_count"],
                        minutes_id,
                    ),
                )
            else:
                conn.execute("ROLLBACK")
                return False, True

        # agenda_items -> speeches
        for ai in ms.agenda_items:
            cur_ai = conn.execute(
                """
                INSERT INTO agenda_items(minutes_id, agenda_item, order_no)
                VALUES (?, ?, ?)
                """,
                (minutes_id, ai.title, ai.order_no),
            )
            agenda_item_id = int(cur_ai.lastrowid)
            for sp in ai.speeches:
                # インデックス対象テキスト: 議題見出し + 話者名/役職 + 本文
                header_parts = [ai.title or "", sp.speaker or "", sp.role or ""]
                header = " ".join([t for t in header_parts if t]).strip()
                body = "\n".join(sp.paragraphs or [])
                raw_text = f"{header}\n{body}" if header else body
                speech_text = _make_index_text(raw_text)
                conn.execute(
                    """
                    INSERT INTO speeches(minutes_id, agenda_item_id, speaker, role, speech_text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (minutes_id, agenda_item_id, sp.speaker, sp.role, speech_text),
                )
        conn.execute("COMMIT")
        return True, False
    except Exception:
        conn.execute("ROLLBACK")
        raise


def load_directory(db_path: Path, src_dir: Path) -> Tuple[int, int, int]:
    """
    Returns (total_files, inserted, skipped)
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA busy_timeout = 5000")
        ensure_schema(conn)
        total = inserted = skipped = 0
        for p in iter_json_files(src_dir):
            total += 1
            ok, sk = load_file(conn, p)
            if ok:
                inserted += 1
            if sk:
                skipped += 1
        logger.info("Loaded files total=%d inserted=%d skipped=%d", total, inserted, skipped)
        return total, inserted, skipped


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load normalized minutes JSON into SQLite catalog with FTS5.")
    parser.add_argument("--src", default="data/normalized", help="Source directory containing JSON files")
    parser.add_argument("--db", default="var/minutes.db", help="SQLite DB path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    src_dir = Path(args.src)
    db_path = Path(args.db)
    total, inserted, _ = load_directory(db_path, src_dir)
    if inserted <= 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
