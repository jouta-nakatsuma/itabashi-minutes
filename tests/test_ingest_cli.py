import json, pathlib, subprocess, sys
import ingest.cli as cli

def test_cli_outputs_json(monkeypatch, tmp_path):
    # 本物の抽出は走らせず、CLI が参照するシンボルを差し替える（前回と同じ発想）
    monkeypatch.setattr("ingest.cli.extract_text_per_page",
                        lambda p, **k: ["P1", "P2"], raising=False)
    inp = tmp_path/"dummy.pdf"
    inp.write_bytes(b"%PDF-1.4 dummy")

    out = tmp_path/"out.json"
    # エントリポイント関数があるなら直接呼ぶ。無ければ subprocess で poetry run を使う
    cli.main(["--input", str(inp), "--out", str(out)])

    data = json.loads(out.read_text())
    assert data["pages"] == ["P1","P2"]
