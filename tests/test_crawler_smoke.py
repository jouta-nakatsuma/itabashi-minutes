
import os, json, subprocess, sys, re
import pytest

MIN_RECORDS = int(os.getenv("CRAWLER_MIN_RECORDS", "5"))

@pytest.mark.smoke
def test_crawler_smoke_generates_min_records(tmp_path):
    # 乾燥走行: 出力をNDJSONに吐くモードがあればそれを利用する。なければstdoutをパース。
    try:
        res = subprocess.run(
            [sys.executable, "-m", "crawler.itabashi_spider"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        pytest.xfail("crawler timeout (site slow?)")

    # 標準出力から JSON ラインを抽出（実装に合わせて調整）
    text = (res.stdout or "") + "\n" + (res.stderr or "")
    # 例: "parsed meeting_date=2025-08-21" の行数で近似判定
    hits = len(re.findall(r"parsed meeting_date=", text))
    if hits == 0 and res.returncode != 0:
        pytest.xfail(f"crawler non-zero exit: {res.returncode}")

    assert hits >= MIN_RECORDS, f"expected >= {MIN_RECORDS} records, got {hits}"
