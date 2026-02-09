"""
Notification Service
────────────────────
Price-drop alerts, deal expirations, best-time-to-book recommendations.
Uses in-memory event bus; swap for Redis Pub/Sub or WebSockets in production.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Coroutine
from uuid import UUID

import structlog

logger = structlog.get_logger()

# ── Types ────────────────────────────────────────────────────────────────────

Subscriber = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


# ── In-memory notification hub ───────────────────────────────────────────────

class NotificationService:
    """Simple pub/sub notification service."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = {}
        self._pending: list[dict[str, Any]] = []

    def subscribe(self, event_type: str, callback: Subscriber) -> None:
        self._subscribers.setdefault(event_type, []).append(callback)
        logger.info("notification.subscribed", event=event_type)

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        notification = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._pending.append(notification)
        for cb in self._subscribers.get(event_type, []):
            try:
                await cb(notification)
            except Exception as exc:
                logger.error("notification.callback.error", event=event_type, error=str(exc))

    async def price_drop_alert(self, user_id: str, item: str, old_price: float, new_price: float, platform: str) -> None:
        await self.publish("price_drop", {
            "user_id": user_id,
            "item": item,
            "old_price": old_price,
            "new_price": new_price,
            "savings": round(old_price - new_price, 2),
            "platform": platform,
        })

    async def deal_expiring(self, deal_id: str, description: str, expires_at: str) -> None:
        await self.publish("deal_expiring", {
            "deal_id": deal_id,
            "description": description,
            "expires_at": expires_at,
        })

    async def surge_alert(self, user_id: str, platform: str, surge_multiplier: float) -> None:
        await self.publish("surge_alert", {
            "user_id": user_id,
            "platform": platform,
            "surge_multiplier": surge_multiplier,
            "message": f"Surge pricing active on {platform}: {surge_multiplier}x",
        })

    def get_pending(self, user_id: str | None = None) -> list[dict[str, Any]]:
        if user_id:
            return [n for n in self._pending if n.get("data", {}).get("user_id") == user_id]
        return list(self._pending)

    def clear_pending(self) -> None:
        self._pending.clear()


# Singleton
notifications = NotificationService()
