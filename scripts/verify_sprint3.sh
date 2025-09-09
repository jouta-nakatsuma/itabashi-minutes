#!/usr/bin/env bash
set -euo pipefail

IM_API_BASE="${IM_API_BASE:-http://127.0.0.1:8000}"

echo "[verify] Sprint 3 quick checks"
echo "[verify] API base: ${IM_API_BASE}"

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "missing command: $1"; exit 1; }; }
need_cmd curl
need_cmd jq

# API readiness (health surrogate)
if ! curl -fsS "${IM_API_BASE}/search?limit=1" >/dev/null; then
  echo "[verify] API not ready at ${IM_API_BASE}"
  exit 1
fi
echo "[verify] API ready"

fail=false

# 1) relevance + snippet <em>
echo "[verify] /search q=給食, order_by=relevance"
resp1="$(curl -fsS "${IM_API_BASE}/search?q=給食&limit=5&order_by=relevance")"
snippet="$(echo "${resp1}" | jq -r '.items[0].snippet // ""')"
if echo "${snippet}" | grep -q '<em>'; then
  echo "[ok] snippet contains <em>"
else
  echo "[ng] snippet lacks <em>"
  fail=true
fi

# 2) pagination meta
echo "[verify] /search limit=3&offset=3"
resp2="$(curl -fsS "${IM_API_BASE}/search?limit=3&offset=3")"
page="$(echo "${resp2}" | jq -r '.page')"
has_next="$(echo "${resp2}" | jq -r '.has_next')"
echo "[info] page=${page} has_next=${has_next}"

# 3) MCP quick readiness (best-effort)
echo "[verify] MCP quick run (best-effort)"
if timeout 5s poetry run mcp-server 2>&1 | grep -q '\[MCP\] itabashi-minutes ready'; then
  echo "[ok] MCP ready line observed"
else
  echo "[warn] MCP not observed (okay if MCP extras not installed)"
fi

if [ "${fail}" = true ]; then
  echo "[result] FAILED"
  exit 1
fi

echo "[result] PASSED"

