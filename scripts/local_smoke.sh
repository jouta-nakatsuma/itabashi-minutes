#!/usr/bin/env bash
set -euo pipefail

# ==== 設定（必要なら上書き）====
PORT_API=${PORT_API:-8000}
PORT_UI=${PORT_UI:-8599}
DB=${DB:-var/minutes.db}

# ==== 必須コマンド ====
need() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1"; exit 1; }; }
need poetry; need curl; need jq
mkdir -p var dist

# ==== 依存導入（UI込み）====
poetry install --only main,dev --with app >/dev/null

# Streamlitの既知相性回避（protobufは<5を推奨）
if poetry run python - <<'PY' >/dev/null 2>&1; then :; else poetry run pip install -q "protobuf>=3.20,<5"; fi
import importlib, sys
try:
    import google.protobuf as pb
    from packaging.version import Version
    assert Version(getattr(pb, "__version__", "0")) < Version("5")
except Exception:
    sys.exit(1)
PY

# ==== DB作成（無ければ tests/fixtures から投入）====
if [[ ! -s "$DB" ]]; then
  echo "[build] creating DB from tests/fixtures -> $DB"
  poetry run catalog-load --src tests/fixtures --db "$DB"
fi

# ==== API起動 ====
echo "[run] API -> http://127.0.0.1:${PORT_API}"
poetry run api-serve --db "$DB" --host 127.0.0.1 --port "$PORT_API" &
API_PID=$!
trap 'kill $API_PID >/dev/null 2>&1 || true; kill ${UI_PID:-0} >/dev/null 2>&1 || true' EXIT

# API待機
for i in {1..30}; do
  curl -sf "http://127.0.0.1:${PORT_API}/search?limit=1" >/dev/null && break
  sleep 0.3
done

# APIクイック検証
echo "[check] highlight"
curl -sf "http://127.0.0.1:${PORT_API}/search?q=給食&limit=5&order_by=relevance" \
  | jq -r '.items[0].snippet' | grep -q '<em>' && echo "  OK: <em>あり" || echo "  NG: <em>なし"
echo "[check] paging meta"
curl -sf "http://127.0.0.1:${PORT_API}/search?limit=3&offset=3" | jq '.page,.has_next'

# ==== UI起動（公式コマンド; ui-serveは使わない）====
echo "[run] UI -> http://127.0.0.1:${PORT_UI}"
IM_API_BASE="http://127.0.0.1:${PORT_API}" \
poetry run python -m streamlit run app/streamlit_app.py \
  --server.address 127.0.0.1 \
  --server.port "${PORT_UI}" \
  --server.headless true \
  --browser.gatherUsageStats false &
UI_PID=$!

# UI待機
for i in {1..40}; do
  curl -sf "http://127.0.0.1:${PORT_UI}" >/dev/null && break
  sleep 0.25
done
echo "[open] UI ready: http://127.0.0.1:${PORT_UI}"
echo "      （終了は Ctrl+C。両プロセスは自動で停止します）"

# 前面で待機
wait

