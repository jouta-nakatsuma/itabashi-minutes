import json
import subprocess
import sys
from pathlib import Path

from jsonschema import validate


def load_schema(repo_root: Path) -> dict:
    with open(repo_root / "schemas" / "minutes.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_minimal_record_validates(repo_root: Path = Path(__file__).resolve().parents[1]):
    schema = load_schema(repo_root)
    minimal = {
        "meeting_date": "2024-03-15",
        "committee": "本会議",
        "title": "令和6年第1回定例会第3日",
        "page_url": "https://www.city.itabashi.tokyo.jp/gikai/kaigiroku/r06/240315.html",
        "crawled_at": "2024-03-20T10:30:00Z",
    }
    validate(instance=minimal, schema=schema)


def test_compat_checker_pass_and_fail(tmp_path: Path, repo_root: Path = Path(__file__).resolve().parents[1]):
    # Base: current schema (write to temp file)
    current_schema = load_schema(repo_root)
    base_file = tmp_path / "base.json"
    base_file.write_text(json.dumps(current_schema, ensure_ascii=False, indent=2), encoding="utf-8")

    # 1) Pass: new = current (no changes)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "check_schema_compat.py"),
        "--base-file",
        str(base_file),
        "--path",
        str(repo_root / "schemas" / "minutes.schema.json"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"compat should pass, stderr={r.stderr}"

    # 2) Fail: add a new top-level required key (breaking)
    new_schema = json.loads(json.dumps(current_schema))
    req = set(new_schema.get("required", []))
    req.add("new_required_field")
    new_schema["required"] = sorted(req)
    new_file = tmp_path / "new.json"
    new_file.write_text(json.dumps(new_schema, ensure_ascii=False, indent=2), encoding="utf-8")

    cmd2 = [
        sys.executable,
        str(repo_root / "tools" / "check_schema_compat.py"),
        "--base-file",
        str(base_file),
        "--path",
        str(new_file),
    ]
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    assert r2.returncode == 1, f"compat should fail, stderr={r2.stderr}"
    assert "required added" in r2.stderr

