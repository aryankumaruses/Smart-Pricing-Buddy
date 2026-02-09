"""
Hotel & Accommodation Agent
────────────────────────────
Searches Booking.com, Expedia, Airbnb, Hotels.com, Vrbo.
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


def _random_hotel_name() -> str:
    adjectives = ["Grand", "Royal", "Sunset", "Ocean View", "Downtown", "Luxe", "Comfort", "Budget"]
    types = ["Hotel", "Inn", "Suites", "Resort", "Lodge", "B&B"]
    return f"{random.choice(adjectives)} {random.choice(types)}"


async def _search_booking(destination: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.15)
    nightly = round(random.uniform(50, 400), 2)
    nights = filters.get("nights", 1)
    tax = round(nightly * nights * 0.12, 2)
    resort_fee = round(random.choice([0, 0, 15, 25, 35]), 2)
    return [
        {
            "platform": Platform.BOOKING,
            "name": f"{_random_hotel_name()} – Booking.com",
            "nightly_rate": nightly,
            "nights": nights,
            "tax": tax,
            "resort_fee": resort_fee,
            "total": round(nightly * nights + tax + resort_fee, 2),
            "rating": round(random.uniform(7.0, 9.8), 1),
            "rating_count": random.randint(100, 5000),
            "cancellation": random.choice(["Free cancellation", "Non-refundable"]),
            "amenities": random.sample(["WiFi", "Pool", "Gym", "Parking", "Breakfast", "Spa"], 3),
            "image": "https://img.placeholder.com/booking.jpg",
            "link": "https://booking.com/hotel/example",
        }
    ]


async def _search_expedia(destination: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.15)
    nightly = round(random.uniform(45, 380), 2)
    nights = filters.get("nights", 1)
    tax = round(nightly * nights * 0.13, 2)
    resort_fee = round(random.choice([0, 0, 20, 30]), 2)
    return [
        {
            "platform": Platform.EXPEDIA,
            "name": f"{_random_hotel_name()} – Expedia",
            "nightly_rate": nightly,
            "nights": nights,
            "tax": tax,
            "resort_fee": resort_fee,
            "total": round(nightly * nights + tax + resort_fee, 2),
            "rating": round(random.uniform(3.0, 5.0), 1),
            "rating_count": random.randint(50, 3000),
            "cancellation": random.choice(["Free cancellation", "Non-refundable"]),
            "amenities": random.sample(["WiFi", "Pool", "Gym", "Parking", "Breakfast", "Spa"], 3),
            "image": "https://img.placeholder.com/expedia.jpg",
            "link": "https://expedia.com/hotel/example",
        }
    ]


async def _search_airbnb(destination: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.15)
    nightly = round(random.uniform(40, 350), 2)
    nights = filters.get("nights", 1)
    cleaning = round(random.uniform(20, 80), 2)
    service = round(nightly * nights * 0.14, 2)
    tax = round(nightly * nights * 0.10, 2)
    return [
        {
            "platform": Platform.AIRBNB,
            "name": f"{_random_hotel_name()} – Airbnb",
            "nightly_rate": nightly,
            "nights": nights,
            "tax": tax,
            "resort_fee": cleaning,
            "service_fee": service,
            "total": round(nightly * nights + cleaning + service + tax, 2),
            "rating": round(random.uniform(4.0, 5.0), 1),
            "rating_count": random.randint(10, 2000),
            "cancellation": random.choice(["Flexible", "Moderate", "Strict"]),
            "amenities": random.sample(["WiFi", "Kitchen", "Washer", "Parking", "Workspace", "Hot tub"], 3),
            "image": "https://img.placeholder.com/airbnb.jpg",
            "link": "https://airbnb.com/rooms/example",
        }
    ]


async def _search_hotels_com(destination: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.12)
    nightly = round(random.uniform(55, 420), 2)
    nights = filters.get("nights", 1)
    tax = round(nightly * nights * 0.12, 2)
    return [
        {
            "platform": Platform.HOTELS_COM,
            "name": f"{_random_hotel_name()} – Hotels.com",
            "nightly_rate": nightly,
            "nights": nights,
            "tax": tax,
            "resort_fee": 0,
            "total": round(nightly * nights + tax, 2),
            "rating": round(random.uniform(6.0, 9.5), 1),
            "rating_count": random.randint(80, 4000),
            "cancellation": random.choice(["Free cancellation", "Non-refundable"]),
            "amenities": random.sample(["WiFi", "Pool", "Gym", "Parking", "Breakfast"], 3),
            "image": "https://img.placeholder.com/hotels.jpg",
            "link": "https://hotels.com/hotel/example",
        }
    ]


async def _search_vrbo(destination: str, filters: dict) -> list[dict]:
    await asyncio.sleep(0.12)
    nightly = round(random.uniform(60, 500), 2)
    nights = filters.get("nights", 1)
    cleaning = round(random.uniform(30, 100), 2)
    tax = round(nightly * nights * 0.11, 2)
    return [
        {
            "platform": Platform.VRBO,
            "name": f"{_random_hotel_name()} – Vrbo",
            "nightly_rate": nightly,
            "nights": nights,
            "tax": tax,
            "resort_fee": cleaning,
            "total": round(nightly * nights + cleaning + tax, 2),
            "rating": round(random.uniform(4.0, 5.0), 1),
            "rating_count": random.randint(10, 1500),
            "cancellation": random.choice(["Full refund", "Partial refund", "No refund"]),
            "amenities": random.sample(["WiFi", "Kitchen", "Pool", "Parking", "Fireplace", "Patio"], 3),
            "image": "https://img.placeholder.com/vrbo.jpg",
            "link": "https://vrbo.com/listing/example",
        }
    ]


PLATFORM_SEARCHERS = {
    Platform.BOOKING: _search_booking,
    Platform.EXPEDIA: _search_expedia,
    Platform.AIRBNB: _search_airbnb,
    Platform.HOTELS_COM: _search_hotels_com,
    Platform.VRBO: _search_vrbo,
}


class HotelAgent(BaseAgent):
    name = "hotel"

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

        budget = filters.get("budget_max")
        if budget:
            results = [r for r in results if r.total_price <= budget]

        return results

    @staticmethod
    def _normalise(raw: dict) -> SearchResultItem:
        nightly = raw["nightly_rate"]
        nights = raw.get("nights", 1)
        tax = raw.get("tax", 0)
        resort = raw.get("resort_fee", 0)
        service = raw.get("service_fee", 0)
        total = raw.get("total", round(nightly * nights + tax + resort + service, 2))

        return SearchResultItem(
            platform=raw["platform"],
            item_name=raw["name"],
            base_price=nightly,
            total_price=total,
            fees_breakdown=PriceBreakdown(
                base_price=round(nightly * nights, 2),
                service_fee=resort + service,
                tax=tax,
                total=total,
            ),
            rating=raw.get("rating"),
            rating_count=raw.get("rating_count"),
            image_url=raw.get("image"),
            deep_link=raw.get("link"),
            extra_data={
                "nightly_rate": nightly,
                "nights": nights,
                "cancellation": raw.get("cancellation"),
                "amenities": raw.get("amenities", []),
            },
        )
