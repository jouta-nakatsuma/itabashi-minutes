#!/usr/bin/env bash
set -euo pipefail
trap 'tail -n +1 logs/nightly.log || true' EXIT

mkdir -p dist logs
: > logs/nightly.log
echo "[nightly] start $(date -Iseconds)" | tee -a logs/nightly.log

# Crawl -> produce NDJSON
poetry run itabashi-crawler --out dist/documents.ndjson 2>&1 | tee -a logs/nightly.log

# Build catalog/index
poetry run catalog-load --in dist/documents.ndjson --duck dist/catalog.duckdb --index dist/index.json 2>&1 | tee -a logs/nightly.log

# Emit a compact JSON summary for downstream parsing
python - <<'PY' | tee -a logs/nightly.log
import json, os
idx = "dist/index.json"
size = os.path.getsize(idx) if os.path.exists(idx) else 0
print(json.dumps({"index_size": size}, ensure_ascii=False))
PY

