from __future__ import annotations
import os
import re
from dataclasses import dataclass
from typing import List, Pattern

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    base_url: str = os.getenv("BASE_URL", "https://www.city.itabashi.tokyo.jp")
    request_delay: float = float(os.getenv("REQUEST_DELAY", "1.0"))
    timeout_connect: float = float(os.getenv("TIMEOUT_CONNECT", "10"))
    timeout_read: float = float(os.getenv("TIMEOUT_READ", "30"))
    retries: int = int(os.getenv("RETRIES", "3"))
    backoff_base: float = float(os.getenv("BACKOFF_BASE", "1.0"))
    backoff_max: float = float(os.getenv("BACKOFF_MAX", "30.0"))
    max_pages: int = int(os.getenv("MAX_PAGES", "2"))
    max_items: int = int(os.getenv("MAX_ITEMS", "50"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    user_agent: str = os.getenv("USER_AGENT", "ItabashiMinutesBot/0.1 (+contact)")
    allow_pattern: str = os.getenv(
        "ALLOW_PATTERN",
        r"^https?://[^/]+/gikai/kaigiroku/.*",
    )
    deny_patterns_raw: str = os.getenv("DENY_PATTERNS", r"\.zip$,\.csv$")

    @property
    def deny_patterns(self) -> List[str]:
        return [p.strip() for p in self.deny_patterns_raw.split(",") if p.strip()]


def compile_allow(config: Config) -> Pattern[str]:
    return re.compile(config.allow_pattern)


def compile_denies(config: Config) -> List[Pattern[str]]:
    return [re.compile(p) for p in config.deny_patterns]

