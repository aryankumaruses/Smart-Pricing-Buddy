"""
Search routes – the main user-facing endpoint.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.agents.orchestrator import OrchestratorAgent
from app.models.enums import Platform, SearchCategory
from app.models.schemas import SearchRequest, SearchResponse

router = APIRouter(prefix="/search", tags=["Search"])

# Singleton orchestrator
_orchestrator = OrchestratorAgent()


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Execute a multi-platform search.

    Accepts natural-language queries like:
    - "Find me the cheapest pizza delivery within 30 minutes"
    - "Best hotel deals in Miami for next weekend under $150/night"
    - "Compare Uber vs Lyft to the airport right now"
    """
    return await _orchestrator.execute_search(request)


@router.get("/quick", response_model=SearchResponse)
async def quick_search(
    q: str = Query(..., min_length=3, description="Search query"),
    category: SearchCategory | None = None,
    budget: float | None = Query(None, gt=0, description="Max budget"),
    location: str | None = None,
    platforms: list[Platform] | None = Query(None),
) -> SearchResponse:
    """Quick search via query parameters."""
    request = SearchRequest(
        query=q,
        category=category,
        budget_max=budget,
        location=location,
        platforms=platforms,
    )
    return await _orchestrator.execute_search(request)
