# 板橋区議会会議録クローラー & 分析システム

板橋区議会の会議録を自動取得し、日本語テキスト処理・分析を行うデータパイプラインです。

## 🎯 プロジェクト概要

このプロジェクトは、板橋区議会の公開会議録を効率的に収集・正規化・分析するためのツールセットです。議会の透明性向上と市民の政治参加促進を目的としています。

## 📁 プロジェクト構成

```
itabashi-minutes/
├── crawler/           # Webクローラー（Python）
│   ├── itabashi_spider.py
│   ├── .env.example
│   └── sample/
├── ingest/           # テキスト正規化処理
│   └── text_normalizer.py
├── schemas/          # データスキーマ定義
│   └── minutes.schema.json
├── analysis/         # データ分析ノートブック
│   ├── topic_modeling.ipynb
│   ├── keyword_trends.ipynb
│   └── speaker_stats.ipynb
├── docs/             # ドキュメント
│   ├── README-ja.md
│   └── architecture.md
└── pyproject.toml    # Python依存関係管理
```

## 🚀 クイックスタート

### 1. 環境セットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd itabashi-minutes

# Python環境の準備（Python 3.8+ 必須）
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 依存関係のインストール
pip install -r requirements.txt
# または Poetry使用の場合
poetry install
```

### 2. 設定ファイルの準備

```bash
# 環境設定をコピー
cp crawler/.env.example crawler/.env

# 必要に応じて設定を編集
nano crawler/.env
```

### 3. クローラーの実行

```bash
# サンプル実行（最新年度の会議録を取得）
cd crawler
python itabashi_spider.py

# 出力確認
ls sample/
```

### 4. テキスト正規化

```bash
# 取得したデータの正規化処理
cd ingest
python text_normalizer.py
```

### 5. 分析の実行

```bash
# Jupyter Notebookの起動
jupyter notebook

# ブラウザで以下を開く
# - analysis/topic_modeling.ipynb
# - analysis/keyword_trends.ipynb
# - analysis/speaker_stats.ipynb
```

## 📋 対象サイトとクロール範囲

### 対象サイト
- **URL**: https://www.city.itabashi.tokyo.jp/gikai/kaigiroku/
- **対象**: 板橋区議会会議録（本会議・委員会）
- **形式**: HTML、PDF

### クロール対象範囲
- ✅ 最新年度の定例会・臨時会
- ✅ 常任委員会・特別委員会
- ✅ 議事録本文（発言者・発言内容）
- ❌ 傍聴記録、議事進行の細かい手続き

### 除外条件
- 個人情報が含まれる可能性のある非公開議事
- 著作権保護対象の資料
- 画像・動画ファイル

## 🤖 アクセス頻度とマナー

### robots.txt の遵守
```bash
# robots.txtの確認
curl https://www.city.itabashi.tokyo.jp/robots.txt
```

### アクセス制御
- **リクエスト間隔**: 1秒以上（デフォルト）
- **同時接続数**: 1接続のみ
- **User-Agent**: `ItabashiMinutesCrawler/1.0 (Research Purpose)`
- **タイムアウト**: 30秒

### サーバー負荷配慮
- 平日の日中（9:00-17:00）は避ける
- 大量データの取得は夜間・休日に実行
- エラー時は指数バックオフで再試行

## 📄 ライセンス・再利用について

### 取得データの利用条件
- **出典表示**: 「板橋区議会会議録より」を明記
- **商用利用**: 要確認（板橋区に問い合わせ推奨）
- **二次配布**: 加工後のデータは可（元データの直接配布は避ける）

### このソフトウェアのライセンス
- **ライセンス**: MIT License
- **再利用**: 自由（出典表示推奨）
- **改変**: 可

## 🔧 技術スタック

### クローラー
- **言語**: Python 3.8+
- **主要ライブラリ**: 
  - `requests` - HTTP通信
  - `BeautifulSoup4` - HTML解析
  - `lxml` - XML/HTML処理

### テキスト処理
- **形態素解析**: MeCab + mecab-python3
- **文字正規化**: unicodedata, 独自正規化ルール
- **エンコーディング**: UTF-8

### 分析
- **データ処理**: pandas, numpy
- **機械学習**: scikit-learn (LDA, TF-IDF)
- **可視化**: matplotlib, seaborn
- **ノートブック**: Jupyter

## 📊 データ形式

### 正規化済みレコード
詳細は `schemas/minutes.schema.json` を参照

```json
{
  \"meeting_date\": \"2024-03-15\",
  \"committee\": \"本会議\",
  \"title\": \"令和6年第1回定例会第3日\",
  \"page_url\": \"https://...\",
  \"agenda_items\": [
    {
      \"agenda_item\": \"令和6年度予算について\",
      \"speaker\": \"田中議員\",
      \"speech_text\": \"議長、質問いたします...\",
      \"page_no\": 5
    }
  ]
}
```

## 🛠️ トラブルシューティング

### よくある問題

**Q: MeCabのインストールでエラーが出る**
```bash
# Ubuntu/Debian
sudo apt-get install mecab mecab-ipadic-utf8 libmecab-dev

# macOS
brew install mecab mecab-ipadic
```

**Q: 文字化けが発生する**
- 環境変数 `LANG=ja_JP.UTF-8` を設定
- エディタのエンコーディングをUTF-8に変更

**Q: クローラーがタイムアウトする**
- `.env` ファイルの `REQUEST_TIMEOUT` を増やす
- ネットワーク接続を確認

### ログの確認
```bash
# クローラーのログ
tail -f crawler.log

# エラー詳細の確認
python -c \"import crawler.itabashi_spider; crawler.itabashi_spider.main()\"
```

## 🤝 貢献方法

1. Issues で問題報告・機能要望
2. Fork してプルリクエスト作成
3. テストの追加・実行
4. ドキュメントの改善

### 開発環境
```bash
# 開発用依存関係のインストール
pip install -e \".[dev]\"

# コード品質チェック
flake8 crawler/ ingest/
mypy crawler/ ingest/

# テスト実行
pytest tests/
```

## 📞 連絡先・サポート

- **Issues**: GitHub Issues で報告
- **ディスカッション**: GitHub Discussions
- **メール**: [設定してください]

## 📝 変更履歴

詳細は [CHANGELOG.md](CHANGELOG.md) を参照

- v1.0.0 (2024-XX-XX): 初回リリース
  - 基本的なクローラー機能
  - テキスト正規化処理
  - 基本的な分析ノートブック

---

**免責事項**: このツールは研究・教育目的で作成されています。商用利用や大量アクセスは事前に板橋区に確認してください。