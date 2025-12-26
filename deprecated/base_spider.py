import logging
import random
import re
import time
from typing import Any, Dict, Iterable, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
]

class BaseSpider:
    def __init__(
        self,
        base_url: str,
        *,
        proxy_pool: Optional[Iterable[str]] = None,
        timeout: int = 10,
        delay_range: Tuple[float, float] = (1.0, 3.0),
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.proxy_pool = list(proxy_pool) if proxy_pool else []
        self.timeout = timeout
        self.delay_range = delay_range
        self.session = self._build_session()
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST"]),
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _pick_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxy_pool:
            return None
        proxy = random.choice(self.proxy_pool)
        return {"http": proxy, "https": proxy}

    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[requests.Response]:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        proxy = self._pick_proxy()
        try:
            resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout, proxies=proxy)
            if resp.status_code >= 400:
                self.logger.warning("GET %s returned %s", url, resp.status_code)
                return None
            return resp
        except requests.RequestException as exc:
            self.logger.warning("GET %s failed: %s", url, exc)
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def random_delay(self) -> None:
        time.sleep(random.uniform(*self.delay_range))

    @staticmethod
    def to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        match = re.search(r"[-+]?\d*\.?\d+", str(value).replace(",", ""))
        return float(match.group()) if match else None

    def run(self) -> None:
        raise NotImplementedError("Subclasses should implement run()")
