"""
NLP Query Parser
────────────────
Parses natural-language queries into structured intents.
Uses rule-based fallbacks + optional OpenAI for complex queries.
"""

from __future__ import annotations

import re
from typing import Any

import structlog

from app.models.enums import SearchCategory
from app.models.schemas import ParsedIntent

logger = structlog.get_logger()

# ── Keyword → category mapping ──────────────────────────────────────────────

_FOOD_KEYWORDS = {
    "pizza", "burger", "sushi", "tacos", "food", "delivery", "restaurant",
    "eat", "meal", "lunch", "dinner", "breakfast", "wings", "chinese",
    "indian", "thai", "mexican", "italian", "noodles", "rice", "salad",
    "sandwich", "soup", "steak", "chicken", "vegan", "vegetarian",
    "dessert", "coffee", "bubble tea", "fries", "pasta", "ramen",
}

_PRODUCT_KEYWORDS = {
    "buy", "product", "price", "laptop", "phone", "headphones", "tv",
    "camera", "tablet", "monitor", "keyboard", "mouse", "watch",
    "shoes", "clothing", "book", "electronics", "appliance", "gadget",
    "deal", "purchase", "shop", "compare", "cheapest",
}

_RIDE_KEYWORDS = {
    "ride", "uber", "lyft", "taxi", "cab", "drive", "airport",
    "transport", "pickup", "drop", "commute", "carpool",
}

_HOTEL_KEYWORDS = {
    "hotel", "motel", "resort", "airbnb", "vrbo", "stay", "accommodation",
    "booking", "lodge", "hostel", "room", "suite", "night", "check-in",
    "vacation", "rental", "bed and breakfast",
}

# ── Budget extraction ────────────────────────────────────────────────────────

_BUDGET_PATTERNS = [
    r"under\s+\$?(\d+(?:\.\d+)?)",
    r"below\s+\$?(\d+(?:\.\d+)?)",
    r"less\s+than\s+\$?(\d+(?:\.\d+)?)",
    r"max(?:imum)?\s+\$?(\d+(?:\.\d+)?)",
    r"budget\s+(?:of\s+)?\$?(\d+(?:\.\d+)?)",
    r"\$(\d+(?:\.\d+)?)\s*(?:max|limit|budget)",
    r"up\s+to\s+\$?(\d+(?:\.\d+)?)",
]

_TIME_PATTERNS = [
    r"within\s+(\d+)\s*(?:min(?:ute)?s?)",
    r"in\s+(\d+)\s*(?:min(?:ute)?s?)",
    r"under\s+(\d+)\s*(?:min(?:ute)?s?)",
]

_LOCATION_PATTERNS = [
    r"(?:in|near|around|to|from|at)\s+([A-Z][a-zA-Z\s]+?)(?:\s+(?:for|under|within|below|max|this|next)|$)",
    r"(?:in|near|around|to|from|at)\s+the\s+([a-zA-Z\s]+?)(?:\s+(?:for|under|within|below|max|this|next)|$)",
]


def _detect_category(query_lower: str) -> SearchCategory:
    scores = {
        SearchCategory.FOOD: sum(1 for kw in _FOOD_KEYWORDS if kw in query_lower),
        SearchCategory.PRODUCT: sum(1 for kw in _PRODUCT_KEYWORDS if kw in query_lower),
        SearchCategory.RIDE: sum(1 for kw in _RIDE_KEYWORDS if kw in query_lower),
        SearchCategory.HOTEL: sum(1 for kw in _HOTEL_KEYWORDS if kw in query_lower),
    }
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best] == 0:
        return SearchCategory.PRODUCT  # default fallback
    return best


def _extract_budget(query: str) -> float | None:
    for pat in _BUDGET_PATTERNS:
        m = re.search(pat, query, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None


def _extract_time(query: str) -> str | None:
    for pat in _TIME_PATTERNS:
        m = re.search(pat, query, re.IGNORECASE)
        if m:
            return f"{m.group(1)} minutes"
    return None


def _extract_location(query: str) -> str | None:
    for pat in _LOCATION_PATTERNS:
        m = re.search(pat, query)
        if m:
            return m.group(1).strip()
    return None


def _extract_item(query: str, category: SearchCategory) -> str:
    """Extract the primary search item from the query."""
    # Remove common preamble words
    cleaned = re.sub(
        r"^(?:find\s+(?:me\s+)?(?:the\s+)?|search\s+(?:for\s+)?|compare\s+|get\s+(?:me\s+)?|"
        r"show\s+(?:me\s+)?|i\s+(?:want|need)\s+(?:a\s+)?|what(?:'s| is)\s+the\s+)",
        "",
        query,
        flags=re.IGNORECASE,
    ).strip()
    # Remove budget/time/location suffixes
    cleaned = re.sub(r"\s+(?:under|below|less than|within|in|near|around|for|max).*$", "", cleaned, flags=re.IGNORECASE)
    # Remove superlatives
    cleaned = re.sub(r"^(?:cheapest|best|fastest|nearest|lowest|most affordable)\s+", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip() or query


async def parse_user_query(query: str) -> ParsedIntent:
    """
    Parse a natural-language query into a structured intent.
    Uses rule-based approach; can be upgraded to use LLM.
    """
    q_lower = query.lower().strip()

    category = _detect_category(q_lower)
    item = _extract_item(query, category)
    budget = _extract_budget(query)
    time_constraint = _extract_time(query)
    location = _extract_location(query)

    filters: dict[str, Any] = {}
    if budget:
        filters["budget_max"] = budget
    if time_constraint:
        filters["time_constraint"] = time_constraint

    intent = ParsedIntent(
        category=category,
        item=item,
        filters=filters,
        location=location,
        time_constraint=time_constraint,
        budget=budget,
    )

    logger.info(
        "query.parsed",
        query=query,
        category=category.value,
        item=item,
        budget=budget,
        location=location,
    )

    return intent
