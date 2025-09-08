from __future__ import annotations

import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
import re

_SPACE_RE = re.compile(r"[ \t\u3000]+")


def _nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


@lru_cache(maxsize=1)
def _load_dict() -> Dict[str, Any]:
    p = Path(__file__).resolve().parents[1] / "resources" / "normalize.yml"
    if not p.exists():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return data


def normalize_text(s: str) -> str:
    s = _nfkc(s)
    s = s.replace("◯", "○").replace("●", "○").replace("◎", "○")
    s = _SPACE_RE.sub(" ", s).strip()
    return s


def _build_alias_map(section: str) -> Dict[str, str]:
    d = _load_dict().get(section, {}) or {}
    m: Dict[str, str] = {}
    for canonical, aliases in d.items():
        can = normalize_text(str(canonical))
        m[can] = can
        for a in aliases or []:
            m[normalize_text(str(a))] = can
    return m


@lru_cache(maxsize=1)
def _roles_map() -> Dict[str, str]:
    return _build_alias_map("roles")


@lru_cache(maxsize=1)
def _committees_map() -> Dict[str, str]:
    return _build_alias_map("committees")


@lru_cache(maxsize=1)
def _names_map() -> Dict[str, str]:
    return _build_alias_map("names")


def normalize_role(s: str | None) -> str | None:
    if not s:
        return s
    t = normalize_text(s)
    return _roles_map().get(t, t)


def normalize_committee(s: str | None) -> str | None:
    if not s:
        return s
    t = normalize_text(s)
    return _committees_map().get(t, t)


def normalize_name(s: str | None) -> str | None:
    if not s:
        return s
    t = normalize_text(s)
    return _names_map().get(t, t)

