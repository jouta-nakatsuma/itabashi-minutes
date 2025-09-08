from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

try:
    from pydantic import BaseModel, Field  # type: ignore
    _USE_PYDANTIC = True
except Exception:  # pragma: no cover - fallback if pydantic not installed
    from dataclasses import asdict, dataclass, field as dataclass_field
    _USE_PYDANTIC = False

from .patterns import (
    ROLE_TITLES,
    is_agenda_heading,
    is_noise,
    match_speaker_line,
    normalize_space,
)
from .normalize import normalize_role, normalize_name, normalize_committee

if _USE_PYDANTIC:
    class Speech(BaseModel):
        speaker: str = Field(..., description="話者名（役職語を除いたコア名）")
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
else:
    @dataclass
    class Speech:  # type: ignore[no-redef]
        speaker: str
        role: Optional[str] = None
        paragraphs: List[str] = dataclass_field(default_factory=list)

        def model_dump(self) -> Dict[str, Any]:  # pragma: no cover - simple passthrough
            return asdict(self)

    @dataclass
    class AgendaItem:  # type: ignore[no-redef]
        title: str
        order_no: int
        speeches: List[Speech] = dataclass_field(default_factory=list)

        def model_dump(self) -> Dict[str, Any]:  # pragma: no cover
            return asdict(self)

    @dataclass
    class MinutesStructure:  # type: ignore[no-redef]
        meeting_date: Optional[str] = None
        committee: Optional[str] = None
        page_url: Optional[str] = None
        pdf_url: Optional[str] = None
        agenda_items: List[AgendaItem] = dataclass_field(default_factory=list)

        def model_dump(self) -> Dict[str, Any]:  # pragma: no cover
            return asdict(self)


def _read_input_text(obj: Mapping[str, Any]) -> str:
    if isinstance(obj.get("text"), str):
        return obj["text"]
    pages = obj.get("pages")
    if isinstance(pages, list) and pages and all(isinstance(p, str) for p in pages):
        return "\n".join(pages)
    if isinstance(obj.get("content"), str):
        return obj["content"]
    return ""


def _split_lines(text: str) -> List[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [ln.rstrip() for ln in text.split("\n")]


def _scan_agenda_boundaries(lines: List[str]) -> List[Tuple[int, str]]:
    boundaries: List[Tuple[int, str]] = []
    for idx, raw in enumerate(lines):
        line = normalize_space(raw)
        if not line or is_noise(line):
            continue
        if is_agenda_heading(line):
            boundaries.append((idx, line))
    return boundaries


def _flush_paragraph(buf: List[str], out: List[str]) -> None:
    if buf:
        joined = normalize_space("".join(buf).strip())
        if joined:
            out.append(joined)
        buf.clear()


def _split_after_colon(line: str) -> Tuple[str, str]:
    for i, ch in enumerate(line):
        if ch in (":", "：", "\uFE13"):
            return line[: i + 1], line[i + 1 :].strip()
    return line, ""


def _parse_block_speeches(lines: List[str], start: int, end: int) -> List[Speech]:
    speeches: List[Speech] = []
    current: Optional[Speech] = None
    para_buf: List[str] = []
    i = start
    while i < end:
        raw = lines[i]
        line = normalize_space(raw)
        if not line or is_noise(line):
            _flush_paragraph(para_buf, current.paragraphs if current else [])
            i += 1
            continue
        m = match_speaker_line(line)
        if m:
            if current is not None:
                _flush_paragraph(para_buf, current.paragraphs)
                speeches.append(current)
                current = None
            name = (m.groupdict().get("name") or "").strip()
            role = m.groupdict().get("role")
            if role is None and name in ROLE_TITLES:
                role = name
            speaker = name.lstrip("○").strip()
            # apply normalization
            role = normalize_role(role)
            speaker = normalize_name(speaker) or speaker
            current = Speech(speaker=speaker, role=role, paragraphs=[])
            _, tail = _split_after_colon(raw)
            if tail:
                para_buf.append(tail + "\n")
            i += 1
            continue
        if current is not None:
            para_buf.append(line + "\n")
        i += 1
    if current is not None:
        _flush_paragraph(para_buf, current.paragraphs)
        speeches.append(current)
    return speeches


def extract_minutes_structure(src: Path | str | Mapping[str, Any]) -> MinutesStructure:
    if isinstance(src, (str, Path)):
        obj: Dict[str, Any] = json.loads(Path(src).read_text(encoding="utf-8"))
    else:
        obj = dict(src)
    text = _read_input_text(obj)
    lines = _split_lines(text)
    boundaries = _scan_agenda_boundaries(lines)
    ms = MinutesStructure(
        meeting_date=obj.get("meeting_date"),
        committee=normalize_committee(obj.get("committee")),
        page_url=obj.get("page_url"),
        pdf_url=obj.get("pdf_url"),
        agenda_items=[],
    )
    if not boundaries:
        speeches = _parse_block_speeches(lines, 0, len(lines))
        ms.agenda_items.append(AgendaItem(title="（議題なし）", order_no=1, speeches=speeches))
        return ms
    idxs = [i for i, _ in boundaries] + [len(lines)]
    titles = [t for _, t in boundaries]
    for order_no, (start, end) in enumerate(zip(idxs[:-1], idxs[1:]), start=1):
        title = titles[order_no - 1]
        speeches = _parse_block_speeches(lines, start + 1, end)
        ms.agenda_items.append(AgendaItem(title=title, order_no=order_no, speeches=speeches))
    return ms


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Extract agenda/speeches structure from normalized minutes JSON")
    parser.add_argument("--src", required=True, help="Input JSON file path")
    parser.add_argument("--out", required=False, help="Output JSON file path")
    args = parser.parse_args(list(argv) if argv is not None else None)
    ms = extract_minutes_structure(args.src)
    out_text = json.dumps(ms.model_dump(), ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(out_text + "\n", encoding="utf-8")
    else:
        print(out_text)


if __name__ == "__main__":
    main()
