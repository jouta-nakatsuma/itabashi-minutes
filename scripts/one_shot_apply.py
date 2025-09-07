from __future__ import annotations

import argparse
import io
import sys
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]


@dataclass
class Patch:
    path: Path
    hunks: List[Hunk]


@dataclass
class ApplyResult:
    path: Path
    applied_hunks: int
    skipped_hunks: int
    already_applied: bool = False


@dataclass
class Summary:
    files: int
    applied: int
    skipped: int
    already: int


def _strip_prefix(p: str, strip: int) -> str:
    parts = Path(p).parts
    return str(Path(*parts[strip:])) if strip and len(parts) > strip else p


def parse_unified_diff(text: str, strip: int = 1) -> List[Patch]:
    """
    Index-based parser with safe push-back.
    Supports git-style unified diffs with multiple hunks/files.
    """
    lines = text.splitlines()
    i = 0
    patches: List[Patch] = []
    current_path: Optional[Path] = None
    current_hunks: List[Hunk] = []

    def flush() -> None:
        nonlocal current_path, current_hunks
        if current_path and current_hunks:
            patches.append(Patch(path=current_path, hunks=current_hunks))
        current_path = None
        current_hunks = []

    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            flush()
            i += 1
            continue
        if line.startswith("--- "):
            # expect +++ next
            if i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
                raise ValueError("Malformed unified diff: expected '+++' after '---'")
            new_path = lines[i + 1][4:].strip()
            p = new_path
            if p.startswith("a/") or p.startswith("b/"):
                p = p[2:]
            p = _strip_prefix(p, strip=0 if "/" in new_path[:2] else strip)
            current_path = Path(p)
            i += 2
            continue
        if line.startswith("@@ "):
            header = line
            try:
                span = header.split("@@")[1].strip().split()
                left, right = span[0], span[1]
            except Exception as e:
                raise ValueError(f"Malformed hunk header: {header}") from e
            def parse_span(tok: str) -> Tuple[int, int]:
                tok = tok[1:]
                if "," in tok:
                    a, b = tok.split(",", 1)
                    return int(a), int(b)
                return int(tok), 1
            old_start, old_count = parse_span(left)
            new_start, new_count = parse_span(right)
            i += 1
            h_lines: List[str] = []
            # collect hunk lines
            while i < len(lines):
                l = lines[i]
                if l.startswith("@@ ") or l.startswith("diff --git ") or l.startswith("--- "):
                    break
                if not l or l[0] not in " +-":
                    h_lines.append(" " + l)
                else:
                    h_lines.append(l)
                i += 1
            current_hunks.append(Hunk(old_start, old_count, new_start, new_count, h_lines))
            continue
        # any other line: skip
        i += 1
    flush()
    return patches


def _detect_eol_and_bom(data: bytes) -> Tuple[str, bool]:
    bom = data.startswith(b"\xef\xbb\xbf")
    text = data.decode("utf-8-sig")
    # detect EOL from original
    if "\r\n" in text:
        return "\r\n", bom
    return "\n", bom


def _is_under(root: Path, child: Path) -> bool:
    try:
        return child.is_relative_to(root)  # py>=3.9
    except AttributeError:
        return os.path.commonpath([str(root), str(child)]) == str(root)

def apply_patch_to_file(path: Path, patch: Patch, *, dry_run: bool = False, fuzz: int = 0, backup: bool = False, verbose: bool = False) -> ApplyResult:
    repo_root = Path.cwd().resolve()
    try:
        target = path.resolve()
    except Exception:
        return ApplyResult(path=path, applied_hunks=0, skipped_hunks=len(patch.hunks))
    if not _is_under(repo_root, target):
        return ApplyResult(path=path, applied_hunks=0, skipped_hunks=len(patch.hunks))

    original_bytes = path.read_bytes() if path.exists() else b""
    eol, bom = _detect_eol_and_bom(original_bytes)
    original = original_bytes.decode("utf-8-sig") if original_bytes else ""
    original_lines = original.splitlines()

    new_lines = original_lines[:]
    applied = 0
    skipped = 0

    def find_context(start_idx: int, ctx: List[str]) -> Optional[int]:
        # strict match first
        if start_idx - 1 < len(new_lines) and new_lines[start_idx - 1 : start_idx - 1 + len(ctx)] == ctx:
            return start_idx - 1
        if fuzz <= 0:
            return None
        # fuzzy search within ±fuzz lines
        window = range(max(0, start_idx - 1 - fuzz), min(len(new_lines), start_idx - 1 + fuzz + 1))
        for i in window:
            if new_lines[i : i + len(ctx)] == ctx:
                return i
        return None

    for h in patch.hunks:
        # build expected context and operations
        ctx: List[str] = [l[1:] for l in h.lines if l.startswith(" ")]
        plus: List[str] = [l[1:] for l in h.lines if l.startswith("+")]
        minus: List[str] = [l[1:] for l in h.lines if l.startswith("-")]
        idx = find_context(h.old_start, ctx)
        if idx is None:
            skipped += 1
            continue
        # verify minus lines match following the context
        minus_block: List[str] = []
        for l in h.lines:
            if l.startswith("-"):
                minus_block.append(l[1:])
            elif l.startswith(" ") and minus_block:
                break
        # compute edit range
        edit_start = idx
        edit_end = idx + len(ctx)
        candidate = new_lines[:edit_start] + new_lines[edit_end:]
        # remove minus where they appear after context
        # (simple strategy: rebuild block around context)
        block = new_lines[edit_start:edit_end]
        # replace block with context first
        new_block = ctx[:]
        # remove minus lines immediately after context in file
        after_idx = edit_end
        for m in minus_block:
            if after_idx < len(new_lines) and new_lines[after_idx] == m:
                del new_lines[after_idx]
        # insert plus lines after context
        insert_pos = edit_start + len(ctx)
        for p in plus:
            new_lines.insert(insert_pos, p)
            insert_pos += 1
        applied += 1

    # Decide if already applied (no change)
    final_text = (eol.join(new_lines) + (eol if new_lines else ""))
    final = (b"\xef\xbb\xbf" if bom else b"") + final_text.encode("utf-8")
    if original_bytes == final:
        # Normalize: already applied means skipped=0
        return ApplyResult(path=path, applied_hunks=applied, skipped_hunks=0, already_applied=True)
    if dry_run:
        return ApplyResult(path=path, applied_hunks=applied, skipped_hunks=skipped)
    # backup if requested
    if backup and path.exists():
        path.with_suffix(path.suffix + ".bak").write_bytes(original_bytes)
    # write atomically
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(final)
    tmp.replace(path)
    return ApplyResult(path=path, applied_hunks=applied, skipped_hunks=skipped)


def apply_to_repo(diff_text: str, *, dry_run: bool = False, strip: int = 1, fuzz: int = 0, backup: bool = False, verbose: bool = False) -> Summary:
    patches = parse_unified_diff(diff_text, strip=strip)
    files = applied = skipped = already = 0
    for p in patches:
        files += 1
        if not p.path.exists():
            # create empty file baseline
            p.path.parent.mkdir(parents=True, exist_ok=True)
            p.path.write_text("", encoding="utf-8")
        res = apply_patch_to_file(p.path, p, dry_run=dry_run, fuzz=fuzz, backup=backup, verbose=verbose)
        applied += res.applied_hunks
        skipped += 0 if res.already_applied else res.skipped_hunks
        already += 1 if res.already_applied else 0
    return Summary(files=files, applied=applied, skipped=skipped, already=already)


def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Safely apply a unified diff to the repo (one-shot)")
    ap.add_argument("--diff", help="Path to unified diff file (default: stdin)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup", action="store_true")
    ap.add_argument("--strip", type=int, default=1)
    ap.add_argument("--fuzz", type=int, default=0)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.diff:
        diff_text = Path(args.diff).read_text(encoding="utf-8")
    else:
        diff_text = sys.stdin.read()
    if not diff_text.strip():
        print("No diff provided", file=sys.stderr)
        return 2
    summary = apply_to_repo(diff_text, dry_run=args.dry_run, strip=args.strip, fuzz=args.fuzz, backup=args.backup, verbose=args.verbose)
    print(f"files={summary.files} applied={summary.applied} skipped={summary.skipped} already={summary.already}")
    return 0 if summary.skipped == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
