"""
Ride-Sharing Agent
──────────────────
Compares Uber, Lyft, and local taxi services for the best ride prices.
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


async def _search_uber(origin: str, destination: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.1)
    surge = random.uniform(1.0, 2.5)
    results = []
    for vehicle, base_mult in [("UberX", 1.0), ("Uber Comfort", 1.3), ("Uber XL", 1.5), ("Uber Black", 2.0)]:
        base = round(random.uniform(8, 30) * base_mult * surge, 2)
        booking_fee = 2.50
        tax = round(base * 0.06, 2)
        results.append({
            "platform": Platform.UBER,
            "name": vehicle,
            "base_fare": base,
            "booking_fee": booking_fee,
            "surge_multiplier": round(surge, 2),
            "tax": tax,
            "eta_min": random.randint(2, 15),
            "trip_time_min": random.randint(10, 45),
            "rating": round(random.uniform(4.5, 5.0), 2),
            "link": "https://uber.com/ride",
        })
    return results


async def _search_lyft(origin: str, destination: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.1)
    surge = random.uniform(1.0, 2.0)
    results = []
    for vehicle, base_mult in [("Lyft", 1.0), ("Lyft XL", 1.4), ("Lux", 1.8), ("Lux Black", 2.2)]:
        base = round(random.uniform(7, 28) * base_mult * surge, 2)
        service_fee = 2.00
        tax = round(base * 0.06, 2)
        results.append({
            "platform": Platform.LYFT,
            "name": vehicle,
            "base_fare": base,
            "booking_fee": service_fee,
            "surge_multiplier": round(surge, 2),
            "tax": tax,
            "eta_min": random.randint(2, 15),
            "trip_time_min": random.randint(10, 45),
            "rating": round(random.uniform(4.5, 5.0), 2),
            "link": "https://lyft.com/ride",
        })
    return results


async def _search_taxi(origin: str, destination: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.1)
    base = round(random.uniform(15, 50), 2)
    tax = round(base * 0.05, 2)
    return [
        {
            "platform": Platform.TAXI,
            "name": "Standard Taxi",
            "base_fare": base,
            "booking_fee": 0,
            "surge_multiplier": 1.0,
            "tax": tax,
            "eta_min": random.randint(5, 20),
            "trip_time_min": random.randint(10, 45),
            "rating": round(random.uniform(3.5, 4.5), 1),
            "link": None,
        }
    ]


PLATFORM_SEARCHERS = {
    Platform.UBER: _search_uber,
    Platform.LYFT: _search_lyft,
    Platform.TAXI: _search_taxi,
}


class RideSharingAgent(BaseAgent):
    name = "ride_sharing"

    async def process(self, message: AgentMessage) -> dict[str, Any]:
        query = message.payload.get("query", "")
        filters = message.payload.get("filters", {})
        items = await self.search(query, filters)
        return {"results": [r.model_dump(mode="json") for r in items]}

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[SearchResultItem]:
        filters = filters or {}
        origin = filters.get("origin", filters.get("location", "current"))
        destination = filters.get("destination", query)
        allowed = filters.get("platforms")

        searchers = {
            p: fn for p, fn in PLATFORM_SEARCHERS.items()
            if allowed is None or p.value in allowed
        }

        raw: list[dict] = []
        tasks = [fn(origin, destination, filters) for fn in searchers.values()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for resp in responses:
            if isinstance(resp, list):
                raw.extend(resp)

        return [self._normalise(r) for r in raw]

    @staticmethod
    def _normalise(raw: dict) -> SearchResultItem:
        base = raw["base_fare"]
        booking = raw.get("booking_fee", 0)
        tax = raw.get("tax", 0)
        total = round(base + booking + tax, 2)

        return SearchResultItem(
            platform=raw["platform"],
            item_name=raw["name"],
            base_price=base,
            total_price=total,
            fees_breakdown=PriceBreakdown(
                base_price=base,
                service_fee=booking,
                tax=tax,
                total=total,
            ),
            delivery_time_min=raw.get("eta_min"),
            rating=raw.get("rating"),
            deep_link=raw.get("link"),
            extra_data={
                "surge_multiplier": raw.get("surge_multiplier"),
                "trip_time_min": raw.get("trip_time_min"),
                "eta_min": raw.get("eta_min"),
            },
        )
