#!/usr/bin/env python3
"""
板橋区議会会議録クローラー
Itabashi Ward Council Minutes Crawler
"""

import time
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, cast

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin  # urlparse は未使用なので削除

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ItabashiMinutesCrawler:
    def __init__(self, base_url: str = "https://www.city.itabashi.tokyo.jp",
                 request_delay: float = 1.0) -> None:
        self.base_url = base_url
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ItabashiMinutesCrawler/1.0 (Research Purpose)'
        })

    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with rate limiting and error handling"""
        try:
            time.sleep(self.request_delay)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def get_latest_fiscal_year_minutes(self) -> List[Dict[str, Any]]:
        """Crawl minutes from the latest fiscal year"""
        minutes_url = urljoin(self.base_url, "/gikai/kaigiroku/")

        response = self._make_request(minutes_url)
        if not response:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        minutes_data: List[Dict[str, Any]] = []

        # Find meeting links (placeholder implementation)
        meeting_links = soup.find_all('a', href=True)
        for link in meeting_links[:5]:  # Limit to first 5 for demo
            href: Optional[str] = link.get('href')
            if not href:
                continue
            if 'kaigiroku' in href.lower():
                full_url = urljoin(self.base_url, href)
                minute_data = self._extract_minute_data(full_url, link.get_text().strip())
                if minute_data is not None:
                    minutes_data.append(minute_data)

        return minutes_data

    def _extract_minute_data(self, url: str, title: str) -> Optional[Dict[str, Any]]:
        """Extract structured data from a single meeting minute page"""
        response = self._make_request(url)
        if not response:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        minute_data: Dict[str, Any] = {
            "meeting_date": self._extract_date(title, soup),
            "committee": self._extract_committee(title, soup),
            "title": title,
            "page_url": url,
            "pdf_url": self._find_pdf_url(soup, url),
            "agenda_items": self._extract_agenda_items(soup),
            "crawled_at": datetime.now().isoformat(),
        }

        return minute_data

    def _extract_date(self, title: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract meeting date from title or page content"""
        import re
        date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        match = re.search(date_pattern, title)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return None

    def _extract_committee(self, title: str, soup: BeautifulSoup) -> str:
        """Extract committee name"""
        if "本会議" in title:
            return "本会議"
        if "常任委員会" in title:
            return "常任委員会"
        if "特別委員会" in title:
            return "特別委員会"
        return "その他"

    def _find_pdf_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find PDF download URL"""
        pdf_links = soup.find_all('a', href=lambda x: bool(x and x.endswith('.pdf')))
        if pdf_links:
            # Tag['href'] は Any 扱いになるので明示キャスト
            href = cast(str, pdf_links[0]['href'])
            return urljoin(base_url, href)
        return None

    def _extract_agenda_items(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract agenda items and speeches"""
        agenda_items: List[Dict[str, Any]] = []

        # This is a simplified extraction - real implementation would be more complex
        content_divs = soup.find_all(['div', 'section'], class_=lambda x: bool(x and 'content' in x))

        for i, div in enumerate(content_divs[:3]):  # Limit for demo
            text_content = div.get_text().strip()
            if len(text_content) > 50:  # Only substantial content
                agenda_item: Dict[str, Any] = {
                    "agenda_item": f"議事{i+1}",
                    "speaker": "議長",  # Placeholder
                    "speech_text": text_content[:500],  # Truncate for demo
                    "page_no": i + 1,
                }
                agenda_items.append(agenda_item)

        return agenda_items


def main() -> None:
    """Main crawling function"""
    crawler = ItabashiMinutesCrawler()

    logger.info("Starting Itabashi minutes crawl...")
    minutes = crawler.get_latest_fiscal_year_minutes()

    output_file = "crawler/sample/sample_minutes.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(minutes, f, ensure_ascii=False, indent=2)

    logger.info(f"Crawled {len(minutes)} minutes. Output saved to {output_file}")


if __name__ == "__main__":
    main()
