from __future__ import annotations

from pathlib import Path
import contextlib, os

from scripts.one_shot_apply import apply_to_repo


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8", newline="")


@contextlib.contextmanager
def chdir(p: Path):
    old = os.getcwd()
    os.chdir(p)
    try:
        yield
    finally:
        os.chdir(old)


def test_apply_add_only(tmp_path: Path) -> None:
    target = tmp_path / "A.txt"
    _write(target, "hello\n")
    diff = """
diff --git a/A.txt b/A.txt
--- a/A.txt
+++ b/A.txt
@@ -1,1 +1,2 @@
 hello
+world
""".strip()
    with chdir(tmp_path):
        summary = apply_to_repo(diff, dry_run=False, strip=1, fuzz=0, backup=False, verbose=False)
    assert (tmp_path / "A.txt").read_text(encoding="utf-8") == "hello\nworld\n"
    assert summary.applied >= 1


def test_apply_delete_only(tmp_path: Path) -> None:
    target = tmp_path / "B.txt"
    _write(target, "keep\nremove\n")
    diff = """
diff --git a/B.txt b/B.txt
--- a/B.txt
+++ b/B.txt
@@ -1,2 +1,1 @@
 keep
-remove
""".strip()
    with chdir(tmp_path):
        summary = apply_to_repo(diff, dry_run=False, strip=1, fuzz=0, backup=False, verbose=False)
    assert (tmp_path / "B.txt").read_text(encoding="utf-8") == "keep\n"
    assert summary.applied >= 1


def test_apply_mixed_replace(tmp_path: Path) -> None:
    target = tmp_path / "C.txt"
    _write(target, "old\nline\n")
    diff = """
diff --git a/C.txt b/C.txt
--- a/C.txt
+++ b/C.txt
@@ -1,2 +1,2 @@
-old
+new
 line
""".strip()
    with chdir(tmp_path):
        summary = apply_to_repo(diff, dry_run=False, strip=1, fuzz=0, backup=False, verbose=False)
    assert (tmp_path / "C.txt").read_text(encoding="utf-8") == "new\nline\n"
    assert summary.applied >= 1


def test_apply_context_mismatch_fail(tmp_path: Path) -> None:
    target = tmp_path / "D.txt"
    _write(target, "x\ny\nz\n")
    diff = """
diff --git a/D.txt b/D.txt
--- a/D.txt
+++ b/D.txt
@@ -1,3 +1,3 @@
 x
-y
+Y
 z
""".strip()
    with chdir(tmp_path):
        summary = apply_to_repo(diff, dry_run=False, strip=1, fuzz=0, backup=False, verbose=False)
    assert summary.skipped >= 1
    # original intact
    assert (tmp_path / "D.txt").read_text(encoding="utf-8") == "x\ny\nz\n"


def test_apply_crlf_eol_preserved(tmp_path: Path) -> None:
    target = tmp_path / "E.txt"
    # CRLF file
    target.write_bytes(b"a\r\nb\r\n")
    diff = """
diff --git a/E.txt b/E.txt
--- a/E.txt
+++ b/E.txt
@@ -1,2 +1,3 @@
 a
 b
+c
""".strip()
    with chdir(tmp_path):
        summary = apply_to_repo(diff, dry_run=False, strip=1, fuzz=0, backup=False, verbose=False)
    data = (tmp_path / "E.txt").read_bytes()
    assert b"\r\n" in data  # EOL preserved
    assert data.endswith(b"c\r\n")


def test_idempotent_apply(tmp_path: Path) -> None:
    target = tmp_path / "F.txt"
    _write(target, "alpha\n")
    diff = """
diff --git a/F.txt b/F.txt
--- a/F.txt
+++ b/F.txt
@@ -1,1 +1,2 @@
 alpha
+beta
""".strip()
    with chdir(tmp_path):
        summary1 = apply_to_repo(diff, dry_run=False, strip=1, fuzz=0, backup=False, verbose=False)
    with chdir(tmp_path):
        summary2 = apply_to_repo(diff, dry_run=False, strip=1, fuzz=0, backup=False, verbose=False)
    assert (tmp_path / "F.txt").read_text(encoding="utf-8") == "alpha\nbeta\n"

