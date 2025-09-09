# Verification Cheatsheet — Sprint 3 (Complete)

目的
- 開発者/レビュアが 5〜10 分で Sprint 3 の完成物（API/UI/MCP/Nightly/抽出テスト）を横断チェックできる。
- コピペ実行可能・期待出力の確認ポイントつき。コード改変は不要。

前提
- Python 3.10 推奨（ローカルは 3.11 でも可）。Poetry 1.8.3。
- `jq`, `gh`（GitHub CLI）, `sqlite3` がインストール済み。

準備（1分）
```bash
# 依存導入（UI/MCP含む）
poetry install --only main,dev --with app,mcp
export IM_API_BASE=${IM_API_BASE:-http://127.0.0.1:8000}

# DBの用意（どちらか）
# A) Nightly成果物を使う（ネット不要）
gh run download --name "catalog-dist-YYYY-MM-DD" || echo "Nightly artifact not found; use B)"
#   DuckDB/JSONが落ちてくる前提。API用のSQLiteが必要な場合は B) で作成してください。

# B) 簡易クロール（ネット必要）
poetry run itabashi-crawler --out dist/documents.ndjson
poetry run catalog-load --in dist/documents.ndjson --db var/minutes.db
# （DuckDB/JSONも欲しければ） --duck dist/catalog.duckdb --index dist/index.json
```

API スモーク（2分）
```bash
# 別ターミナルでAPI起動
poetry run api-serve --db var/minutes.db --host 127.0.0.1 --port 8000
```
確認（別ターミナル）
```bash
# スニペットに <em> が含まれる（qあり + relevance）
curl "$IM_API_BASE/search?q=給食&limit=5&order_by=relevance" \
| jq -r '.items[0].snippet' | grep -q '<em>'

# ページングメタ
curl "$IM_API_BASE/search?limit=3&offset=3" | jq '.page,.has_next'
```
注意
- `order_by=relevance` かつ `q` 空のときは `date` にフォールバックする。

UI スモーク（2分）
```bash
poetry run ui-serve
```
手順
- キーワード検索 → `<em>` 強調を確認 → Prev/Next → 詳細 → PDFリンク。
- 注意: 「並び替え=relevance」は q あり時のみ有効。話者フィルタは limit<=10 でページ内適用。

MCP スモーク（2分）
```bash
# MCP（SDK/stdio）があれば ready 行がstderrに出る
poetry run mcp-server
# stderr: [MCP] itabashi-minutes ready (base=http://127.0.0.1:8000)
```
JSON-RPC フォールバック（SDK無環境向けの最小例）
```bash
printf '{"jsonrpc":"2.0","id":1,"method":"search_minutes","params":{"q":"給食","limit":3}}' \
| poetry run mcp-server 2>/dev/null | jq
```
期待: `items/total/limit/offset/page/has_next` が含まれる。

Nightly の確認（1分）
```bash
# 手動実行（mainに対して）
gh workflow run Nightly --ref main
gh run watch

# 成果物取得（当日の artifact 名）
gh run download --name "catalog-dist-YYYY-MM-DD"
```
メモ
- 失敗時は自動で Issue 起票。実行詳細URL: `https://github.com/${REPO}/actions/runs/${RUN_ID}`

構造抽出の回帰（2分）
```bash
poetry run pytest -q -k structure_extractor
```
しきい値（暫定）
- Precision ≥ 0.90 / Recall ≥ 0.85
- 失敗時は pytest の差分表示と、該当テストのログを参照。

トラブルシュート
- ポート競合: `lsof -i :8000` → 衝突プロセス停止。
- `.env` 未設定: `IM_API_BASE` を明示（例の通り）。
- Streamlit/MCP未導入: `poetry install --with app,mcp` を再実行。
- `gh`/`jq` 未導入: `brew install gh jq`（macOS）。
- ネットワーク: Nightlyダウンロードを使う場合は GitHub へのアクセスのみ。簡易クロールは外部サイトへのアクセスが必要。

付録: /search の主要フィールド
- items: `id, meeting_date, committee, title, hit_count, snippet(<em>…</em>)`
- meta: `total, limit, offset, page, has_next`

付録: 代表コマンド（コピペ可）
```bash
# Install
poetry install --only main,dev --with app,mcp
export IM_API_BASE=${IM_API_BASE:-http://127.0.0.1:8000}

# Build (local crawl)
poetry run itabashi-crawler --out dist/documents.ndjson
poetry run catalog-load --in dist/documents.ndjson --db var/minutes.db

# API
poetry run api-serve --db var/minutes.db --host 127.0.0.1 --port 8000
curl "$IM_API_BASE/search?q=給食&limit=5&order_by=relevance" | jq '.items[0].snippet'
curl "$IM_API_BASE/search?limit=3&offset=3" | jq '.page,.has_next'

# UI
poetry run ui-serve

# MCP
poetry run mcp-server   # stderr に [MCP] ... ready
printf '{"jsonrpc":"2.0","id":1,"method":"search_minutes","params":{"q":"給食","limit":3}}' \
| poetry run mcp-server 2>/dev/null | jq

# Nightly
gh workflow run Nightly --ref main && gh run watch
gh run download --name "catalog-dist-YYYY-MM-DD"
```

