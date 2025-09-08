# Sprint 3 Issues (Itabashi Minutes)

---

## Issue 1: API v0.2 拡張（検索機能の充実）
**内容**
- `/search` に `limit`/`offset`/`order_by`/`order` を追加
- レスポンスに `total`, `page`, `has_next`
- FTS5 `snippet()/highlight()` を用いた `<em>…</em>` 付きスニペット
- デフォルト並び替えは `date desc`

**完了条件**
- `/search` が拡張パラメータを受け付け、正しく結果を返す
- OpenAPI `/docs` に反映
- テストでパラメータ境界とハイライト整合を検証

**ラベル**
- `api`, `backend`, `sprint3`

---

## Issue 2: Streamlit UI v0.1 実装
**内容**
- 検索フォーム＋フィルタ（年度/委員会/話者）
- 一覧画面：スニペット強調表示、ページャ
- 詳細画面：メタ情報＋抽出テキスト＋PDFリンク
- `pyproject.toml` に `ui-serve = "app.streamlit_app:main"` 追加

**完了条件**
- ローカルで検索→一覧→詳細が動作
- スナップショットE2Eテスト通過

**ラベル**
- `ui`, `frontend`, `sprint3`

---

## Issue 3: MCPサーバ v0.1
**内容**
- ツール：`search_minutes(query, filters, limit)` / `get_document(meeting_id)`
- APIへのプロキシ実装
- `manifest.json` と README に ChatGPT/Claude 設定例を追加

**完了条件**
- MCPサーバを起動し、ChatGPT/Claude から検索が可能
- サンプルクエリで上位3件の結果が返る

**ラベル**
- `mcp`, `integration`, `sprint3`

---

## Issue 4: Nightly ジョブ（定期クロール＆成果物公開）
**内容**
- `.github/workflows/nightly.yml` を追加
- cronで毎晩実行、Artifacts に `catalog.duckdb` / `index.json` / `documents.ndjson`
- 週1で自動Release（タグ `catalog-YYYYMMDD`）
- 失敗時に自動でIssue化（ログ添付）

**完了条件**
- 2夜連続で成功（Artifacts作成・Release週1）
- 失敗時にIssueが自動作成される

**ラベル**
- `ci`, `automation`, `sprint3`

---

## Issue 5: 構造抽出の精度向上（誤検知抑制）
**内容**
- `resources/normalize.yml` に役職/委員会/氏名の正規化辞書を追加
- 正規表現ルールを強化（行頭アンカー、節番号パターン、否定先読み）
- ゴールデンセットで Precision/Recall を計測

**完了条件**
- Precision ≥ 0.9 / Recall ≥ 0.85 を満たす
- 回帰テストで劣化を検知できる

**ラベル**
- `extractor`, `quality`, `sprint3`

---

## Issue 6: Verification Cheatsheet (Sprint 3) & Makefile
**内容**
- README末尾に「Verification Cheatsheet (Sprint 3)」を追記
- Makefileに `catalog/api/ui/mcp/test` タスクを追加
- `poetry run` でも等価実行できるようにする

**完了条件**
- ローカルで `make catalog && make api && make ui && make mcp && make test` が成功
- READMEの手順通りに検証可能

**ラベル**
- `docs`, `devex`, `sprint3`
