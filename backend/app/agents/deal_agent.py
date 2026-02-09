"""
Deal Finder Agent
─────────────────
Monitors promo codes, cashback offers, credit-card rewards, seasonal sales,
and applies them to search results.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any
import uuid

import structlog

from app.agents.base_agent import BaseAgent
from app.models.enums import DealType, Platform, SearchCategory
from app.models.schemas import AgentMessage, DealRead, SearchResultItem

logger = structlog.get_logger()

# ── Simulated deals database ────────────────────────────────────────────────

_SAMPLE_DEALS: list[dict] = [
    {
        "platform": Platform.UBER_EATS,
        "deal_type": DealType.PROMO_CODE,
        "code": "EAT20OFF",
        "description": "20% off your first order",
        "discount_percent": 20,
        "max_discount": 10.0,
        "valid_days": 30,
    },
    {
        "platform": Platform.DOORDASH,
        "deal_type": DealType.PROMO_CODE,
        "code": "DASH5",
        "description": "$5 off orders over $25",
        "discount_amount": 5.0,
        "min_order": 25.0,
        "valid_days": 14,
    },
    {
        "platform": Platform.AMAZON,
        "deal_type": DealType.CASHBACK,
        "code": None,
        "description": "5% cashback with Amazon Prime credit card",
        "discount_percent": 5,
        "valid_days": 365,
    },
    {
        "platform": Platform.UBER,
        "deal_type": DealType.PROMO_CODE,
        "code": "RIDE10",
        "description": "$10 off next ride",
        "discount_amount": 10.0,
        "valid_days": 7,
    },
    {
        "platform": Platform.BOOKING,
        "deal_type": DealType.SEASONAL,
        "code": None,
        "description": "Genius member 15% discount",
        "discount_percent": 15,
        "valid_days": 60,
    },
    {
        "platform": Platform.LYFT,
        "deal_type": DealType.PROMO_CODE,
        "code": "LYFT15",
        "description": "15% off next 3 rides",
        "discount_percent": 15,
        "max_discount": 8.0,
        "valid_days": 14,
    },
    {
        "platform": Platform.WALMART,
        "deal_type": DealType.FLASH_SALE,
        "code": None,
        "description": "Flash sale – up to 30% off electronics",
        "discount_percent": 30,
        "valid_days": 2,
    },
    {
        "platform": Platform.AIRBNB,
        "deal_type": DealType.SEASONAL,
        "code": None,
        "description": "Weekly stay discount – 10% off 7+ nights",
        "discount_percent": 10,
        "valid_days": 90,
    },
]

# Map platforms to categories for quick lookup
_PLATFORM_CATEGORY: dict[Platform, SearchCategory] = {
    Platform.UBER_EATS: SearchCategory.FOOD,
    Platform.DOORDASH: SearchCategory.FOOD,
    Platform.GRUBHUB: SearchCategory.FOOD,
    Platform.POSTMATES: SearchCategory.FOOD,
    Platform.AMAZON: SearchCategory.PRODUCT,
    Platform.EBAY: SearchCategory.PRODUCT,
    Platform.WALMART: SearchCategory.PRODUCT,
    Platform.TARGET: SearchCategory.PRODUCT,
    Platform.BESTBUY: SearchCategory.PRODUCT,
    Platform.UBER: SearchCategory.RIDE,
    Platform.LYFT: SearchCategory.RIDE,
    Platform.TAXI: SearchCategory.RIDE,
    Platform.BOOKING: SearchCategory.HOTEL,
    Platform.EXPEDIA: SearchCategory.HOTEL,
    Platform.AIRBNB: SearchCategory.HOTEL,
    Platform.HOTELS_COM: SearchCategory.HOTEL,
    Platform.VRBO: SearchCategory.HOTEL,
}


class DealFinderAgent(BaseAgent):
    name = "deal_finder"

    async def process(self, message: AgentMessage) -> dict[str, Any]:
        category = SearchCategory(message.payload.get("category", "food"))
        filters = message.payload.get("filters", {})
        deals = await self.find_deals(category, filters)
        return {"deals": [d.model_dump(mode="json") for d in deals]}

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[SearchResultItem]:
        # Deals don't return SearchResultItems directly
        return []

    async def find_deals(self, category: SearchCategory, filters: dict) -> list[DealRead]:
        """Find active deals relevant to the search category."""
        now = datetime.utcnow()
        relevant: list[DealRead] = []

        for d in _SAMPLE_DEALS:
            cat = _PLATFORM_CATEGORY.get(d["platform"])
            if cat != category:
                continue
            valid_from = now - timedelta(days=1)
            valid_until = now + timedelta(days=d.get("valid_days", 30))
            relevant.append(
                DealRead(
                    id=uuid.uuid4(),
                    platform=d["platform"],
                    deal_type=d["deal_type"],
                    code=d.get("code"),
                    description=d["description"],
                    discount_amount=d.get("discount_amount"),
                    discount_percent=d.get("discount_percent"),
                    min_order=d.get("min_order"),
                    max_discount=d.get("max_discount"),
                    valid_from=valid_from,
                    valid_until=valid_until,
                    is_active=True,
                )
            )

        return relevant

    @staticmethod
    def apply_deals(results: list[SearchResultItem], deals: list[DealRead]) -> list[SearchResultItem]:
        """Apply matching deals to results and annotate savings."""
        deal_map: dict[Platform, list[DealRead]] = {}
        for deal in deals:
            deal_map.setdefault(deal.platform, []).append(deal)

        for result in results:
            platform_deals = deal_map.get(result.platform, [])
            for deal in platform_deals:
                if deal.min_order and result.total_price < deal.min_order:
                    continue
                discount = 0.0
                if deal.discount_amount:
                    discount = deal.discount_amount
                elif deal.discount_percent:
                    discount = result.total_price * (deal.discount_percent / 100)
                if deal.max_discount:
                    discount = min(discount, deal.max_discount)

                discount = round(discount, 2)
                if discount > 0:
                    result.total_price = round(result.total_price - discount, 2)
                    label = f"{deal.description}"
                    if deal.code:
                        label += f" (code: {deal.code})"
                    result.deals_applied.append(label)
                    if result.fees_breakdown:
                        result.fees_breakdown.discount += discount
                        result.fees_breakdown.total = result.total_price

        return results
