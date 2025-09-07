from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Tuple

from catalog.load import load_directory


def run(db_path: Path, src_dir: Optional[Path], *, fresh: bool, analyze: bool, vacuum: bool, verbose: bool) -> Tuple[int, int, int]:
    if fresh and db_path.exists():
        if verbose:
            print(f"[INFO] Removing existing DB: {db_path}")
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # choose src
    chosen_src = src_dir if src_dir and src_dir.exists() and any(src_dir.glob("*.json")) else None
    if chosen_src is None:
        fallback = Path("data/normalized")
        if not (fallback.exists() and any(fallback.glob("*.json"))):
            fallback = Path("tests/fixtures")
        chosen_src = fallback
    if verbose:
        print(f"[INFO] Using source dir: {chosen_src}")

    # apply schema
    sql = Path("catalog/schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)

    total, inserted, skipped = load_directory(db_path, chosen_src)

    with sqlite3.connect(db_path) as conn:
        def count(q: str) -> int:
            return int(conn.execute(q).fetchone()[0])

        minutes = count("SELECT COUNT(*) FROM minutes")
        agenda = count("SELECT COUNT(*) FROM agenda_items")
        speeches = count("SELECT COUNT(*) FROM speeches")
        fts_hits = count("SELECT COUNT(*) FROM speeches_fts WHERE speeches_fts MATCH '教育長 OR 給食'")

        print(f"[INFO] minutes={minutes} agenda_items={agenda} speeches={speeches} fts_hits={fts_hits}")

        if analyze:
            print("[INFO] Running ANALYZE ...")
            conn.execute("ANALYZE")
        if vacuum:
            print("[INFO] Running VACUUM ...")
            conn.execute("VACUUM")

    return total, inserted, skipped


def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Rebuild SQLite catalog from schema + JSON sources")
    ap.add_argument("--db", default="var/minutes.db")
    ap.add_argument("--src", default="data/normalized/")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--vacuum", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(list(argv) if argv is not None else None)

    db_path = Path(args.db)
    src_dir = Path(args.src) if args.src else None
    total, inserted, skipped = run(db_path, src_dir, fresh=args.fresh, analyze=args.analyze, vacuum=args.vacuum, verbose=args.verbose)

    if args.fresh:
        return 0 if inserted > 0 else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
