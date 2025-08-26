from __future__ import annotations

import re
from typing import Optional, Pattern

"""Pattern utilities for detecting agenda headings and speaker lines."""

# 議題見出し検出：
# - 行内にコロン（:：）が含まれない
# - 次のいずれかの形式に合致
#   * 【...】 / 〔...〕 の括り見出し（行全体）
#   * 第○（漢数字） + 任意テキスト
#   * 数字+.)） + 任意テキスト
#   * 丸印など + 任意テキスト
AGENDA_HEADING_RE: Pattern[str] = re.compile(
    r"^(?!.*[:：])(?:"
    r"【[^】]+】"
    r"|〔[^〕]+〕"
    r"|第[一二三四五六七八九十百]+[ 　]*.+"
    r"|[0-9０-９]{1,3}[.)）][ 　]*.+"
    r"|[◇◆■○●◎・].+"
    r")$"
)

# 話者行検出：「○中妻委員：」「教育長：」「理事者：」「○ 田中議員：」等
SPEAKER_LINE_RE: Pattern[str] = re.compile(
    r"^(?:[○〇]?[ 　]*)"
    r"(?P<name>[^\s　:：]+?)"
    r"(?P<role>委員長|副委員長|委員|議員|部長|課長|教育長|理事者)?"
    r"[ 　]*[:：]"
)

# ページノイズ（— 12 — など）/短い括弧書き（拍手・休憩・参照）/装飾のみの行
PAGE_HEADER_RE: Pattern[str] = re.compile(r"^[―—\-–\s]*\d+\s*[―—\-–\s]*$")
PAREN_NOISE_RE: Pattern[str] = re.compile(r"^（[^）]{1,8}）$")
DECOR_ONLY_RE: Pattern[str] = re.compile(r"^[○〇・◎◇◆■]+$")

ROLE_TITLES = {"委員長", "副委員長", "委員", "議員", "部長", "課長", "教育長", "理事者"}


def normalize_space(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[ \t\u3000]+", " ", s)
    return s


def is_agenda_heading(line: str) -> bool:
    s = normalize_space(line)
    return bool(AGENDA_HEADING_RE.match(s))


def match_speaker_line(line: str) -> Optional[re.Match[str]]:
    s = normalize_space(line)
    return SPEAKER_LINE_RE.match(s)


def is_noise(line: str) -> bool:
    s = normalize_space(line)
    if not s:
        return False
    return bool(PAGE_HEADER_RE.match(s) or PAREN_NOISE_RE.match(s) or DECOR_ONLY_RE.match(s))
