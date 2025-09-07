# Itabashi Minutes — Dev Quickstart

## Setup
- Python 3.11 推奨。Poetry で依存導入: `poetry install --only main,dev`
- 実行前に robots.txt とアクセス制御を遵守してください（1 req/sec + ジッター、夜間実行推奨）。

## Configuration
- `.env`（任意）: `REQUEST_DELAY=1.0`, `MAX_PAGES=2`, `MAX_ITEMS=50`, `RETRIES=3`, `TIMEOUT_CONNECT=10`, `TIMEOUT_READ=30`, `BACKOFF_BASE=1.0`, `BACKOFF_MAX=30.0`, `USER_AGENT="ItabashiMinutesBot/0.1 (+contact)"`, `BASE_URL=https://www.city.itabashi.tokyo.jp`, `ALLOW_PATTERN=^https?://[^/]+/gikai/kaigiroku/.*`, `DENY_PATTERNS=\.zip$,\.csv$`
- URL制約: 許可リスト `^https?://[^/]+/gikai/kaigiroku/.*`、DENYは `.zip,.csv` など。

## Run
- クローラー（サンプル取得）: `poetry run python crawler/itabashi_spider.py`
  - 出力: JSON `crawler/sample/sample_minutes.json`
  - 環境変数（.env）でページ数や遅延などを制御できます（`MAX_PAGES`, `MAX_ITEMS`, `REQUEST_DELAY` など）。

## Apply Unified Diff (one-shot)
- ドライラン: `git diff | poetry run python scripts/one_shot_apply.py --dry-run --strip 1`
- 実適用（バックアップ作成）: `git diff | poetry run python scripts/one_shot_apply.py --strip 1 --backup`
- オプション:
  - `--strip`: `a/`, `b/` などのパス接頭辞を剥がす深さ（既定: 1）
  - `--fuzz`: 文脈マッチに許容するズレ行数（既定: 0）
  - `--backup`: 上書き前に `.bak` を作成
  - 本ユーティリティは EOL/BOM を保持し、パス安全性（リポジトリ外書き込み防止）に対応しています。

## Rebuild Catalog (SQLite)
- スキーマ適用＋JSON取り込み:  
  `poetry run python scripts/rebuild_catalog.py --db var/minutes.db --src data/normalized/ --fresh --verbose`
- `--src` に JSON が無い場合は `tests/fixtures` をフォールバックとして使用します。

## Test
- 単体テスト: `poetry run pytest -q`
- 429/503/Retry-After、ページング停止、重複除外、バックオフ上限などを responses でスタブ。

## Notes
- スキーマ互換性を破壊しないこと（meeting_id は出力に含むが検証時は除外投影）。
- robots.txt を起動時に取得し、許可判定の上でのみクロールします（読込失敗時は警告ログ、can_fetch 例外時は許可扱い）。

## Schema Compatibility
- ポリシー（破壊的変更の例）:
  - required の追加、properties の削除、type の縮小（旧 ⊄ 新）、enum の縮小
  - 数値/文字列制約の強化（minimum↑, maximum↓, minLength↑, maxLength↓）
  - additionalProperties を true→false、配列 items.required の追加（要素必須の強化）
- 非破壊の例:
  - 任意プロパティの追加、required の削除、enum の拡張、制約の緩和
- バージョニング:
  - `x-schema-version` をスキーマに付与（例: 1.0.0）
  - patch: 任意項目追加・緩和、minor: サブスキーマ拡張、major: 破壊的変更（原則禁止）
- CI チェック:
  - PR 上で `tools/check_schema_compat.py` により `schemas/minutes.schema.json` の互換性を検査します。
  - 破壊的変更が検出されるとワークフローが失敗します。
