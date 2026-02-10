"""
Food Delivery Agent
───────────────────
Searches Uber Eats, DoorDash, Grubhub, Postmates for the best food deals.

Integrates with LangChain for tool-based function calling.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent
from app.models.enums import Platform
from app.models.schemas import AgentMessage, PriceBreakdown, SearchResultItem

logger = structlog.get_logger()


# ── Tool Input Schema ────────────────────────────────────────────────────────

class FoodSearchInput(BaseModel):
    """Input schema for food delivery search."""
    query: str = Field(..., description="Food item or restaurant to search for")
    location: str | None = Field(None, description="Delivery location/address")
    platforms: list[str] | None = Field(None, description="Specific platforms to search (uber_eats, doordash, grubhub, postmates)")
    budget_max: float | None = Field(None, description="Maximum budget for the order")

# ── Simulated platform adapters (swap for real API calls) ────────────────────


async def _search_ubereats(item: str, location: str | None, filters: dict) -> list[dict]:
    """Simulates Uber Eats API call."""
    await asyncio.sleep(0.1)  # simulate network
    base = round(random.uniform(8, 25), 2)
    delivery = round(random.uniform(0, 5.99), 2)
    service = round(base * 0.15, 2)
    return [
        {
            "platform": Platform.UBER_EATS,
            "name": f"{item} – UberEats Restaurant",
            "base_price": base,
            "delivery_fee": delivery,
            "service_fee": service,
            "tax": round((base + delivery + service) * 0.08, 2),
            "delivery_time": random.randint(15, 45),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "rating_count": random.randint(50, 2000),
            "image": "https://img.placeholder.com/ubereats.jpg",
            "link": "https://ubereats.com/store/example",
        }
    ]


async def _search_doordash(item: str, location: str | None, filters: dict) -> list[dict]:
    await asyncio.sleep(0.1)
    base = round(random.uniform(7, 24), 2)
    delivery = round(random.uniform(0, 6.99), 2)
    service = round(base * 0.12, 2)
    return [
        {
            "platform": Platform.DOORDASH,
            "name": f"{item} – DoorDash Place",
            "base_price": base,
            "delivery_fee": delivery,
            "service_fee": service,
            "tax": round((base + delivery + service) * 0.08, 2),
            "delivery_time": random.randint(20, 50),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "rating_count": random.randint(50, 3000),
            "image": "https://img.placeholder.com/doordash.jpg",
            "link": "https://doordash.com/store/example",
        }
    ]


async def _search_grubhub(item: str, location: str | None, filters: dict) -> list[dict]:
    await asyncio.sleep(0.1)
    base = round(random.uniform(7.5, 23), 2)
    delivery = round(random.uniform(0, 4.99), 2)
    service = round(base * 0.10, 2)
    return [
        {
            "platform": Platform.GRUBHUB,
            "name": f"{item} – Grubhub Kitchen",
            "base_price": base,
            "delivery_fee": delivery,
            "service_fee": service,
            "tax": round((base + delivery + service) * 0.07, 2),
            "delivery_time": random.randint(20, 55),
            "rating": round(random.uniform(3.2, 4.9), 1),
            "rating_count": random.randint(30, 1500),
            "image": "https://img.placeholder.com/grubhub.jpg",
            "link": "https://grubhub.com/restaurant/example",
        }
    ]


async def _search_postmates(item: str, location: str | None, filters: dict) -> list[dict]:
    await asyncio.sleep(0.1)
    base = round(random.uniform(8.5, 26), 2)
    delivery = round(random.uniform(0, 7.99), 2)
    service = round(base * 0.18, 2)
    return [
        {
            "platform": Platform.POSTMATES,
            "name": f"{item} – Postmates Spot",
            "base_price": base,
            "delivery_fee": delivery,
            "service_fee": service,
            "tax": round((base + delivery + service) * 0.09, 2),
            "delivery_time": random.randint(18, 40),
            "rating": round(random.uniform(3.0, 4.8), 1),
            "rating_count": random.randint(20, 1000),
            "image": "https://img.placeholder.com/postmates.jpg",
            "link": "https://postmates.com/store/example",
        }
    ]


# ── Agent ────────────────────────────────────────────────────────────────────


PLATFORM_SEARCHERS = {
    Platform.UBER_EATS: _search_ubereats,
    Platform.DOORDASH: _search_doordash,
    Platform.GRUBHUB: _search_grubhub,
    Platform.POSTMATES: _search_postmates,
}


class FoodDeliveryAgent(BaseAgent):
    """Agent for searching food delivery platforms."""
    
    name = "food_search"
    description = "Search for food delivery options across Uber Eats, DoorDash, Grubhub, and Postmates. Use this when the user wants to order food or compare food delivery prices."
    tool_input_schema = FoodSearchInput

    async def execute(self, message: AgentMessage) -> list[SearchResultItem]:
        """Execute search from AgentMessage."""
        query = message.payload.get("query", "")
        filters = message.payload.get("filters", {})
        return await self.search(query, filters)

    async def process(self, message: AgentMessage) -> dict[str, Any]:
        query = message.payload.get("query", "")
        filters = message.payload.get("filters", {})
        items = await self.search(query, filters)
        return {"results": [r.model_dump(mode="json") for r in items]}

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[SearchResultItem]:
        filters = filters or {}
        location = filters.get("location")
        allowed = filters.get("platforms")

        searchers = {
            p: fn for p, fn in PLATFORM_SEARCHERS.items()
            if allowed is None or p.value in allowed
        }

        raw_results: list[dict] = []
        tasks = [fn(query, location, filters) for fn in searchers.values()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for resp in responses:
            if isinstance(resp, list):
                raw_results.extend(resp)

        return [self._normalise(r, filters) for r in raw_results]

    # ── normalisation ────────────────────────────────────────────────

    @staticmethod
    def _normalise(raw: dict, filters: dict) -> SearchResultItem:
        base = raw["base_price"]
        delivery = raw.get("delivery_fee", 0)
        service = raw.get("service_fee", 0)
        tax = raw.get("tax", 0)
        total = round(base + delivery + service + tax, 2)

        return SearchResultItem(
            platform=raw["platform"],
            item_name=raw["name"],
            base_price=base,
            total_price=total,
            fees_breakdown=PriceBreakdown(
                base_price=base,
                delivery_fee=delivery,
                service_fee=service,
                tax=tax,
                total=total,
            ),
            delivery_time_min=raw.get("delivery_time"),
            rating=raw.get("rating"),
            rating_count=raw.get("rating_count"),
            image_url=raw.get("image"),
            deep_link=raw.get("link"),
        )
