"""
Health & meta endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.models.enums import Platform, SearchCategory

router = APIRouter(tags=["Meta"])
settings = get_settings()


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "app": settings.APP_NAME, "env": settings.APP_ENV}


@router.get("/platforms")
async def platforms() -> dict:
    return {
        "categories": [c.value for c in SearchCategory],
        "platforms": [p.value for p in Platform],
    }
