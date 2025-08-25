import os
from unittest import mock

import responses

from crawler.config import Config
from crawler.itabashi_spider import ItabashiMinutesCrawler


@responses.activate
def test_crawl_minimum():
    base = "https://example.local"

    # root page with two meeting links and a next page
    root = f"{base}/gikai/kaigiroku/"
    body1 = """
    <main>
      <a href="/gikai/kaigiroku/r06/m1.html">令和6年3月15日 本会議</a>
      <a href="/gikai/kaigiroku/r06/m2.html">令和6年3月16日 常任委員会</a>
      <a rel=\"next\" href="/gikai/kaigiroku/r06/list2.html">次へ</a>
    </main>
    """
    responses.add(responses.GET, root, body=body1, status=200)

    # page2 loops back to root (cycle)
    list2 = '<main><a href="/gikai/kaigiroku/">戻る</a></main>'
    responses.add(
        responses.GET, f"{base}/gikai/kaigiroku/r06/list2.html", body=list2, status=200
    )

    # meeting 1: first 429 with Retry-After, then 200
    m1 = f"{base}/gikai/kaigiroku/r06/m1.html"
    responses.add(responses.GET, m1, status=429, headers={"Retry-After": "0.01"})
    meeting_body = """
    <article>
      <a href="/documents/sample.pdf">PDF</a>
      <div class="content">2024年3月15日 本会議 議事...（本文ダミーが続く）</div>
    </article>
    """
    responses.add(responses.GET, m1, body=meeting_body, status=200)

    # meeting 2: first 503 then 200
    m2 = f"{base}/gikai/kaigiroku/r06/m2.html"
    responses.add(responses.GET, m2, status=503)
    responses.add(responses.GET, m2, body=meeting_body, status=200)

    # pdf
    responses.add(responses.GET, f"{base}/documents/sample.pdf", body=b"%PDF-1.7", status=200)

    # Avoid real robots.txt fetch; always allow
    with mock.patch.object(
        ItabashiMinutesCrawler,
        "_load_robots",
        return_value=mock.Mock(can_fetch=lambda ua, u: True),
    ):
        cfg = Config()
        cfg.base_url = base
        cfg.max_pages = 3
        cfg.max_items = 2
        cfg.retries = 2
        cfg.backoff_base = 0.01
        cfg.backoff_max = 0.05
        cfg.request_delay = 0.0

        crawler = ItabashiMinutesCrawler(cfg)

        # speed up sleep
        with mock.patch.object(crawler, "_sleep_polite", lambda: None), mock.patch(
            "time.sleep", lambda s: None
        ):
            recs = crawler.get_latest_fiscal_year_minutes()

    assert len(recs) == 2
    assert all("meeting_id" in r for r in recs)
    assert all(
        r.get("pdf_url", "").endswith(".pdf") for r in recs if r.get("pdf_url")
    )

    # schema minimal validation (project unknown fields out)
    import json as _json
    from jsonschema import validate as _validate

    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "schemas", "minutes.schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = _json.load(f)

    def project(rec):
        allow = {
            "meeting_date",
            "committee",
            "title",
            "page_url",
            "pdf_url",
            "agenda_items",
            "crawled_at",
        }
        return {k: rec[k] for k in allow if k in rec}

    _validate(instance=project(recs[0]), schema=schema)


def test_backoff_capped():
    cfg = Config()
    cfg.backoff_base = 1.0
    cfg.backoff_max = 0.5
    with mock.patch("random.uniform", return_value=0.0):
        c = ItabashiMinutesCrawler(cfg)
        assert c._compute_backoff(10) <= cfg.backoff_max

