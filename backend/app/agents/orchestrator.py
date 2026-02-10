"""
LangGraph Orchestrator Agent
────────────────────────────
Central coordinator using LangGraph StateGraph that:
  1. Parses user queries via NLP
  2. Uses LLM reasoning to identify intent and select agents
  3. Fans out to specialized agents in parallel
  4. Collects, ranks, and returns results

Implements a supervisor pattern with LangGraph for state management.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from typing import Any, Literal

import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.agents.base_agent import BaseAgent
from app.agents.deal_agent import DealFinderAgent
from app.agents.ecommerce_agent import ECommerceAgent
from app.agents.food_agent import FoodDeliveryAgent
from app.agents.hotel_agent import HotelAgent
from app.agents.ride_agent import RideSharingAgent
from app.agents.state import AgentState, create_initial_state
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


# ── System Prompt for LLM Reasoning ──────────────────────────────────────────

SUPERVISOR_SYSTEM_PROMPT = """You are a smart shopping assistant that helps users find the best deals across multiple platforms.

Your job is to:
1. Understand what the user is looking for
2. Determine the correct category (food, product, ride, or hotel)
3. Use the appropriate search tools to find options
4. Apply any available deals/discounts
5. Return the best results ranked by value

Available tools:
- food_search: Search for food delivery (Uber Eats, DoorDash, Grubhub, Postmates)
- ecommerce_search: Search for products (Amazon, eBay, Walmart, Target, Best Buy)
- ride_search: Search for rides (Uber, Lyft, taxi services)
- hotel_search: Search for accommodations (Booking.com, Expedia, Airbnb, Hotels.com, Vrbo)
- deal_search: Find promo codes and discounts

When the user asks for something, analyze their request and use the most appropriate tool(s).
Always try to find deals that can be applied to reduce the total cost.

Be concise in your reasoning and focus on finding the best value for the user."""


class OrchestratorAgent(BaseAgent):
    """LangGraph-based orchestrator using supervisor pattern with LLM reasoning."""
    
    name = "orchestrator"
    description = "Coordinates all search agents and orchestrates the search workflow"

    def __init__(self) -> None:
        super().__init__()
        
        # Initialize specialized agents
        self.food_agent = FoodDeliveryAgent()
        self.ecommerce_agent = ECommerceAgent()
        self.ride_agent = RideSharingAgent()
        self.hotel_agent = HotelAgent()
        self.deal_agent = DealFinderAgent()
        self.user_profile_agent = UserProfileAgent()

        # Category to agent mapping
        self._category_agent_map: dict[SearchCategory, BaseAgent] = {
            SearchCategory.FOOD: self.food_agent,
            SearchCategory.PRODUCT: self.ecommerce_agent,
            SearchCategory.RIDE: self.ride_agent,
            SearchCategory.HOTEL: self.hotel_agent,
        }

        # Initialize LLM (uses OPENAI_API_KEY from environment)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )

        # Build the LangGraph workflow
        self.graph = self._build_graph()

    def _get_tools(self) -> list[BaseTool]:
        """Get all agent tools for LLM function calling."""
        return [
            self.food_agent.as_tool(),
            self.ecommerce_agent.as_tool(),
            self.ride_agent.as_tool(),
            self.hotel_agent.as_tool(),
            self.deal_agent.as_tool(),
        ]

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for agent orchestration."""
        
        # Create the graph with our state schema
        workflow = StateGraph(AgentState)

        # ── Define nodes ─────────────────────────────────────────────
        
        async def parse_intent_node(state: AgentState) -> dict:
            """Parse user query to extract intent."""
            intent = await parse_user_query(state["query"])
            return {
                "intent": intent,
                "category": intent.category,
                "status": SearchStatus.PROCESSING,
            }

        async def get_user_preferences_node(state: AgentState) -> dict:
            """Fetch user preferences if user_id is provided."""
            user_id = state.get("user_id")
            if user_id:
                prefs = await self.user_profile_agent.get_preferences(user_id)
                return {"user_preferences": prefs}
            return {"user_preferences": {}}

        async def search_node(state: AgentState) -> dict:
            """Execute search using the appropriate agent."""
            category = state["category"]
            intent = state["intent"]
            
            if not category or not intent:
                return {"errors": ["Failed to parse intent"]}

            agent = self._category_agent_map.get(category)
            if not agent:
                return {"errors": [f"Unknown category: {category}"]}

            # Build merged filters
            merged_filters = {
                **(intent.filters or {}),
                **(state.get("filters") or {}),
            }
            if state.get("budget_max"):
                merged_filters["budget_max"] = state["budget_max"]
            if state.get("location") or intent.location:
                merged_filters["location"] = state.get("location") or intent.location
            if state.get("platforms"):
                merged_filters["platforms"] = state["platforms"]

            try:
                results = await agent.search(intent.item, merged_filters)
                return {"results": results}
            except Exception as e:
                return {"errors": [f"Search failed: {str(e)}"]}

        async def find_deals_node(state: AgentState) -> dict:
            """Find applicable deals for the search category."""
            category = state.get("category")
            if not category:
                return {"deals": []}
            
            try:
                deals = await self.deal_agent.find_deals(category, state.get("filters", {}))
                return {"deals": deals}
            except Exception as e:
                return {"errors": [f"Deal search failed: {str(e)}"]}

        async def apply_deals_and_rank_node(state: AgentState) -> dict:
            """Apply deals to results and rank them."""
            results = state.get("results", [])
            deals = state.get("deals", [])
            user_prefs = state.get("user_preferences", {})

            # Apply deals
            if deals:
                results = self.deal_agent.apply_deals(results, deals)

            # Rank results
            weights = user_prefs.get("ranking_weights") if user_prefs else None
            ranked = rank_results(results, weights)

            return {
                "ranked_results": ranked[:10],
                "status": SearchStatus.COMPLETED,
            }

        # ── Add nodes to graph ───────────────────────────────────────
        workflow.add_node("parse_intent", parse_intent_node)
        workflow.add_node("get_preferences", get_user_preferences_node)
        workflow.add_node("search", search_node)
        workflow.add_node("find_deals", find_deals_node)
        workflow.add_node("apply_deals_and_rank", apply_deals_and_rank_node)

        # ── Define edges (workflow) ──────────────────────────────────
        workflow.set_entry_point("parse_intent")
        
        # After parsing intent, get preferences and search in parallel would be ideal
        # but for simplicity, we'll do sequential for now
        workflow.add_edge("parse_intent", "get_preferences")
        workflow.add_edge("get_preferences", "search")
        workflow.add_edge("search", "find_deals")
        workflow.add_edge("find_deals", "apply_deals_and_rank")
        workflow.add_edge("apply_deals_and_rank", END)

        return workflow.compile()

    # ── BaseAgent contract ───────────────────────────────────────────

    async def execute(self, message: AgentMessage) -> list[SearchResultItem]:
        """Execute search from AgentMessage."""
        request = SearchRequest(**message.payload)
        response = await self.execute_search(request, user_id=message.context.get("user_id"))
        return response.results

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[SearchResultItem]:
        """Execute a search using the LangGraph workflow."""
        request = SearchRequest(query=query, filters=filters)
        response = await self.execute_search(request)
        return response.results

    # ── Main orchestration using LangGraph ───────────────────────────

    async def execute_search(
        self,
        request: SearchRequest,
        user_id: str | None = None,
    ) -> SearchResponse:
        """Execute search using the LangGraph workflow."""
        start = time.monotonic()
        correlation_id = uuid.uuid4()
        log = logger.bind(cid=str(correlation_id))

        log.info("orchestrator.start", query=request.query)

        # Create initial state
        initial_state = create_initial_state(
            query=request.query,
            user_id=user_id,
            filters=request.filters,
            location=request.location,
            budget_max=request.budget_max,
            platforms=[p.value for p in request.platforms] if request.platforms else None,
        )

        # Run the LangGraph workflow
        try:
            final_state = await self.graph.ainvoke(initial_state)
        except Exception as e:
            log.error("orchestrator.failed", error=str(e))
            return SearchResponse(
                session_id=correlation_id,
                query=request.query,
                category=request.category or SearchCategory.PRODUCT,
                status=SearchStatus.FAILED,
                result_count=0,
                results=[],
                search_time_ms=int((time.monotonic() - start) * 1000),
            )

        elapsed_ms = int((time.monotonic() - start) * 1000)
        
        ranked_results = final_state.get("ranked_results", [])
        deals_found = final_state.get("deals", [])
        category = final_state.get("category", SearchCategory.PRODUCT)
        status = final_state.get("status", SearchStatus.COMPLETED)

        log.info("orchestrator.complete", count=len(ranked_results), ms=elapsed_ms)

        return SearchResponse(
            session_id=correlation_id,
            query=request.query,
            category=category,
            status=status,
            result_count=len(ranked_results),
            results=ranked_results,
            deals_found=deals_found,
            search_time_ms=elapsed_ms,
        )

    # ── LLM-powered search (alternative flow) ────────────────────────

    async def execute_search_with_llm(
        self,
        request: SearchRequest,
        user_id: str | None = None,
    ) -> SearchResponse:
        """
        Execute search using LLM reasoning and tool calling.
        
        This is an alternative to the deterministic workflow that uses
        the LLM to decide which tools to call based on the query.
        """
        start = time.monotonic()
        correlation_id = uuid.uuid4()
        log = logger.bind(cid=str(correlation_id))

        log.info("orchestrator.llm_search.start", query=request.query)

        # Create tools
        tools = self._get_tools()
        
        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(tools)

        # Create messages
        messages = [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=f"""User query: {request.query}
            
Additional context:
- Location: {request.location or 'Not specified'}
- Budget: {request.budget_max or 'No limit'}
- Preferred platforms: {request.platforms or 'All platforms'}

Please search for the best options and find any applicable deals."""),
        ]

        # Get LLM response with tool calls
        response = await llm_with_tools.ainvoke(messages)
        
        # Process tool calls if any
        all_results: list[SearchResultItem] = []
        all_deals = []

        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                log.info("tool_call", tool=tool_name, args=tool_args)
                
                # Find and execute the tool
                for tool in tools:
                    if tool.name == tool_name:
                        try:
                            result = await tool.ainvoke(tool_args)
                            if isinstance(result, list):
                                for r in result:
                                    if isinstance(r, dict):
                                        all_results.append(SearchResultItem(**r))
                        except Exception as e:
                            log.error("tool_execution_failed", tool=tool_name, error=str(e))

        # Rank results
        ranked = rank_results(all_results, None)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.info("orchestrator.llm_search.complete", count=len(ranked), ms=elapsed_ms)

        # Determine category from intent or default
        intent = await parse_user_query(request.query)
        category = request.category or intent.category

        return SearchResponse(
            session_id=correlation_id,
            query=request.query,
            category=category,
            status=SearchStatus.COMPLETED,
            result_count=len(ranked),
            results=ranked[:10],
            deals_found=all_deals,
            search_time_ms=elapsed_ms,
        )
