# CODEX Notes — Sprint 3 Kickoff (Working Handbook)

目的
- 次スプリント開始時に迷わないよう、最小で十分な運用・実装の要点を1ファイルに集約。
- 実運用のガードレール、CI要件、主要コマンド、作業手順、バックログの優先事項を明文化。

## プロジェクト現況（Sprint 2 完了時点）
- 最短動線: 構造抽出 → カタログ → API（/search, /document）
- 追加ユーティリティ:
  - `scripts/one_shot_apply.py`（Unified diffの安全適用）
  - `scripts/rebuild_catalog.py`（SQLiteカタログ再構築）
- ドキュメント:
  - READMEに Quick Start（fixtures前提）と Verification Cheatsheet を追加
  - Codex-result 報告（Step5/6/7）一式あり
- リリース: `v0.2.0-sprint2`

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

## CI（最低限）
- lint-and-type: flake8/mypy/black（対象拡張は段階的）
- test: pytest（3.9/3.10/3.11）
- crawler-dry-run（PR時のみ）
- schema-compat（破壊的変更検出）
- Blackチェック: `ingest catalog api scripts tests` に限定（現状）

## スクリプト・エントリ
- Catalog: `poetry run catalog-load --db var/minutes.db --src tests/fixtures`
- API: `poetry run api-serve --db var/minutes.db --host 127.0.0.1 --port 8000`
- Diff適用:
  - Dry-run: `git diff | poetry run python scripts/one_shot_apply.py --dry-run --strip 1`
  - Apply: `git diff | poetry run python scripts/one_shot_apply.py --strip 1 --backup`
- Rebuild（optional）:
  `poetry run python scripts/rebuild_catalog.py --db var/minutes.db --src tests/fixtures --fresh --analyze --vacuum --verbose`

## 検証（ローカル）
- README: Quick Start と Verification Cheatsheet のコマンドは「コピペ可」
- Smoke:
  - `/health`
  - `/search?q=高島平`
  - `/search?committee=文教児童委員会&date_from=2025-08-01&date_to=2025-08-31`
  - `/document/1`

## バックログ（Sprint 3 優先）
- #22 構造抽出の精度向上（誤検知抑制／正規化辞書）
  - 誤検知パターン除外/辞書拡充/スナップショットテスト強化
- #23 API ページネーション＆並び替え、ハイライト返却
  - sort/limit/offset/FTSハイライト
- #24 MCP 横展開（ChatGPT/Claude ツール連携）
  - MCPサーバ/ツール導線、最小サンプル/README
- #25 Nightly カタログ再構築のジョブ化
  - 定期実行、Artifacts/Release添付、失敗通知

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

## APIメモ（現行）
- `/search`:
  - クエリ: `q`（FTS）、`committee`、`date_from`、`date_to`、`limit`、`offset`
  - 現状のsort/ハイライトは次スプリント対応（#23）
- `/document/{id}`:
  - 議題・スピーチをネスト返却（パラグラフ配列）

## 実装の注意（よくある詰まり）
- one_shot_apply: 単一連続コンテキストのみ対応（保守的）。EOL/BOM保持。idempotent guardあり。
- READMEのコードブロック: URL/パスの折り返し禁止（1行化）
- Blackの全体適用は別PRで（CI落ち回避のため段階拡張）
- ネットワーク操作（タグ/リリース/Issue作成等）は承認の上で実施

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

以上。Sprint 3では、まず #22 or #23 から着手（優先度と影響範囲で選択）。差分プレビュー→承認→小粒実装→PR→CI→マージの型を維持する。
