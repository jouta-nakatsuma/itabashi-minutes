import json
from typing import Iterator, List

import pytest

from ingest import pdf_extractor as pe
from ingest.cli import main as cli_main


def test_extract_with_pypdf_monkeypatch(monkeypatch, tmp_path):
    class FakePage:
        def __init__(self, t: str):
            self._t = t

        def extract_text(self):
            return self._t

    class FakeReader:
        def __init__(self, path):
            self.pages = [FakePage("A"), FakePage("B"), FakePage("C")]

    monkeypatch.setattr("ingest.cli.extract_text_per_page", lambda p, **k: ["P1", "P2"], raising=False)
# no-op, clarity
    monkeypatch.setattr(pe, "PYPDF_READER", FakeReader, raising=False)

    # Call through provider path
    texts = pe.extract_text_per_page("dummy.pdf", provider="pypdf")
    assert texts == ["A", "B", "C"]


def test_fallback_to_pdfminer(monkeypatch):
    # Force pypdf path to raise
    def raise_reader(path):
        raise RuntimeError("boom")

    monkeypatch.setattr(pe, "PYPDF_READER", raise_reader, raising=False)

    # Dummy LTTextContainer and extract_pages to simulate pdfminer
    class DummyText:
        def __init__(self, t):
            self._t = t

        def get_text(self):
            return self._t

    def fake_extract_pages(path) -> Iterator[List[DummyText]]:
        yield [DummyText("X")]
        yield [DummyText("Y")]

    monkeypatch.setattr(pe, "PDFMINER_LT", DummyText, raising=False)
    monkeypatch.setattr(pe, "PDFMINER_EXTRACT_PAGES", fake_extract_pages, raising=False)

    texts = pe.extract_text_per_page("dummy.pdf", provider="auto")
    assert texts == ["X", "Y"]


def test_cli_writes_json_and_ndjson(monkeypatch, tmp_path):
    # Monkeypatch extract_text_per_page to return predictable pages
    monkeypatch.setattr("ingest.cli.extract_text_per_page", lambda p, **k: ["P1", "P2"], raising=False)
# Prepare dummy input files
    f1 = tmp_path / "a.pdf"
    f2 = tmp_path / "b.pdf"
    f1.write_bytes(b"%PDF-1.4")
    f2.write_bytes(b"%PDF-1.4")

    # JSON (array) output for multiple inputs
    json_out = tmp_path / "out.json"
    args = [
        "prog",
        "--glob",
        str(tmp_path / "*.pdf"),
        "--out",
        str(json_out),
        "--provider",
        "auto",
    ]
    monkeypatch.setenv("PYTHONWARNINGS", "ignore")
    monkeypatch.setattr("sys.argv", args)
    cli_main()
    data = json.loads(json_out.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) == 2
    assert data[0]["num_pages"] == 2 and data[0]["pages"] == ["P1", "P2"]

    # NDJSON output
    ndjson_out = tmp_path / "out.ndjson"
    args = [
        "prog",
        "--glob",
        str(tmp_path / "*.pdf"),
        "--out",
        str(ndjson_out),
        "--ndjson",
    ]
    monkeypatch.setattr("sys.argv", args)
    cli_main()
    lines = [json.loads(l) for l in ndjson_out.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2
    assert lines[0]["num_pages"] == 2 and lines[0]["pages"] == ["P1", "P2"]

