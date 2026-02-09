"""SQLAlchemy ORM models for the Smart Dealer system."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import DealType, Platform, SearchCategory, SearchStatus


# ── User ─────────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    profile: Mapped[Optional["UserProfile"]] = relationship(back_populates="user", uselist=False)
    searches: Mapped[list["SearchSession"]] = relationship(back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    budget_min: Mapped[Optional[float]] = mapped_column(Float)
    budget_max: Mapped[Optional[float]] = mapped_column(Float)
    preferred_platforms: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    dietary_restrictions: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    loyalty_memberships: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    default_location: Mapped[Optional[str]] = mapped_column(String(500))
    preferred_currency: Mapped[str] = mapped_column(String(3), default="USD")
    ranking_weights: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="profile")


# ── Search ───────────────────────────────────────────────────────────────────


class SearchSession(Base):
    __tablename__ = "search_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    query_text: Mapped[str] = mapped_column(Text)
    category: Mapped[SearchCategory] = mapped_column(Enum(SearchCategory))
    status: Mapped[SearchStatus] = mapped_column(Enum(SearchStatus), default=SearchStatus.PENDING)
    parsed_intent: Mapped[Optional[dict]] = mapped_column(JSON)
    filters: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped[Optional["User"]] = relationship(back_populates="searches")
    results: Mapped[list["SearchResult"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class SearchResult(Base):
    __tablename__ = "search_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("search_sessions.id", ondelete="CASCADE"))
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    item_name: Mapped[str] = mapped_column(String(500))
    base_price: Mapped[float] = mapped_column(Float)
    total_price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    fees_breakdown: Mapped[Optional[dict]] = mapped_column(JSON)
    delivery_time_min: Mapped[Optional[int]] = mapped_column(Integer)
    rating: Mapped[Optional[float]] = mapped_column(Float)
    rating_count: Mapped[Optional[int]] = mapped_column(Integer)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000))
    deep_link: Mapped[Optional[str]] = mapped_column(String(2000))
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON)
    value_score: Mapped[Optional[float]] = mapped_column(Float)
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["SearchSession"] = relationship(back_populates="results")


# ── Deals ────────────────────────────────────────────────────────────────────


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    deal_type: Mapped[DealType] = mapped_column(Enum(DealType))
    code: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    discount_amount: Mapped[Optional[float]] = mapped_column(Float)
    discount_percent: Mapped[Optional[float]] = mapped_column(Float)
    min_order: Mapped[Optional[float]] = mapped_column(Float)
    max_discount: Mapped[Optional[float]] = mapped_column(Float)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    terms: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── Price History ────────────────────────────────────────────────────────────


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    category: Mapped[SearchCategory] = mapped_column(Enum(SearchCategory))
    item_identifier: Mapped[str] = mapped_column(String(500), index=True)
    item_name: Mapped[str] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
