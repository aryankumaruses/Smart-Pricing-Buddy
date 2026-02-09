"""
Orchestrator Agent
──────────────────
Central coordinator that:
  1. Parses user queries via NLP
  2. Identifies the search category
  3. Fans out to specialised agents in parallel
  4. Collects, ranks, and returns results
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.agents.food_agent import FoodDeliveryAgent
from app.agents.ecommerce_agent import ECommerceAgent
from app.agents.ride_agent import RideSharingAgent
from app.agents.hotel_agent import HotelAgent
from app.agents.deal_agent import DealFinderAgent
from app.agents.user_profile_agent import UserProfileAgent
from app.models.enums import SearchCategory, SearchStatus
from app.models.schemas import (
    AgentMessage,
    ParsedIntent,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.services.nlp_parser import parse_user_query
from app.services.ranking import rank_results

logger = structlog.get_logger()


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    def __init__(self) -> None:
        self.food_agent = FoodDeliveryAgent()
        self.ecommerce_agent = ECommerceAgent()
        self.ride_agent = RideSharingAgent()
        self.hotel_agent = HotelAgent()
        self.deal_agent = DealFinderAgent()
        self.user_profile_agent = UserProfileAgent()

        self._category_agent_map: dict[SearchCategory, BaseAgent] = {
            SearchCategory.FOOD: self.food_agent,
            SearchCategory.PRODUCT: self.ecommerce_agent,
            SearchCategory.RIDE: self.ride_agent,
            SearchCategory.HOTEL: self.hotel_agent,
        }

    # ── BaseAgent contract ───────────────────────────────────────────

    async def process(self, message: AgentMessage) -> dict[str, Any]:
        request = SearchRequest(**message.payload)
        response = await self.execute_search(request, user_id=message.context.get("user_id"))
        return response.model_dump(mode="json")

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[SearchResultItem]:
        request = SearchRequest(query=query, filters=filters)
        response = await self.execute_search(request)
        return response.results

    # ── Main orchestration loop ──────────────────────────────────────

    async def execute_search(
        self,
        request: SearchRequest,
        user_id: str | None = None,
    ) -> SearchResponse:
        start = time.monotonic()
        correlation_id = uuid.uuid4()
        log = logger.bind(cid=str(correlation_id))

        # 1. Parse intent
        intent: ParsedIntent = await parse_user_query(request.query)
        category = request.category or intent.category
        log.info("intent.parsed", category=category.value, item=intent.item)

        # 2. Merge user profile preferences
        user_prefs: dict[str, Any] = {}
        if user_id:
            user_prefs = await self.user_profile_agent.get_preferences(user_id)

        # 3. Build merged filters
        merged_filters = {**(intent.filters or {}), **(request.filters or {})}
        if request.budget_max:
            merged_filters["budget_max"] = request.budget_max
        if request.location or intent.location:
            merged_filters["location"] = request.location or intent.location
        if request.platforms:
            merged_filters["platforms"] = [p.value for p in request.platforms]

        # 4. Fan out to category agents + deal agent in parallel
        agent = self._category_agent_map.get(category)
        if not agent:
            return SearchResponse(
                session_id=correlation_id,
                query=request.query,
                category=category,
                status=SearchStatus.FAILED,
                result_count=0,
                results=[],
                search_time_ms=0,
            )

        search_task = agent.search(intent.item, merged_filters)
        deals_task = self.deal_agent.find_deals(category, merged_filters)

        results, deals = await asyncio.gather(search_task, deals_task, return_exceptions=True)

        if isinstance(results, Exception):
            log.error("agent.search.failed", error=str(results))
            results = []
        if isinstance(deals, Exception):
            log.error("deals.search.failed", error=str(deals))
            deals = []

        # 5. Apply deals to results
        results = self.deal_agent.apply_deals(results, deals)

        # 6. Rank results
        weights = user_prefs.get("ranking_weights") if user_prefs else None
        ranked = rank_results(results, weights)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.info("search.complete", count=len(ranked), ms=elapsed_ms)

        return SearchResponse(
            session_id=correlation_id,
            query=request.query,
            category=category,
            status=SearchStatus.COMPLETED,
            result_count=len(ranked),
            results=ranked[:10],
            deals_found=deals,
            search_time_ms=elapsed_ms,
        )
