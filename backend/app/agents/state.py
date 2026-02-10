"""
LangGraph State Schema
──────────────────────
Defines the shared state for the Smart Dealer agent graph.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, TypedDict
import operator
import uuid

from pydantic import BaseModel, Field

from app.models.enums import SearchCategory, SearchStatus
from app.models.schemas import DealRead, ParsedIntent, SearchResultItem


class AgentState(TypedDict):
    """Shared state passed between agents in the LangGraph."""
    
    # Input
    session_id: str
    query: str
    user_id: str | None
    
    # Parsed intent
    intent: ParsedIntent | None
    category: SearchCategory | None
    
    # Filters
    filters: dict[str, Any]
    location: str | None
    budget_max: float | None
    platforms: list[str] | None
    
    # User preferences
    user_preferences: dict[str, Any]
    
    # Results accumulator (using operator.add for parallel node merging)
    results: Annotated[list[SearchResultItem], operator.add]
    deals: Annotated[list[DealRead], operator.add]
    
    # Final ranked results
    ranked_results: list[SearchResultItem]
    
    # Metadata
    status: SearchStatus
    errors: Annotated[list[str], operator.add]
    search_time_ms: int
    timestamp: datetime
    
    # LLM messages for reasoning
    messages: list[dict[str, Any]]


def create_initial_state(
    query: str,
    user_id: str | None = None,
    filters: dict[str, Any] | None = None,
    location: str | None = None,
    budget_max: float | None = None,
    platforms: list[str] | None = None,
) -> AgentState:
    """Create an initial state for a new search session."""
    return AgentState(
        session_id=str(uuid.uuid4()),
        query=query,
        user_id=user_id,
        intent=None,
        category=None,
        filters=filters or {},
        location=location,
        budget_max=budget_max,
        platforms=platforms,
        user_preferences={},
        results=[],
        deals=[],
        ranked_results=[],
        status=SearchStatus.PENDING,
        errors=[],
        search_time_ms=0,
        timestamp=datetime.utcnow(),
        messages=[],
    )


class ToolInput(BaseModel):
    """Base input schema for agent tools."""
    query: str = Field(..., description="Search query or item name")
    filters: dict[str, Any] = Field(default_factory=dict, description="Search filters")


class FoodSearchInput(ToolInput):
    """Input schema for food search tool."""
    location: str | None = Field(None, description="Delivery location")


class ECommerceSearchInput(ToolInput):
    """Input schema for e-commerce search tool."""
    budget_max: float | None = Field(None, description="Maximum budget")
    platforms: list[str] | None = Field(None, description="Specific platforms to search")


class RideSearchInput(ToolInput):
    """Input schema for ride search tool."""
    origin: str = Field(..., description="Pickup location")
    destination: str = Field(..., description="Drop-off location")


class HotelSearchInput(ToolInput):
    """Input schema for hotel search tool."""
    destination: str = Field(..., description="Destination city or area")
    check_in: str | None = Field(None, description="Check-in date")
    check_out: str | None = Field(None, description="Check-out date")
    nights: int = Field(default=1, description="Number of nights")


class DealSearchInput(BaseModel):
    """Input schema for deal search tool."""
    category: str = Field(..., description="Search category (food, product, ride, hotel)")
    platforms: list[str] | None = Field(None, description="Specific platforms to search")
