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
COLON_CLASS = r"[:：\uFE13]"  # ":" "：" "︓"
BULLET_CLASS = r"[○◯●◎]?"
_GENERIC_HEAD = r"(?:議題|案件|報告事項|所管事務調査)"
_NO_TOPIC_TAIL = r"(?!について|に関する|の報告)"
AGENDA_HEADING_RE: Pattern[str] = re.compile(
    rf"^(?:{BULLET_CLASS}\s*)?(?:"
    rf"【[^】]+】"
    rf"|〔[^〕]+〕"
    # generic head: colon付きは許容、colon無しは“について/に関する/の報告”を除外
    rf"|{_GENERIC_HEAD}\s*{COLON_CLASS}\s*.+"
    rf"|{_GENERIC_HEAD}\s*{_NO_TOPIC_TAIL}\s*.+"
    rf"|議案第[〇一二三四五六七八九十百千0-9]+号\s*{COLON_CLASS}?\s*.+"
    rf"|請願第.*?号\s*{COLON_CLASS}?\s*.+"
    rf"|陳情第.*?号\s*{COLON_CLASS}?\s*.+"
    rf"|第[一二三四五六七八九十百]+[ 　]*.+"
    rf"|[0-9０-９]{{1,3}}[.)）][ 　]*.+"
    rf"|[◇◆■○●◎・].+"
    rf")$"
)

# 話者行検出：「○中妻委員：」「教育長：」「理事者：」「○ 田中議員：」等
ROLE_PART = r"(?:委員長|副委員長|委員|議員|部長|課長|教育長|理事者|副区長)"
NAME_PART = r"[一-龥々ヵヶ゙゜・ー\u30A0-\u30FF\u3040-\u309F]{1,12}"
SPEAKER_LINE_RE_A: Pattern[str] = re.compile(
    rf"^(?:{BULLET_CLASS}\s*)?(?P<role>{ROLE_PART})\s*(?P<name>{NAME_PART})\s*{COLON_CLASS}\s+"
)
SPEAKER_LINE_RE_B: Pattern[str] = re.compile(
    rf"^(?:{BULLET_CLASS}\s*)?(?P<name>{NAME_PART})\s*{COLON_CLASS}\s+"
)
SPEAKER_LINE_RE_C: Pattern[str] = re.compile(
    rf"^(?:{BULLET_CLASS}\s*)?(?P<role>{ROLE_PART})\s*{COLON_CLASS}\s+"
)

# ページノイズ（— 12 — など）/短い括弧書き（拍手・休憩・参照）/装飾のみの行
PAGE_HEADER_RE: Pattern[str] = re.compile(r"^[―—\-–\s]*\d+\s*[―—\-–\s]*$")
PAREN_NOISE_RE: Pattern[str] = re.compile(r"^（[^）]{1,8}）$")
DECOR_ONLY_RE: Pattern[str] = re.compile(r"^[○〇・◎◇◆■]+$")

ROLE_TITLES = {"委員長", "副委員長", "委員", "議員", "部長", "課長", "教育長", "理事者", "副区長"}


def normalize_space(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[ \t\u3000]+", " ", s)
    return s


def is_agenda_heading(line: str) -> bool:
    s = normalize_space(line)
    return bool(AGENDA_HEADING_RE.match(s))


def match_speaker_line(line: str) -> Optional[re.Match[str]]:
    s = normalize_space(line)
    m = SPEAKER_LINE_RE_A.match(s)
    if m:
        return m
    m = SPEAKER_LINE_RE_B.match(s)
    if m:
        return m
    return SPEAKER_LINE_RE_C.match(s)


def is_noise(line: str) -> bool:
    s = normalize_space(line)
    if not s:
        return False
    return bool(PAGE_HEADER_RE.match(s) or PAREN_NOISE_RE.match(s) or DECOR_ONLY_RE.match(s))
