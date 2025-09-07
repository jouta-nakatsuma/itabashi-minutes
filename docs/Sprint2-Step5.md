# Step 5: スクリプト化（ワンショット差分・運用補助）

## 目的
- Unified diff を安全に当てるユーティリティと、
- SQLite カタログを再構築する運用スクリプトを追加する。
- 依存追加・pyproject変更は不要（直接 `poetry run python ...` で実行）。

## 追加ファイル
scripts/
  one_shot_apply.py
  rebuild_catalog.py

## one_shot_apply.py（要件）
- 使い方:
  - stdin から Unified diff を受け取り、対象ファイルに適用
  - または `--diff path/to/patch.diff` を指定
  - `--dry-run` で適用可否のみ検査
  - `--backup` 指定で `.bak` を生成
- 安全策:
  - 適用前に対象ファイルの存在・先頭数行の一致を確認
  - 失敗したhunkは報告してロールバック（ファイルは変更前に戻す）
- 終了コード:
  - 全hunk適用成功で0、それ以外は非0

## rebuild_catalog.py（要件）
- 引数:
  - `--db var/minutes.db`（既定）
  - `--src data/normalized/`（既定。無ければ `tests/fixtures/` を使って良い）
  - `--fresh`（DBを削除して作り直し）
  - `--analyze` / `--vacuum`
- 手順:
  1) `--fresh` ならDBを削除
  2) `catalog/schema.sql` を `executescript`
  3) `catalog.load.load_directory(db_path, src_dir)` を実行
  4) 件数出力（minutes / agenda_items / speeches / speeches_fts）
  5) `--analyze` / `--vacuum` を指定時に実行
- 終了コード: `inserted > 0` なら0、そうでなければ1

## 受入基準
- `poetry run python scripts/one_shot_apply.py --dry-run < some.patch` が正常終了
- `poetry run python scripts/rebuild_catalog.py --db var/minutes.db --src tests/fixtures --fresh` が0で終了し、件数が表示される
