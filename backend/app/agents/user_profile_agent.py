"""
User Profile Agent
──────────────────
Manages user preferences, budget constraints, loyalty memberships.
Learns from past searches and personalises results.

Integrates with LangChain for tool-based function calling.
"""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentMessage, SearchResultItem

logger = structlog.get_logger()


# ── Tool Input Schema ────────────────────────────────────────────────────────

class UserPreferencesInput(BaseModel):
    """Input schema for getting user preferences."""
    user_id: str = Field(..., description="User ID to get preferences for")


# In-memory store for demo; swap with DB in production
_PROFILES: dict[str, dict[str, Any]] = {}


class UserProfileAgent(BaseAgent):
    """Agent for managing user profiles and preferences."""
    
    name = "user_profile"
    description = "Get or update user preferences, budget constraints, and loyalty memberships. Use this to personalize search results."
    tool_input_schema = UserPreferencesInput

    async def execute(self, message: AgentMessage) -> list[SearchResultItem]:
        """Execute action from AgentMessage."""
        return []  # Profile agent doesn't return search results

    async def process(self, message: AgentMessage) -> dict[str, Any]:
        action = message.action
        user_id = message.context.get("user_id", "")

        if action == "get_preferences":
            return await self.get_preferences(user_id)
        elif action == "update_preferences":
            return await self.update_preferences(user_id, message.payload)
        elif action == "record_choice":
            return await self.record_choice(user_id, message.payload)
        return {"error": f"Unknown action: {action}"}

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[SearchResultItem]:
        return []

    # ── Profile operations ───────────────────────────────────────────

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        return _PROFILES.get(user_id, {
            "budget_min": None,
            "budget_max": None,
            "preferred_platforms": {},
            "dietary_restrictions": [],
            "loyalty_memberships": {},
            "default_location": None,
            "preferred_currency": "USD",
            "ranking_weights": None,
            "search_history_count": 0,
        })

    async def update_preferences(self, user_id: str, prefs: dict[str, Any]) -> dict[str, Any]:
        existing = _PROFILES.get(user_id, {})
        existing.update(prefs)
        _PROFILES[user_id] = existing
        logger.info("profile.updated", user_id=user_id)
        return existing

    async def record_choice(self, user_id: str, choice: dict[str, Any]) -> dict[str, Any]:
        """Record a user's selection so the system can learn preferences."""
        profile = _PROFILES.get(user_id, {})
        history: list[dict] = profile.get("choice_history", [])
        history.append(choice)
        profile["choice_history"] = history[-50]  # keep last 50
        profile["search_history_count"] = profile.get("search_history_count", 0) + 1
        _PROFILES[user_id] = profile
        logger.info("choice.recorded", user_id=user_id)
        return {"status": "recorded"}
