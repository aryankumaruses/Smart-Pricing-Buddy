"""
Ranking Engine
──────────────
Ranks search results using a weighted scoring algorithm.
Default weights: Price 40%, Time 20%, Rating 20%, Fees 10%, User Pref 10%.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.config import get_settings
from app.models.schemas import SearchResultItem

logger = structlog.get_logger()
settings = get_settings()


def _normalise_min_is_best(value: float, min_val: float, max_val: float) -> float:
    """0 = worst (max), 1 = best (min)."""
    if max_val == min_val:
        return 1.0
    return 1.0 - (value - min_val) / (max_val - min_val)


def _normalise_max_is_best(value: float, min_val: float, max_val: float) -> float:
    """0 = worst (min), 1 = best (max)."""
    if max_val == min_val:
        return 1.0
    return (value - min_val) / (max_val - min_val)


def rank_results(
    results: list[SearchResultItem],
    custom_weights: dict[str, float] | None = None,
) -> list[SearchResultItem]:
    """
    Score each result and sort descending by value_score.
    Returns results with `value_score` and `rank` populated.
    """
    if not results:
        return results

    # Merge weights
    w_price = (custom_weights or {}).get("price", settings.WEIGHT_PRICE)
    w_time = (custom_weights or {}).get("time", settings.WEIGHT_TIME)
    w_rating = (custom_weights or {}).get("rating", settings.WEIGHT_RATING)
    w_fees = (custom_weights or {}).get("fees", settings.WEIGHT_FEES)
    w_pref = (custom_weights or {}).get("user_pref", settings.WEIGHT_USER_PREF)

    # Collect ranges for normalisation
    prices = [r.total_price for r in results]
    times = [r.delivery_time_min for r in results if r.delivery_time_min is not None]
    ratings = [r.rating for r in results if r.rating is not None]
    fees = []
    for r in results:
        if r.fees_breakdown:
            fees.append(r.fees_breakdown.delivery_fee + r.fees_breakdown.service_fee)
        else:
            fees.append(0)

    price_min, price_max = min(prices), max(prices)
    time_min, time_max = (min(times), max(times)) if times else (0, 1)
    rating_min, rating_max = (min(ratings), max(ratings)) if ratings else (0, 5)
    fee_min, fee_max = (min(fees), max(fees)) if fees else (0, 1)

    max_price = max(prices) if prices else 1

    for idx, r in enumerate(results):
        # Price score (lower is better)
        s_price = _normalise_min_is_best(r.total_price, price_min, price_max)

        # Time score (lower is better)
        t = r.delivery_time_min if r.delivery_time_min is not None else time_max
        s_time = _normalise_min_is_best(t, time_min, time_max)

        # Rating score (higher is better)
        rt = r.rating if r.rating is not None else rating_min
        s_rating = _normalise_max_is_best(rt, rating_min, rating_max)

        # Fee score (lower is better)
        f = fees[idx] if idx < len(fees) else 0
        s_fees = _normalise_min_is_best(f, fee_min, fee_max)

        # User pref placeholder (will be based on profile matching)
        s_pref = 0.5

        score = (
            w_price * s_price
            + w_time * s_time
            + w_rating * s_rating
            + w_fees * s_fees
            + w_pref * s_pref
        )

        r.value_score = round(score, 4)

        # Calculate savings vs most expensive option
        r.savings_vs_max = round(max_price - r.total_price, 2)

    # Sort descending by value_score
    results.sort(key=lambda r: r.value_score or 0, reverse=True)

    for rank, r in enumerate(results, start=1):
        r.rank = rank

    logger.info("results.ranked", count=len(results), top_score=results[0].value_score if results else None)
    return results
