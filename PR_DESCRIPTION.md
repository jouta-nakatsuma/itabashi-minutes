# Pull Request: feat(init): scaffold crawler & data pipeline (Itabashi Minutes)

## 概要 (Summary)

板橋区議会会議録を自動取得・分析するデータパイプラインの基盤を構築しました。

This PR creates the foundational scaffold for the Itabashi Ward Council Minutes crawler and analysis pipeline.

## 対象サイトURLの例 (Target Site Examples)

- **メインサイト**: https://www.city.itabashi.tokyo.jp/gikai/kaigiroku/
- **会議録一覧**: https://www.city.itabashi.tokyo.jp/gikai/kaigiroku/r06/
- **PDF資料**: https://www.city.itabashi.tokyo.jp/documents/

## クロールの対象範囲と除外条件 (Crawl Scope & Exclusions)

### ✅ 対象範囲 (Target Scope)
- 最新年度の本会議・委員会議事録
- HTML形式およびPDF形式の会議録
- 議事録本文（発言者・発言内容・議題）
- 公開されている定例会・臨時会記録

### ❌ 除外条件 (Exclusions)
- 個人情報を含む可能性のある非公開議事
- 著作権保護対象の資料・画像
- 傍聴記録、議事進行の詳細手続き
- 過去5年以前の古いアーカイブ（初期段階）

## robots.txt の遵守とアクセス頻度の配慮 (robots.txt Compliance & Access Rate)

### 🤖 robots.txt 遵守
```bash
# robots.txtの確認コマンド
curl https://www.city.itabashi.tokyo.jp/robots.txt
```

### ⏱️ アクセス制御
- **リクエスト間隔**: 1秒以上（`REQUEST_DELAY=1.0`）
- **同時接続数**: 1接続のみ
- **User-Agent**: `ItabashiMinutesCrawler/1.0 (Research Purpose)`
- **タイムアウト**: 30秒
- **エラー時**: 指数バックオフで再試行

### 📅 サーバー負荷配慮
- 平日日中（9:00-17:00）のアクセス回避を推奨
- 大量データ取得は夜間・休日に実行
- CI/CDでの dry-run は最小限（最大2ページ）に制限

## ライセンス/再利用可否のメモ欄 (License & Reuse Notes)

### 📄 取得データの利用条件
- **出典表示**: 「板橋区議会会議録より」の明記が必要
- **商用利用**: 要確認（板橋区への問い合わせを推奨）
- **二次配布**: 加工後データは可、元データ直接配布は避ける
- **研究利用**: 学術研究・教育目的での利用は想定範囲内

### 💻 このソフトウェアのライセンス
- **ライセンス**: MIT License
- **再利用**: 自由（出典表示推奨）
- **改変**: 可
- **配布**: 可

### ⚖️ 法的考慮事項
- 取得データは公開情報のみ
- 政治的中立性の維持
- プライバシー保護の徹底
- 著作権法の遵守

---

## 実装内容 (Implementation Details)

### 📁 プロジェクト構成
```
itabashi-minutes/
├── crawler/           # Webクローラー (Python + requests + BeautifulSoup)
├── ingest/           # 日本語テキスト正規化処理
├── schemas/          # JSONスキーマ定義
├── analysis/         # 分析ノートブック (LDA, キーワード、発言者統計)
├── docs/             # ドキュメント (日本語README + アーキテクチャ)
├── .github/workflows/ # CI/CD パイプライン
└── pyproject.toml    # Poetry設定
```

### 🛠️ 技術スタック
- **Python 3.8+** (requests, BeautifulSoup4, pandas, scikit-learn)
- **日本語処理**: MeCab形態素解析、Unicode正規化
- **データ分析**: Jupyter Notebooks, matplotlib, seaborn
- **CI/CD**: GitHub Actions (lint + mypy + crawler dry-run)

### 📊 サンプルデータ
`/crawler/sample/sample_minutes.json` に3件のサンプルレコードを配置:
- 本会議（教育予算質疑）
- 常任委員会（防災対策）  
- 特別委員会（環境政策）

## テスト結果 (Test Results)

### ✅ CI/CD パイプライン
- **Lint**: flake8でコード品質チェック
- **Type Check**: mypyで型安全性検証
- **Crawler Dry-run**: 実際のサイトへの制限付きアクセステスト
- **Security**: banditでセキュリティスキャン
- **Notebook**: Jupyter notebookの構文チェック

### 🧪 動作確認
```bash
# クローラーテスト
cd crawler && python itabashi_spider.py

# テキスト正規化テスト  
cd ingest && python text_normalizer.py

# 分析ノートブック確認
jupyter notebook analysis/
```

## 今後の拡張予定 (Future Enhancements)

### Phase 1: 基本機能強化
- [ ] より多くの会議録データの取得
- [ ] PDF解析機能の向上
- [ ] エラーハンドリングの強化

### Phase 2: 分析機能拡張
- [ ] 感情分析の追加
- [ ] ネットワーク分析（議員間関係）
- [ ] 時系列トレンド分析の詳細化

### Phase 3: ユーザビリティ向上
- [ ] Web UI/ダッシュボード
- [ ] API提供
- [ ] 定期実行・自動更新

## 動作確認方法 (How to Test)

```bash
# 1. 環境セットアップ
git clone <repository>
cd itabashi-minutes
python -m venv venv
source venv/bin/activate
pip install poetry
poetry install

# 2. 設定
cp crawler/.env.example crawler/.env

# 3. サンプル実行
cd crawler
python itabashi_spider.py

# 4. 分析ノートブック
jupyter notebook analysis/
```

## レビューポイント (Review Points)

- [ ] コード品質・設計パターンの適切性
- [ ] 日本語テキスト処理の妥当性
- [ ] アクセス頻度・マナーの適切性
- [ ] ドキュメントの充実度
- [ ] CI/CDパイプラインの設定
- [ ] ライセンス・法的配慮の妥当性

---

**Note**: このPRは基盤となるスキャフォールドの提供を目的としており、実際のデータ取得・分析は今後の継続開発で実装予定です。