"""
Data Scraper Module
───────────────────
Async HTTP client with rate-limiting, retries, and ethical scraping.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Global rate-limiting semaphore (max concurrent requests per platform)
_SEMAPHORES: dict[str, asyncio.Semaphore] = {}


def _get_semaphore(platform: str, max_concurrent: int = 5) -> asyncio.Semaphore:
    if platform not in _SEMAPHORES:
        _SEMAPHORES[platform] = asyncio.Semaphore(max_concurrent)
    return _SEMAPHORES[platform]


class DataScraper:
    """Rate-limited, retry-capable async HTTP client."""

    DEFAULT_HEADERS = {
        "User-Agent": "SmartDealer/1.0 (price-comparison; contact@smartdealer.app)",
        "Accept": "application/json",
    }

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=self.DEFAULT_HEADERS,
            follow_redirects=True,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def fetch_json(
        self,
        url: str,
        platform: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict:
        """GET JSON with rate limiting and retries."""
        sem = _get_semaphore(platform)
        async with sem:
            await asyncio.sleep(settings.SCRAPE_DELAY_SECONDS)
            if not self._client:
                await self.start()
            resp = await self._client.get(url, params=params, headers=headers)  # type: ignore[union-attr]
            resp.raise_for_status()
            return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def fetch_html(
        self,
        url: str,
        platform: str,
        headers: dict[str, str] | None = None,
    ) -> str:
        """GET HTML with rate limiting and retries."""
        sem = _get_semaphore(platform)
        async with sem:
            await asyncio.sleep(settings.SCRAPE_DELAY_SECONDS)
            if not self._client:
                await self.start()
            resp = await self._client.get(url, headers=headers)  # type: ignore[union-attr]
            resp.raise_for_status()
            return resp.text

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def post_json(
        self,
        url: str,
        platform: str,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict:
        """POST JSON with rate limiting and retries."""
        sem = _get_semaphore(platform)
        async with sem:
            await asyncio.sleep(settings.SCRAPE_DELAY_SECONDS)
            if not self._client:
                await self.start()
            resp = await self._client.post(url, json=json_body, headers=headers)  # type: ignore[union-attr]
            resp.raise_for_status()
            return resp.json()


# Singleton
scraper = DataScraper()
