#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "== clean =="
rm -rf dist var && mkdir -p dist var

echo "== crawl (real site, small) =="
PYTHONPATH="$(pwd)" poetry run python -m crawler.itabashi_spider

echo "== split array json -> per-file =="
python - <<'PY'
import json, os, pathlib, hashlib
src="crawler/sample/sample_minutes.json"
dst=pathlib.Path("dist/crawl"); dst.mkdir(parents=True, exist_ok=True)
data=json.load(open(src,"r",encoding="utf-8"))
for i, rec in enumerate(data, 1):
    md=str(rec.get("meeting_date") or "unknown")
    com=(rec.get("committee") or "unknown").replace("/","-")
    h=hashlib.sha1(json.dumps(rec, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:8]
    path=dst / f"{md}_{com}_{i:03d}_{h}.json"
    json.dump(rec, open(path,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("files:", len(list(dst.glob("*.json"))))
PY

echo "== load to sqlite =="
poetry run catalog-load --src dist/crawl --db var/minutes.db

echo "== sanity check =="
poetry run python - <<'PY'
import sqlite3
conn=sqlite3.connect("var/minutes.db"); c=conn.execute("SELECT COUNT(*) FROM minutes")
print("minutes rows:", c.fetchone()[0])
PY

echo "== start api (tty1) =="
echo "Run in another terminal:"
echo "  poetry run api-serve --db var/minutes.db --host 127.0.0.1 --port 8000"
echo
echo "== start UI (tty2) =="
echo "  IM_API_BASE=http://127.0.0.1:8000 poetry run python -m streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8599"
echo
echo "Then open http://127.0.0.1:8599 and try: 給食 / 陳情 / 所管事務調査 / 文教児童委員会"

