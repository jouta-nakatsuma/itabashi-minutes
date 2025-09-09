# CODEX Notes — Sprint 3 (Working Handbook)

目的
- 次スプリント開始時に迷わないよう、最小で十分な運用・実装の要点を1ファイルに集約。
- 実運用のガードレール、CI要件、主要コマンド、作業手順、バックログの優先事項を明文化。

## 現況サマリ（Sprint 3）
- コア動線: 構造抽出 → カタログ → API（/search, /document） → UI（Streamlit） → MCP（stdio） → Nightly
- 追加ユーティリティ/ワークフロー:
  - `scripts/one_shot_apply.py`（Unified diffの安全適用）
  - `scripts/rebuild_catalog.py`（SQLiteカタログ再構築）
  - `scripts/nightly.sh`（夜間オーケストレーター）
  - `.github/workflows/ci.yaml`（unit + mcp-smoke 二系統）
  - `.github/workflows/mcp-weekly.yml`（週次 with mcp マトリクス）
  - `.github/workflows/nightly.yml`（毎晩アーティファクト/週次Release/失敗時Issue）

リリース: `v0.3.0-sprint3`（想定）

## ステータス（2025-09-09 14:33 JST）
- #34 完了: Verification Cheatsheet (Sprint 3) と README/スクリプトを追加（PR #42）。
- #22〜#25: Sprint 3 実装に包含（#33/#29/#31/#32 にて実現）。duplicate コメント付きでClose。
- #41: Nightly failed 2025-09-08（Artifactsに `nightly-logs-YYYY-MM-DD`）。本日時点は監視継続、恒常化時のみ調整。

### Nightly トリアージ手順（Playbook）
- 状況確認:
  - `gh run list --workflow Nightly --limit 5`
  - `gh run download --name "nightly-logs-YYYY-MM-DD"`
  - `sed -n '1,200p' nightly.out` / `sed -n '1,200p' logs/nightly.log`
- 典型原因と対処:
  - 429/5xx/タイムアウト: バックオフ/リトライ上限の緩和、夜間実行（既定）。単発なら再実行で様子見。
  - HTML構造変化: crawler のセレクタ更新。responsesベースのテスト追加を検討。
  - I/Oエラー（Artifactsなし）: 権限/パスを確認。`if-no-files-found: error` で検知済み。
- 再実行/手動検証:
  - `gh workflow run Nightly --ref main && gh run watch`
  - ローカル: `bash scripts/nightly.sh`（API不要、Poetry main のみ）

## 実行環境・依存
- Python: 3.11 推奨（CIは3.9/3.10/3.11）
- Poetry: ローカルは `poetry install --only main,dev` でOK（UI/ノート類は不要）
- OS: 開発者ローカル（macOS想定）/CI（Ubuntu）
- ネットワーク: on-request/明示承認（GitHub操作・外部通信）

## ガードレール（再掲）
- Approval Mode: on-request（差分プレビュー→「approve apply」で適用）
- 破壊的変更禁止（スキーマ互換性重視）
- 小さなPR/小粒コミット（Conventional Commits）
- ブランチ命名: `feat/<issue-number>-<slug>`（または fix/chore/docs/test）
- PRタイトル: `type(scope): subject (#<issue>)`
- DoD（共通）: CI green（lint/format/mypy/pytest）/ スキーマ互換性OK / README/usage更新 / Issueコメントに確認手順

## CI（二系統 + 週次）
- unit: Python 3.10 / Poetry 1.8.3 固定
  - install: `poetry install --only main,dev`（必要に応じ `poetry lock --no-update`）
  - jobs: flake8/mypy/black/pytest（対象は段階拡張）
- mcp-smoke: with mcp（`poetry lock` → `--with mcp`）/ continue-on-error（段階導入）
- MCP Weekly: 3.9/3.10/3.11 マトリクスで with mcp の簡易検証
- Nightly: crawl/build → artifacts（14d）→ Fri JST Release → failure→Issue

## スクリプト・エントリ
- Catalog: `poetry run catalog-load --db var/minutes.db --src tests/fixtures`
- API: `poetry run api-serve --db var/minutes.db --host 127.0.0.1 --port 8000`
- UI: `poetry run ui-serve`（Streamlit。`.env: IM_API_BASE` 任意）
- MCP: `poetry run mcp-server`（SDKあればMCP/無ければJSON-RPCにフォールバック）
- Diff適用:
  - Dry-run: `git diff | poetry run python scripts/one_shot_apply.py --dry-run --strip 1`
  - Apply: `git diff | poetry run python scripts/one_shot_apply.py --strip 1 --backup`
- Rebuild（optional）:
  `poetry run python scripts/rebuild_catalog.py --db var/minutes.db --src tests/fixtures --fresh --analyze --vacuum --verbose`
 - Nightly（手動ローカル）: `bash scripts/nightly.sh`

## 検証（ローカル）
- README: Quick Start と Verification Cheatsheet のコマンドは「コピペ可」
- Smoke:
  - `/health`
  - `/search?q=高島平`
  - `/search?committee=文教児童委員会&date_from=2025-08-01&date_to=2025-08-31`
  - `/document/1`

## Sprint 3 成果（要点）
- #29 API v0.2: `/search` に limit/offset/order_by/order、`page/has_next`、FTS `snippet()` ハイライト、relevance=ヒット数降順
- #30 UI v0.1: Streamlit 検索/一覧/詳細、日付フィルタはチェックON時のみ
- #31 MCP v0.1: stdio MCP（SDK）＋ JSON-RPC フォールバック、ツール `search_minutes/get_document`
- CI follow-up: unit + mcp-smoke、週次MCPマトリクス、Poetry/Python固定・lock運用
- #32 Nightly: 毎晩crawl/build→Artifacts、金曜JSTにRelease、失敗時Issue
- #33 抽出精度: 正規化辞書（resources/normalize.yml）と正規化ユーティリティ、見出し/話者REの強化（丸印誤検知抑制、氏名↔役職/役職のみケース対応、︓対応）

## 作業の型（小粒で安全に）
1) ブランチ作成  
`git checkout -b feat/<issue-number>-<slug>`
2) 差分は最小・段階適用（README/Docsも同PRで）
3) テスト追加 or 既存テスト拡張（対象小さく→広く）
4) CI確認（lint/format/mypy/pytest）
5) PR作成（Conventional Commits / タイトル規約 / 受入コマンドを本文に）
6) マージ後、ローカルブランチ削除・報告（Codex-result*）

## スキーマポリシー（要点）
- 破壊的変更NG（required追加/enum縮小/type縮小/min/max強化 等）
- 非破壊（任意追加・緩和）はOK
- 変更時は `tools/check_schema_compat.py` がCIで検出

## APIメモ（v0.2）
- `/search`:
  - クエリ: `q, committee, date_from, date_to, limit(<=100), offset, order_by(date|committee|relevance), order(asc|desc)`
  - レスポンス: `items, total, limit, offset, page, has_next`、qありで`snippet()`に`<em>`
- `/document/{id}`:
  - 議題・スピーチをネスト返却（パラグラフ配列）

## 実装の注意（よくある詰まり）
- one_shot_apply: 単一連続コンテキストのみ対応（保守的）。EOL/BOM保持。idempotent guardあり。
- READMEのコードブロック: URL/パスの折り返し禁止（1行化）
- Blackの全体適用は別PRで（CI落ち回避のため段階拡張）
- ネットワーク操作（タグ/リリース/Issue作成等）は承認の上で実施
 - `pyproject.toml` を変更したら、PR内で `poetry lock`（with mcp系は別ジョブ）を考慮。unitでは `--no-update` 運用可。
 - 抽出RE: 見出しは行頭アンカー、丸印見出しは見出し扱いしない。スピーカーは A(役職+氏名) / B(氏名) / C(役職) / D(氏名+役職) の順で判定。コロンは `:：︓` を許容。
 - 正規化: `ingest/normalize.py` + `resources/normalize.yml`。役職/委員会/氏名の表記ゆれ追加は辞書で。

## リリース手順（簡略）
- タグ作成: `git tag -a vX.Y.Z-sprintN -m "message"` → `git push origin <tag>`
- リリース作成（gh CLI）: `gh release create <tag> --title ... --notes ...`
- ノート（短文）: 主変更/Docs/CI/互換性の有無

## 参考ファイル
- README.md（Quick Start / Cheatsheet / Lint&Type）
- docs/Codex-result_*.md（各Stepの報告）
- scripts/one_shot_apply.py / scripts/rebuild_catalog.py
- .github/workflows/*.yml（CI）
- catalog/load.py / api/main.py（本流）
- scripts/nightly.sh / ingest/normalize.py / resources/normalize.yml
- .github/workflows/nightly.yml / mcp-weekly.yml

以上。差分プレビュー→承認→小粒実装→PR→CI→マージ→Nightlyでの観測までを一気通貫で回す。次の改善（P/Rテストの導入や辞書拡充）は小粒PRで継続。
