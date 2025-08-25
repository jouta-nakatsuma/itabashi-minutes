# tests/test_crawler_minimum.py
import json
from pathlib import Path
from unittest import mock

import responses
from jsonschema import validate as _validate

from crawler.config import Config
from crawler.itabashi_spider import ItabashiMinutesCrawler

SCHEMA_PATH = Path("schemas/minutes.schema.json")

def _add_index_page(rsps, base):
    root = f"{base}/gikai/kaigiroku/"
    body1 = """
    <html><body>
      <a href="/gikai/kaigiroku/meetings/1">会議1</a>
      <a href="/gikai/kaigiroku/meetings/2">会議2</a>
      <a rel="next" href="/gikai/kaigiroku/?page=2">次へ</a>
    </body></html>
    """
    rsps.add(responses.GET, root, body=body1, status=200)

    body2 = """
    <html><body>
      <a href="/gikai/kaigiroku/meetings/3">会議3</a>
    </body></html>
    """
    rsps.add(responses.GET, f"{root}?page=2", body=body2, status=200)

def _add_detail_pages(rsps, base):
    for i in (1, 2, 3):
        rsps.add(
            responses.GET,
            f"{base}/gikai/kaigiroku/meetings/{i}",
            body=f"""
            <html><body>
              <article id="main">
                <h1>委員会{i}</h1>
                <p>本文{i}</p>
                <a href="/pdfs/minutes_{i}.pdf">PDF</a>
              </article>
            </body></html>
            """,
            status=200,
        )
        rsps.add(
            responses.GET,
            f"{base}/pdfs/minutes_{i}.pdf",
            body=b"%PDF-1.6 ...",
            status=200,
            content_type="application/pdf",
        )

@responses.activate
def test_crawl_minimum(tmp_path):
    base = "https://example.local"
    _add_index_page(responses, base)
    _add_detail_pages(responses, base)

    cfg = Config()
    cfg.base_url = f"{base}/gikai/kaigiroku/"
    cfg.max_pages = 2
    cfg.request_delay = 0.0
    cfg.retries = 0
    with mock.patch("random.uniform", return_value=0.0):
        c = ItabashiMinutesCrawler(cfg)
        recs = list(c.crawl(max_pages=2, max_items=None))  # ← 公開APIに合わせて調整

    # 件数
    assert len(recs) == 3

    # スキーマ検証（1件でOK）
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    def project(rec):
        keep = {"date", "committee", "page_url", "pdf_url", "content", "source"}
        return {k: rec[k] for k in keep if k in rec}
    _validate(instance=project(recs[0]), schema=schema)

def test_backoff_capped():
    cfg = Config()
    cfg.backoff_base = 1.0
    cfg.backoff_max = 0.5
    with mock.patch("random.uniform", return_value=0.0):
        c = ItabashiMinutesCrawler(cfg)
        assert c._compute_backoff(10) <= cfg.backoff_max
