#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import logging
import os
import random
import time
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Set, cast
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from urllib import robotparser

from .config import Config, compile_allow, compile_denies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_date(text: str) -> Optional[str]:
    """
    Detects a date string in either Gregorian (YYYY年M月D日) or Reiwa (令和N年M月D日) formats.
    Returns ISO date string 'YYYY-MM-DD' or None if not found/invalid.
    """
    import re

    if not text:
        return None

    # Try Gregorian first: 2024年3月15日
    m = re.search(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日", text)
    if m:
        y, mo, d = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        try:
            _ = date(y, mo, d)
            return f"{y:04d}-{mo:02d}-{d:02d}"
        except ValueError:
            return None

    # Try Reiwa: 令和6年3月15日 -> year = 2018 + 6 = 2024
    m = re.search(r"令和\s*(\d{1,2})年\s*(\d{1,2})月\s*(\d{1,2})日", text)
    if m:
        ry, mo, d = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        y = 2018 + ry
        try:
            _ = date(y, mo, d)
            return f"{y:04d}-{mo:02d}-{d:02d}"
        except ValueError:
            return None

    return None

class ItabashiMinutesCrawler:
    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        logging.getLogger().setLevel(
            getattr(logging, self.config.log_level.upper(), logging.INFO)
        )
        self.base_url = self.config.base_url.rstrip("/")
        self.allow_re = compile_allow(self.config)
        self.deny_res = compile_denies(self.config)
        self.minutes_root = urljoin(self.base_url + "/", "gikai/kaigiroku/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})
        self.robots = self._load_robots()

    def _load_robots(self) -> robotparser.RobotFileParser:
        rp = robotparser.RobotFileParser()
        rp.set_url(urljoin(self.base_url + "/", "robots.txt"))
        try:
            rp.read()
        except Exception as e:
            # 読み込み失敗は警告ログのみ。許可判定は can_fetch 側を try/except True。
            logger.warning("Failed to read robots.txt: %s", e)
        return rp

    def _allowed(self, url: str) -> bool:
        if not self.allow_re.match(url):
            return False
        for d in self.deny_res:
            if d.search(url):
                return False
        try:
            return self.robots.can_fetch(self.config.user_agent, url)
        except Exception:
            return True

    def _sleep_polite(self) -> None:
        delay = self.config.request_delay * random.uniform(0.9, 1.1)
        time.sleep(max(0.0, delay))

    def _compute_backoff(self, attempt: int) -> float:
        base = self.config.backoff_base * (2 ** attempt)
        jitter = base * random.uniform(-0.1, 0.1)
        return min(self.config.backoff_max, max(0.0, base + jitter))

    def _make_request(self, url: str) -> Optional[requests.Response]:
        if not self._allowed(url):
            logger.debug("Blocked by allow/deny/robots: %s", url)
            return None
        last_exc: Optional[Exception] = None
        for attempt in range(self.config.retries + 1):
            try:
                self._sleep_polite()
                resp = self.session.get(
                    url,
                    timeout=(self.config.timeout_connect, self.config.timeout_read),
                )
                status = resp.status_code
                if status in (429, 503):
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait = float(retry_after)
                        except ValueError:
                            wait = self._compute_backoff(attempt)
                    else:
                        wait = self._compute_backoff(attempt)
                    logger.warning(
                        "Retryable status %s for %s; sleeping %.2fs", status, url, wait
                    )
                    time.sleep(wait)
                    last_exc = None
                    continue
                resp.raise_for_status()
                return resp
            except requests.Timeout as e:
                last_exc = e
                wait = self._compute_backoff(attempt)
                logger.warning("Timeout for %s; sleeping %.2fs", url, wait)
                time.sleep(wait)
            except requests.RequestException as e:
                code = getattr(getattr(e, "response", None), "status_code", None)
                if code and 400 <= code < 500 and code not in (429,):
                    logger.warning("Non-retryable HTTP %s for %s", code, url)
                    return None
                last_exc = e
                wait = self._compute_backoff(attempt)
                logger.warning("Request error for %s; sleeping %.2fs", url, wait)
                time.sleep(wait)
        if last_exc:
            logger.error("Request permanently failed for %s: %s", url, last_exc)
        return None

    def get_latest_fiscal_year_minutes(self) -> List[Dict[str, Any]]:
        visited: Set[str] = set()
        items: List[Dict[str, Any]] = []
        pages = 0
        url = self.minutes_root
        while True:
            if pages >= self.config.max_pages:
                break
            if url in visited:
                break
            visited.add(url)
            resp = self._make_request(url)
            if not resp:
                break
            soup = BeautifulSoup(resp.content, "html.parser")
            for a in soup.select("main a[href], .content a[href]"):
                href = a.get("href")
                if not href:
                    continue
                abs_url = urljoin(url, href)
                if not self._allowed(abs_url):
                    continue
                if abs_url.lower().endswith(".pdf"):
                    continue
                title = a.get_text(strip=True)

                # fetch meeting page to detect date from main content; fallback to link text
                meeting_resp = self._make_request(abs_url)
                if not meeting_resp:
                    continue
                meeting_soup = BeautifulSoup(meeting_resp.content, "html.parser")
                parts = meeting_soup.select("article, section, #main, .content")
                text_blob = (
                    " ".join(
                        p.get_text(separator=" ", strip=True) for p in parts
                    )
                    if parts
                    else meeting_soup.get_text(separator=" ", strip=True)
                )
                meeting_dt = detect_date(text_blob) or detect_date(title)
                if not meeting_dt:
                    # skip records without meeting_date to satisfy schema
                    continue
                logger.info("parsed meeting_date=%s", meeting_dt)

                record = self._extract_minute_data(
                    abs_url, title, soup=meeting_soup, meeting_date_override=meeting_dt
                )
                if record:
                    items.append(record)
                    if len(items) >= self.config.max_items:
                        break
            if len(items) >= self.config.max_items:
                break
            # nextリンク探索
            next_link = soup.find("a", attrs={"rel": "next"})
            if not next_link:
                next_link = soup.find("a", string=lambda s: bool(s and "次" in s))
            if not next_link or not next_link.get("href"):
                break
            next_url = urljoin(url, cast(str, next_link["href"]))
            if next_url in visited:
                break
            url = next_url
            pages += 1
        return items

    def _extract_minute_data(
        self,
        url: str,
        title: str,
        soup: Optional[BeautifulSoup] = None,
        meeting_date_override: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if soup is None:
            resp = self._make_request(url)
            if not resp:
                return None
            soup = BeautifulSoup(resp.content, "html.parser")
        meeting_date = meeting_date_override or self._extract_date(title, soup)
        committee = self._extract_committee(title, soup)
        pdf = self._find_pdf_url(soup, url)
        agenda = self._extract_agenda_items(soup)
        meeting_id = self._make_meeting_id(meeting_date, committee, url, title)
        return {
            "meeting_id": meeting_id,  # スキーマ検証時は投影で除外
            "meeting_date": meeting_date,
            "committee": committee,
            "title": title,
            "page_url": url,
            "pdf_url": pdf,
            "agenda_items": agenda,
            "crawled_at": datetime.now().isoformat(),
        }

    def _make_meeting_id(
        self, date: Optional[str], committee: str, url: str, title: str
    ) -> str:
        base = f"{date or 'unknown'}_{committee}".encode("utf-8")
        h = hashlib.sha1(base + url.encode("utf-8") + title.encode("utf-8")).hexdigest()[
            :8
        ]
        return f"{(date or 'unknown')}_{committee}_{h}"

    def _extract_date(self, title: str, soup: BeautifulSoup) -> Optional[str]:
        import re

        m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", title)
        if m:
            y, mo, d = m.groups()
            return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
        return None

    def _extract_committee(self, title: str, soup: BeautifulSoup) -> str:
        if "本会議" in title:
            return "本会議"
        if "常任委員会" in title:
            return "常任委員会"
        if "特別委員会" in title:
            return "特別委員会"
        return "その他"

    def _find_pdf_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        link = soup.find("a", href=lambda x: bool(x and x.lower().endswith(".pdf")))
        if link:
            href = cast(str, link["href"])
            return urljoin(base_url, href)
        return None

    def _extract_agenda_items(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        agenda_items: List[Dict[str, Any]] = []
        content_divs = soup.find_all(
            ["div", "section"], class_=lambda x: bool(x and "content" in x)
        )
        for i, div in enumerate(content_divs[:3]):
            text_content = div.get_text().strip()
            if len(text_content) > 50:
                agenda_items.append(
                    {
                        "agenda_item": f"議事{i+1}",
                        "speaker": "議長",
                        "speech_text": text_content[:500],
                        "page_no": i + 1,
                    }
                )
        return agenda_items


def main() -> None:
    # 後方互換（推奨は crawler.cli:main）
    crawler = ItabashiMinutesCrawler(Config())
    logger.info("Starting Itabashi minutes crawl...")
    minutes = crawler.get_latest_fiscal_year_minutes()
    output_file = "crawler/sample/sample_minutes.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(minutes, f, ensure_ascii=False, indent=2)
    logger.info("Crawled %d minutes. Output saved to %s", len(minutes), output_file)


if __name__ == "__main__":
    main()
