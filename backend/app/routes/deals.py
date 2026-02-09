"""
Deal routes – browse and search active deals.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.agents.deal_agent import DealFinderAgent
from app.models.enums import SearchCategory
from app.models.schemas import DealRead

router = APIRouter(prefix="/deals", tags=["Deals"])

_deal_agent = DealFinderAgent()


@router.get("/", response_model=list[DealRead])
async def list_deals(
    category: SearchCategory = Query(..., description="Deal category"),
) -> list[DealRead]:
    """Get all active deals for a category."""
    return await _deal_agent.find_deals(category, {})
