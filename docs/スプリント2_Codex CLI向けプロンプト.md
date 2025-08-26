# Codex CLIプロンプト出力

Codex 指示 — Step 1: 構造抽出（議題・登壇者）
===============================

ゴール
---

*   Sprint1 で得た正規化済みテキスト/JSONを入力として、**議題（Agenda）** と **発言（Speaker/Speech）** を最小構造に抽出するモジュールを実装する。
*   代表サンプルで **議題数** と **先頭5件の話者名** が期待値と一致。将来の抽出改善でも**スナップショットで回帰検知**できること。

前提
--

*   リポジトリ: `itabashi-minutes`
*   Python: 3.10+（既存プロジェクト準拠）
*   追加依存は不要（標準ライブラリ + pydantic で実装）。
*   入力は `data/normalized/*.json` を想定（無ければ **fixtures を生成** してテストを回す）。

* * *

1) 追加・変更するファイル/構成
-----------------

```
ingest/
  __init__.py
  structure_extractor.py        # 実装本体（main()あり）
  patterns.py                   # 正規表現と定数
tests/
  fixtures/
    sample_minutes_01.json      # フィクスチャ（最小）
    sample_minutes_02.json      # 任意で追加
    sample_minutes_03.json      # 任意で追加
  test_structure_extractor.py   # 単体テスト
  test_structure_snapshot.py    # スナップショットテスト
```

> 既に `data/normalized/*.json` がある場合は **fixtures 生成をスキップ**して良いが、テストが自給自足で回るよう最低1本は `tests/fixtures/` に置く。

* * *

2) 仕様（抽出ルール）
------------

### 2.1 データモデル（pydantic v2）

```python
# ingest/structure_extractor.py
from typing import List, Optional
from pydantic import BaseModel, Field

class Speech(BaseModel):
    speaker: str = Field(..., description="話者名（例：○中妻委員、教育長 などから抽出）")
    role: Optional[str] = Field(None, description="役職（委員/議員/部長/課長/教育長/理事者 等）")
    paragraphs: List[str] = Field(default_factory=list, description="発言本文の段落配列")

class AgendaItem(BaseModel):
    title: str
    order_no: int
    speeches: List[Speech] = Field(default_factory=list)

class MinutesStructure(BaseModel):
    meeting_date: Optional[str] = None
    committee: Optional[str] = None
    page_url: Optional[str] = None
    pdf_url: Optional[str] = None
    agenda_items: List[AgendaItem] = Field(default_factory=list)
```

### 2.2 正規表現・判定（`ingest/patterns.py`）

*   **議題見出し検出**（先頭一致を重視、飾り記号への過検出を抑制）
    ```
    ^(?:第[一二三四五六七八九十百]+[ 　]*|[0-9０-９]{1,3}[.)）][ 　]*|〔[^〕]+〕|【[^】]+】|[◇◆■○●◎・])[^\n]+
    ```
*   **話者行検出**（代表例／順に評価、漢字かな・役職語＋コロン許容）
    ```
    ^(?:○?[ 　]*([^\s　:：]+?)(?:委員|議員|委員長|副委員長|部長|課長|教育長|理事者)?)[ 　]*[:：]
    ```
    *   例：「○中妻委員：」「教育長：」「○ 田中議員：」「理事者：」
*   **ページヘッダ/ノイズ除去**
    *   例：「— _ページ番号_ —」「（参照）」「（拍手）」等は本文から除外。
*   **段落整形**
    *   全角/半角スペースの正規化、連続空行は1つに圧縮、行末の全角約物や圏点の連続は適度に縮約。
    *   話者切替時に paragraphs を新規開始。話者行から次の話者行/議題見出しまでを1ブロックとする。

> これらの **正規表現・共通語彙** は `patterns.py` に定数としてまとめ、ユニットテストで守る。

* * *

3) 実装（`ingest/structure_extractor.py`）
--------------------------------------

*   入力：`Path` か `str` でファイルパスを受け取り、正規化済み JSON から `text` もしくは `pages`（ページ配列）を読み取る。無ければ `content` 等の代替キーを漁る。
*   **抽出アルゴリズムの流れ**
    1.  全文を行単位に分割（\\r\\n, \\n 等を吸収）
    2.  前処理：空白正規化、ページヘッダ/フッタ（数字だけのセンタリング行等）除去
    3.  先に**議題見出し**をスキャンし、`AgendaItem` の境界をつくる（ヒットなしなら `AgendaItem(title="（議題なし）", order_no=1)` を作って全体をそこへ）
    4.  各ブロック内で**話者行**を検出し、`Speech` を切る
    5.  段落蓄積：空行で段落を閉じる／次の話者行で Speech を閉じる
    6.  role は話者トークン末尾（委員/議員/部長…）から推定し、speaker は役職語を取り除いた人名コア（可能な範囲）
*   **決め打ち/安全策**
    *   過検出しやすい「○」「・」「◎」だけの行は無視
    *   ひらがな全角コロン「：」と半角「:」の両方を許容
    *   行頭の全角スペース/タブは strip
*   **main() の実装**
    *   CLI: `python -m ingest.structure_extractor --src tests/fixtures/sample_minutes_01.json --out /tmp/out.json`
    *   出力：`MinutesStructure` を JSON へ（ensure\_ascii=False, indent=2）

* * *

4) テスト
------

### 4.1 単体テスト（`tests/test_structure_extractor.py`）

*   代表フィクスチャ1本で以下を検証：
    *   `AgendaItem` が **N件以上**（例：`>= 2`）生成されている
    *   各 `AgendaItem.speeches` の総数が閾値以上（例：`>= 3`）
    *   先頭の `Speech.speaker` が期待列（例：`["中妻穣太", "教育長", "田中太郎"][:5]`）と一致（空白差は許容）

### 4.2 スナップショット（`tests/test_structure_snapshot.py`）

*   `MinutesStructure` を dict 化 → `json.dumps(..., sort_keys=True, ensure_ascii=False)`
    *   ファイル `tests/fixtures/snapshots/structure_sample01.json` と比較
    *   差分は空白・末尾改行のみ許容（比較関数で正規化）

### 4.3 フィクスチャ

*   `tests/fixtures/sample_minutes_01.json`
    *   最小構成の JSON（`{"meeting_date": "...", "committee": "...", "text": "...（ここに代表的な書式例を含む）..."}`）
    *   話者行の例は **3種以上**（委員/教育長/理事者 等）を含める

* * *

5) 受入基準（Step 1）
---------------

*   `poetry run pytest -q` がグリーン
*   代表フィクスチャで
    *   議題数が閾値以上（例：2+）
    *   **先頭5件の話者名** がスナップショット/期待値と一致（空白差のみ許容）
*   `python -m ingest.structure_extractor --src tests/fixtures/sample_minutes_01.json` が動作し、JSONを出力

* * *

6) 実行コマンド（ローカル検証用／Codexも参照）
---------------------------

```bash
# テスト実行
poetry run pytest -q tests/test_structure_extractor.py
poetry run pytest -q tests/test_structure_snapshot.py

# 手動抽出（確認用）
poetry run python -m ingest.structure_extractor \
  --src tests/fixtures/sample_minutes_01.json \
  --out .tmp/structure_out.json
```

* * *

7) 実装メモ（品質と保守）
--------------

*   正規表現は **過検出しない** ことを最優先。ユースケース追加で調整しやすいよう `patterns.py` に集約。
*   話者名の正規化は **役職語の剥離** と **丸印（○）除去** を最小限にとどめる。姓/名の切り分けは不要。
*   例外時は空配列や `"(unknown)"` を返さず、**議題1件＋speech 0件**など**構造を保つ**戻り値にする。
*   I/O は**UTF-8**固定。JSONは `ensure_ascii=False`。

* * *

8) 仕上げ
------

*   すべてのコードに最小 docstring を付与。
*   `ruff`/`black` で整形（プロジェクト設定に従う）。
*   変更一式をコミット：  
    `feat(ingest): add structure extractor with regex-based agenda/speaker parsing and snapshot tests`

* * *

**以上。** 実装が完了したらテスト結果と生成ファイル（抜粋）を共有してください。レビューに進みます。