"""
E-Commerce Agent
────────────────
Searches Amazon, eBay, Walmart, Target, Best Buy for products.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.models.enums import Platform
from app.models.schemas import AgentMessage, PriceBreakdown, SearchResultItem

logger = structlog.get_logger()


# ── Simulated platform adapters ──────────────────────────────────────────────


async def _search_amazon(item: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.15)
    price = round(random.uniform(5, 500), 2)
    shipping = round(random.choice([0, 0, 0, 5.99, 9.99]), 2)
    tax = round(price * 0.08, 2)
    return [
        {
            "platform": Platform.AMAZON,
            "name": f"{item} – Amazon",
            "price": price,
            "shipping": shipping,
            "tax": tax,
            "rating": round(random.uniform(3.0, 5.0), 1),
            "rating_count": random.randint(100, 50000),
            "delivery_days": random.choice([1, 2, 3, 5, 7]),
            "image": "https://img.placeholder.com/amazon.jpg",
            "link": "https://amazon.com/dp/example",
            "seller": "Amazon.com",
            "prime": random.choice([True, False]),
        }
    ]


async def _search_ebay(item: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.15)
    price = round(random.uniform(3, 480), 2)
    shipping = round(random.choice([0, 0, 4.99, 7.99, 12.99]), 2)
    tax = round(price * 0.07, 2)
    return [
        {
            "platform": Platform.EBAY,
            "name": f"{item} – eBay",
            "price": price,
            "shipping": shipping,
            "tax": tax,
            "rating": round(random.uniform(3.0, 5.0), 1),
            "rating_count": random.randint(10, 10000),
            "delivery_days": random.choice([3, 5, 7, 10, 14]),
            "image": "https://img.placeholder.com/ebay.jpg",
            "link": "https://ebay.com/itm/example",
            "seller": "top_rated_seller",
        }
    ]


async def _search_walmart(item: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.12)
    price = round(random.uniform(4, 450), 2)
    shipping = round(random.choice([0, 0, 5.99]), 2)
    tax = round(price * 0.08, 2)
    return [
        {
            "platform": Platform.WALMART,
            "name": f"{item} – Walmart",
            "price": price,
            "shipping": shipping,
            "tax": tax,
            "rating": round(random.uniform(3.0, 5.0), 1),
            "rating_count": random.randint(50, 20000),
            "delivery_days": random.choice([2, 3, 5]),
            "image": "https://img.placeholder.com/walmart.jpg",
            "link": "https://walmart.com/ip/example",
            "seller": "Walmart.com",
        }
    ]


async def _search_target(item: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.12)
    price = round(random.uniform(5, 400), 2)
    shipping = round(random.choice([0, 0, 5.99]), 2)
    tax = round(price * 0.075, 2)
    return [
        {
            "platform": Platform.TARGET,
            "name": f"{item} – Target",
            "price": price,
            "shipping": shipping,
            "tax": tax,
            "rating": round(random.uniform(3.5, 5.0), 1),
            "rating_count": random.randint(20, 8000),
            "delivery_days": random.choice([2, 3, 5, 7]),
            "image": "https://img.placeholder.com/target.jpg",
            "link": "https://target.com/p/example",
            "seller": "Target",
        }
    ]


async def _search_bestbuy(item: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.12)
    price = round(random.uniform(10, 2000), 2)
    shipping = round(random.choice([0, 0, 0, 5.99]), 2)
    tax = round(price * 0.08, 2)
    return [
        {
            "platform": Platform.BESTBUY,
            "name": f"{item} – Best Buy",
            "price": price,
            "shipping": shipping,
            "tax": tax,
            "rating": round(random.uniform(3.5, 5.0), 1),
            "rating_count": random.randint(30, 15000),
            "delivery_days": random.choice([1, 2, 3, 5]),
            "image": "https://img.placeholder.com/bestbuy.jpg",
            "link": "https://bestbuy.com/site/example",
            "seller": "Best Buy",
        }
    ]


PLATFORM_SEARCHERS = {
    Platform.AMAZON: _search_amazon,
    Platform.EBAY: _search_ebay,
    Platform.WALMART: _search_walmart,
    Platform.TARGET: _search_target,
    Platform.BESTBUY: _search_bestbuy,
}


class ECommerceAgent(BaseAgent):
    name = "ecommerce"

    async def process(self, message: AgentMessage) -> dict[str, Any]:
        query = message.payload.get("query", "")
        filters = message.payload.get("filters", {})
        items = await self.search(query, filters)
        return {"results": [r.model_dump(mode="json") for r in items]}

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[SearchResultItem]:
        filters = filters or {}
        allowed = filters.get("platforms")

        searchers = {
            p: fn for p, fn in PLATFORM_SEARCHERS.items()
            if allowed is None or p.value in allowed
        }

        raw: list[dict] = []
        tasks = [fn(query, filters) for fn in searchers.values()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for resp in responses:
            if isinstance(resp, list):
                raw.extend(resp)

        results = [self._normalise(r) for r in raw]

        # budget filter
        budget = filters.get("budget_max")
        if budget:
            results = [r for r in results if r.total_price <= budget]

        return results

    @staticmethod
    def _normalise(raw: dict) -> SearchResultItem:
        price = raw["price"]
        shipping = raw.get("shipping", 0)
        tax = raw.get("tax", 0)
        total = round(price + shipping + tax, 2)

        return SearchResultItem(
            platform=raw["platform"],
            item_name=raw["name"],
            base_price=price,
            total_price=total,
            fees_breakdown=PriceBreakdown(
                base_price=price,
                delivery_fee=shipping,
                tax=tax,
                total=total,
            ),
            delivery_time_min=raw.get("delivery_days", 0) * 24 * 60 if raw.get("delivery_days") else None,
            rating=raw.get("rating"),
            rating_count=raw.get("rating_count"),
            image_url=raw.get("image"),
            deep_link=raw.get("link"),
            extra_data={
                "seller": raw.get("seller"),
                "prime": raw.get("prime", False),
                "delivery_days": raw.get("delivery_days"),
            },
        )
