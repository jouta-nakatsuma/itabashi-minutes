# ギャップ分析と実装プラン

**User:** Anonymous (sunpin32@yahoo.co.jp)  
**Created:** 8/20/2025 18:58  
**Updated:** 8/20/2025 19:04  
**Exported:** 8/25/2025 11:36  
**Link:** [https://chatgpt.com/g/g-p-68a2428917408191ab595311b37e4516/c/68a59c42-021c-8324-b65e-4ccc91322195](https://chatgpt.com/g/g-p-68a2428917408191ab595311b37e4516/c/68a59c42-021c-8324-b65e-4ccc91322195)  

## Prompt:
ChatGPT-Gitコマンド 使い方.md

ファイル

では、Itabashi Minutesを具体的に作っていく段階に入ろう。
まず、VIBE-KANBANによって作成されたGitHubリポジトリ
https://github.com/jouta-nakatsuma/itabashi-minutes
を評価してくれ。
CIを通すだけで必死になってて、結局これが今どこまでできてるのかわからん^^;

このリポジトリの現状と、先ほど見通しを立ててもらった「仕様書 v0.1」を比較してギャップ分析し、必要な実装作業のプランを立ててくれ。

## Response:
思考時間: 3m 54s

より良い回答のため思考中

Browsing GitHub repo and performing gap analysis

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes)

クリックしてリポジトリ内容を確認

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/tree/main/analysis)

事前にファイル開いてエラー回避方法を確認

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/blob/main/pyproject.toml)

トラブルシューティングとUI動的読み込み対策

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/tree/main/.github/workflows)

GitHubでファイル情報を取得する方法の検討

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/commits/main/)

探しているコミットのファイル変更内容

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498)

ファイル内容の調査と変更点確認

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498)

クリックしたコミットの詳細確認

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/858714d1904a9c0cb83a9897279e63106f507512)

クリックして"fix(normalizer)"コミットの詳細確認

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/97ae6aeaa191f8e1156f69da42cb12aabc820f3a)

引用元の取得と型に関する修正

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/249e176e6dd2f51e5e099d25d5d21edad7529ce1)

コミットの diff 行に基づいた議題抽出

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/249e176e6dd2f51e5e099d25d5d21edad7529ce1)

Browsing commit diffs and expanding specific file views

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498)

Gap分析と仕様書再構築

[

![](https://www.google.com/s2/favicons?domain=https://skills.github.com&sz=32)

skills.github.com

](https://skills.github.com/)

確認とギャップ分析：テストディレクトリ調査

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes)

調査中: テストディレクトリとCIジョブ状況

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/actions)

レビューしてパイプラインの障害内容確認

[

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

github.com

](https://github.com/jouta-nakatsuma/itabashi-minutes/pull/3)

PRにすべてのコミットを反映して、進捗が分かりやすくなっています。この状態をもとに、「仕様書 v0.1」を参照してギャップ分析を行います。必要な実装タスクを提案し、計画を立てます。タスク、担当者（Glyph vs Jouta）、努力、受入基準、スプリントでの順序を整理しましょう。また、「何が動いているか」「何が足りないか」についても簡潔にまとめます。

報告内容として、次の通りです：

*   pyproject と Poetry による再現可能な環境。Python >=3.9、依存パッケージ（requests、bs4、lxml、mecab-python3、jsonschema、python-dotenv）。オプションで 'app' extras（streamlit）を使ってノートブックテスト。Jupyter ノートブックもあります。
*   余談として、最初のコミットに分析用ノートブックを見かけましたが、誤って 'venv' がコミットされていました（.gitignore に追加するべきか？）。

進展している内容として、いくつかの改善点と現状を整理します。

*   'venv'が含まれている点は改善可能。
*   Crawler：「ItabashiMinutesCrawler」では、会議リンクの取得と議事録の抽出処理、PDF URLの検出やユーザーエージェント、レートリミティングを行っており、基本的な骨組みが整備されています。
*   Normalizer：「JapaneseTextNormalizer」には、引数の置換やテキスト正規化などの機能があり、これらの処理例があります。
*   スキーマ：minutes.schema.jsonが存在し、CIでデータ検証が行われており、内容の確認は行っていませんが、ワークフロー内で確認済み。
*   CI：CIのパイプラインには、静的解析ツール、型チェック、テスト実行、クローラーの動作確認、「jsonschema」検証、セキュリティスキャンなどが含まれており、いくつかの実行で失敗したものの、マージ後は成功しています。

以下の点が未実装です：

*   OCRによるPDFフォールバック、実際のPDF解析（pdfminerやpytesseractの参照なし）、Itabashiサイトに合わせた詳細なCSSセレクタ、DBインデックスへの格納、検索APIやMCPプラグイン、要約/比較ツールなどの機能。

また、テストが確認できない点もあります。コミットにはテストが見当たりませんでしたが、パイプラインの実行時に失敗があり、指摘された8月17日の失敗はテストやPoetryに関連する可能性があります。

完了

穣太さん、把握したよ。まず「いま何ができてるか」を端的に、その後にv0.1仕様とのギャップ→実装プランの順でまとめます。

いまのリポジトリの到達点（2025-08-20時点）
==========================

*   基盤
    *   Poetry/pyproject で依存を整理（Python >=3.9）。CI内でもPoetryとpipの使い分けまで調整済み。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/pull/3)
    *   CI は lint（flake8）/format（black）/型（mypy）/簡易クローラ乾燥走行/スキーマ検証まで段組み済み。過程で失敗を挟みつつも、設定改善のコミットが続いている。[GitHub+1](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498)
*   クローラ（`crawler/itabashi_spider.py`）
    *   ベースURL（区サイト）から会議録リンクを拾い、最新年度の数件（デモとして上位5件）を走査する骨格を実装。ユーザーエージェント付与、レート制御、例外時の戻り値ガードなど最低限の堅牢化は済み。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/249e176e6dd2f51e5e099d25d5d21edad7529ce1)
    *   抽出項目：日付（正規表現）、委員会種別の簡易判定、ページURL、PDF URLの検出、議題テキスト（プレースホルダ実装）。サンプル JSON を `crawler/sample/sample_minutes.json` に出力。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/249e176e6dd2f51e5e099d25d5d21edad7529ce1)
*   取込・正規化（`ingest/text_normalizer.py`）
    *   日本語テキスト用の正規化（引用符の統一、全角括弧の半角化、段落抽出など）を型安全に実装・改善。CIで単体実行されるフローも用意。[GitHub+1](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/97ae6aeaa191f8e1156f69da42cb12aabc820f3a)
*   スキーマ＆検証
    *   `schemas/minutes.schema.json` を用意。CIでサンプルJSONに対し jsonschema でバリデーションする手順を組み込み。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498)
*   解析ノートブック
    *   `analysis/` にトピックモデリングやキーワードトレンドなどのノートブックの雛形を配置（初期スキャフォールドに含まれる）。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498)

> ひとことで言うと：「クロール→（軽い）抽出→正規化→スキーマ検証→ノートで見る」という最短ループは“動く形”ができています。ただし抽出精度や網羅性、検索API/UIなどは未着手〜途中です。

* * *

v0.1 仕様とのギャップ分析
===============

| 項目 | v0.1の狙い | 現状 | ギャップ / やること |
| --- | --- | --- | --- |
| クロール網羅性 | 年度・会期・委員会別一覧を堅牢に巡回、ページング対応、リトライ・バックオフ、robots順守 | トップ配下からリンク抽出の雛形＋デモ件数のみ。基底の`_make_request`はあるがサイト構造に依存した選択ロジックは未実装 | 一覧ページ構造に合わせたセレクタ実装、ページング、年度横断、委員会別の深掘り。HTTP 429/5xxリトライとバックオフ追加。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/249e176e6dd2f51e5e099d25d5d21edad7529ce1) |
| PDFテキスト抽出 | PDFパーサ＋スキャンPDF用OCR（日本語）でページ単位抽出、版面ノイズ除去 | PDF URL検出のみ。テキスト抽出やOCRは未実装 | `pdfminer.six`/`pypdf`＋`tesseract-ocr-jpn` を導入しページテキスト生成・信頼度メタ付与 |
| 構造抽出（議題/発言） | 見出し・議題・登壇者・発言本文・ページ範囲などの構造化 | `content`系divからテキストを切り出す簡易版。スピーカー等はプレースホルダ | 見出し・書式・用語（「○○委員」「○○議員」「△△部長」等）に基づくルール抽出＋後段の正規化辞書 |
| スキーマ | 議会ID、会期、日付、種別、議題、発言、ページ配列、ソースURL、抽出器バージョン等 | `minutes.schema.json`あり。CIで検証まで実装 | フィールドの最終確定と必須/任意の整理、スキーマ版管理。CIで互換性チェックを追加。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498) |
| 正規化 | 日本語の表記ゆれ、引用符・括弧、段落、空白の正規化 | 引用符/括弧/段落等の正規化実装は進捗良好 | スピーカー名・役職の正規化辞書、地名/組織名の正規化（カナ/漢字）を追加 |
| 解析 | EDA、話者統計、トピック等のノート | 雛形ノートあり | 実データ適用と再現実行パス（Make/Invoke/Poetry scripts） |
| 検索API/MCP | `search_minutes` / `get_document` / `summarize_compare` などのMCP/簡易API | 未実装 | SQLite/DuckDB等で索引 → MCPサーバ or FastAPI を用意 |
| UI | 最小の閲覧UI（Streamlit想定） | 依存グループ`app`は整理済みだがUI本体は未配置 | 検索→一覧→詳細（PDFプレビュー＋抽出テキスト）の簡易UI |
| テスト | 単体/結合/回帰スナップショット、サンプルPDFでの黄金データ | CIにpytestジョブはあるがテスト群は未確認/不足 | まずはスキーマ適合＆抽出ルールのスナップショットテストから着手。CI安定化。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498) |
| 運用 | 定期ジョブ（夜間クロール）、成果物保存、ログ／メトリクス | CIは手動/PRトリガ中心。過去に失敗ログも確認 | `schedule` ワークフローでナイトリー、成果物のArtifacts/Release保管、失敗時通知。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/actions) |

* * *

実装プラン（優先度順・3スプリント想定）
====================

スプリント1（収集の堅牢化と最低限の品質）
---------------------

1.  一覧巡回の本実装
    *   年度・会期・委員会ページのDOM/URL規則に合わせたセレクタ、ページング実装、429/5xxの指数バックオフ。
    *   Done条件：直近2年度・全委員会で10件以上のレコードを安定取得。出力はNDJSON/JSON。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/249e176e6dd2f51e5e099d25d5d21edad7529ce1)
2.  PDF抽出（テキスト）
    *   `pdfminer.six`/`pypdf`でページごと文字抽出。ページ番号・座標は当面不要、テキストのみ。
    *   Done条件：サンプルPDF3本でページテキストを生成しスキーマに格納。
3.  スキーマ確定と検証強化
    *   必須/任意フィールドを確定しバージョン付与。`jsonschema` で互換性チェックをCIに追加。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498)
4.  最初のテスト
    *   「クローラがN件以上返す」「スキーマ適合」「正規化の単体（引用符/括弧）」の3系統。
    *   CIのpytestを安定させる（現状の過去失敗を踏まえ、依存解決とタイムアウトを見直し）。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/actions)

スプリント2（構造化と検索）
--------------

5.  構造抽出（議題・登壇者）
    *   ルールベース（正規表現＋見出しパターン）で「議題」「登壇者（役職/氏名）」をタグ付け。
    *   スナップショットテストで破壊的変更を検知。
6.  カタログ/インデックス
    *   SQLite/DuckDBに読み込み、主キー（`meeting_id`）と副インデックス（年度/委員会/議題キーワード/話者）を作成。
7.  簡易API or MCP
    *   FastAPI で `/search` `/document/{id}` を用意、もしくはMCPサーバで `search_minutes`/`get_document` を実装（将来のClaude/ChatGPTツール連携を見据え）。

スプリント3（可視化と運用）
--------------

8.  最小UI（Streamlit）
    *   検索→一覧→詳細（PDFプレビュー＋抽出テキスト）。`pyproject` の `app` グループ活用。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/pull/3)
9.  定期クロール＆成果物保管
    *   GitHub Actionsの`schedule:`でナイトリー、成果物をArtifacts/Releaseへ。失敗時は通知。[GitHub+1](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498)
10.  解析ノートの実データ化
    *   ノートをパイプラインに接続し、再現実行（`poetry run`/Makefile）で更新できるように。

* * *

すぐにやると良い“小タスク”（1〜2時間で効く）
========================

*   **サイト固有セレクタの当て込み**（`itabashi_spider.py`）  
    今は「contentクラスのdivを上から3つ」などのプレースホルダ。会議録一覧と詳細ページの実DOMに合わせたセレクタへ差し替えを。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/249e176e6dd2f51e5e099d25d5d21edad7529ce1)
*   **PDF抽出ユーティリティの雛形作成**（`ingest/pdf_extractor.py`）  
    まずは1本のPDFをページテキストへ。将来OCRを差し込める関数型の設計に。
*   **最初のpytest**（`tests/`）  
    サンプルJSONのスキーマ適合、正規化の単体、クローラの返却件数（モックHTMLでも可）を用意。CIの安定度が上がります。[GitHub](https://github.com/jouta-nakatsuma/itabashi-minutes/commit/52439e12be4d8cd953a688aeece71bafa02a4498)
*   **.gitignoreの整理 & venv除外**  
    ルートに`venv/`が見えるので、誤コミット防止のため`.gitignore`を強化。

* * *

実行コマンド（ローカル動作の最短ルート）
====================

```bash
# セットアップ
poetry install

# デモクロール（サンプルJSON生成）
python crawler/itabashi_spider.py

# 正規化（サンプルに対して）
python ingest/text_normalizer.py
```

これで「動いている最小ループ」を再確認できます。その上で、上のスプリント1に着手すれば、\*\*“板橋区の会議録を安定収集→PDF含めたテキスト抽出→構造化→検索可能”\*\*のラインまで一気に詰められます。ここまで進めば、一般質問準備にも直結するダッシュボード（検索・横断要約）を短期間で出せます。

必要なら、上記タスクを私の方でIssueテンプレ＋ラベル（`crawler`, `ingest`, `schema`, `ci`, `ui`, `mcp/api`）に起票する形で整理して出します。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)