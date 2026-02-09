"""
Notification routes.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services.notifications import notifications

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/")
async def get_notifications(user_id: str | None = None) -> list[dict[str, Any]]:
    """Get pending notifications, optionally filtered by user."""
    return notifications.get_pending(user_id)


@router.delete("/clear")
async def clear_notifications() -> dict[str, str]:
    notifications.clear_pending()
    return {"status": "cleared"}
