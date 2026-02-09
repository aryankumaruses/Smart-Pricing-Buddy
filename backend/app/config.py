"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "SmartDealer"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/smartdealer"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── OpenAI ───────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── External API Keys ────────────────────────────────
    UBER_CLIENT_ID: str = ""
    UBER_CLIENT_SECRET: str = ""
    LYFT_CLIENT_ID: str = ""
    LYFT_CLIENT_SECRET: str = ""
    DOORDASH_API_KEY: str = ""
    UBEREATS_API_KEY: str = ""
    AMAZON_ACCESS_KEY: str = ""
    AMAZON_SECRET_KEY: str = ""
    AMAZON_PARTNER_TAG: str = ""
    EBAY_APP_ID: str = ""
    BOOKING_API_KEY: str = ""
    EXPEDIA_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    # ── Rate Limiting ────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    SCRAPE_DELAY_SECONDS: float = 2.0

    # ── Ranking Weights (default) ─────────────────────────
    WEIGHT_PRICE: float = 0.40
    WEIGHT_TIME: float = 0.20
    WEIGHT_RATING: float = 0.20
    WEIGHT_FEES: float = 0.10
    WEIGHT_USER_PREF: float = 0.10


@lru_cache
def get_settings() -> Settings:
    return Settings()
