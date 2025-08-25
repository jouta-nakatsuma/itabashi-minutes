# Itabashi Minutes — Dev Quickstart

## Setup
- Python 3.11 推奨。Poetry で依存導入: `poetry install --only main,dev`
- 実行前に robots.txt とアクセス制御を遵守してください（1 req/sec + ジッター、夜間実行推奨）。

## Configuration
- `.env`（任意）: `REQUEST_DELAY=1.0`, `MAX_PAGES=2`, `MAX_ITEMS=50`, `RETRIES=3`, `TIMEOUT_CONNECT=10`, `TIMEOUT_READ=30`, `BACKOFF_BASE=1.0`, `BACKOFF_MAX=30.0`, `USER_AGENT="ItabashiMinutesBot/0.1 (+contact)"`, `BASE_URL=https://www.city.itabashi.tokyo.jp`, `ALLOW_PATTERN=^https?://[^/]+/gikai/kaigiroku/.*`, `DENY_PATTERNS=\.zip$,\.csv$`
- URL制約: 許可リスト `^https?://[^/]+/gikai/kaigiroku/.*`、DENYは `.zip,.csv` など。

## Run
- 互換エントリ（現状すぐ実行可）: `poetry run python -m crawler.cli --max-pages 2 --max-items 3 --validate --ndjson`
- スクリプトエントリ（pyproject更新済み）: `poetry run itabashi-crawler`
- 出力: JSON `crawler/sample/sample_minutes.json`、NDJSON `crawler/sample/sample_minutes.ndjson`

## Validate
- スキーマ検証（--validate指定時）: `schemas/minutes.schema.json` に対して未知キーを除外して検証します（互換維持）。

## Test
- 単体テスト: `poetry run pytest -q`
- 429/503/Retry-After、ページング停止、重複除外、バックオフ上限などを responses でスタブ。

## Notes
- スキーマ互換性を破壊しないこと（meeting_id は出力に含むが検証時は除外投影）。
- robots.txt を起動時に取得し、許可判定の上でのみクロールします（読込失敗時は警告ログ、can_fetch 例外時は許可扱い）。
