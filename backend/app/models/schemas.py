"""Pydantic schemas for request / response validation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import DealType, Platform, SearchCategory, SearchStatus


# ── Auth ─────────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User Profile ─────────────────────────────────────────────────────────────


class UserProfileUpdate(BaseModel):
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_platforms: Optional[dict[str, bool]] = None
    dietary_restrictions: Optional[list[str]] = None
    loyalty_memberships: Optional[dict[str, str]] = None
    default_location: Optional[str] = None
    preferred_currency: Optional[str] = "USD"
    ranking_weights: Optional[dict[str, float]] = None


class UserProfileRead(UserProfileUpdate):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Search ───────────────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language search query")
    category: Optional[SearchCategory] = None
    filters: Optional[dict[str, Any]] = None
    location: Optional[str] = None
    budget_max: Optional[float] = None
    platforms: Optional[list[Platform]] = None


class ParsedIntent(BaseModel):
    category: SearchCategory
    item: str
    filters: dict[str, Any] = {}
    location: Optional[str] = None
    time_constraint: Optional[str] = None
    budget: Optional[float] = None
    sort_preference: Optional[str] = None


class PriceBreakdown(BaseModel):
    base_price: float
    delivery_fee: float = 0.0
    service_fee: float = 0.0
    tax: float = 0.0
    tip: float = 0.0
    discount: float = 0.0
    total: float


class SearchResultItem(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    platform: Platform
    item_name: str
    base_price: float
    total_price: float
    currency: str = "USD"
    fees_breakdown: Optional[PriceBreakdown] = None
    delivery_time_min: Optional[int] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    image_url: Optional[str] = None
    deep_link: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None
    value_score: Optional[float] = None
    rank: Optional[int] = None
    savings_vs_max: Optional[float] = None
    deals_applied: list[str] = []
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    session_id: uuid.UUID
    query: str
    category: SearchCategory
    status: SearchStatus
    result_count: int
    results: list[SearchResultItem]
    deals_found: list["DealRead"] = []
    search_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Deals ────────────────────────────────────────────────────────────────────


class DealRead(BaseModel):
    id: uuid.UUID
    platform: Platform
    deal_type: DealType
    code: Optional[str]
    description: str
    discount_amount: Optional[float]
    discount_percent: Optional[float]
    min_order: Optional[float]
    max_discount: Optional[float]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    is_active: bool

    model_config = {"from_attributes": True}


# ── Price History ─────────────────────────────────────────────────────────────


class PricePoint(BaseModel):
    price: float
    recorded_at: datetime
    platform: Platform


class PriceTrend(BaseModel):
    item_identifier: str
    item_name: str
    category: SearchCategory
    history: list[PricePoint]
    avg_price: float
    min_price: float
    max_price: float
    current_price: float
    recommendation: str


# ── Agent Messages ───────────────────────────────────────────────────────────


class AgentMessage(BaseModel):
    """Standardized message format for inter-agent communication."""

    agent_from: str
    agent_to: str
    action: str
    payload: dict[str, Any] = {}
    context: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
