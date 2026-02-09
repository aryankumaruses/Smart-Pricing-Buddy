"""
Smart Dealer – FastAPI Application
───────────────────────────────────
Multi-agent price comparison system.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.logging_config import setup_logging
from app.services.cache import cache
from app.services.scraper import scraper

# Import routers
from app.routes.search import router as search_router
from app.routes.deals import router as deals_router
from app.routes.profile import router as profile_router
from app.routes.notifications import router as notif_router
from app.routes.health import router as health_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Startup / shutdown lifecycle."""
    setup_logging(debug=settings.DEBUG)
    await cache.connect()
    await scraper.start()
    yield
    await scraper.close()


app = FastAPI(
    title="Smart Dealer API",
    description="Multi-agent price comparison across food delivery, e-commerce, rides, and hotels.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(health_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(deals_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(notif_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "app": "Smart Dealer",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
