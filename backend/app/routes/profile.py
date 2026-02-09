"""
User-profile routes.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.agents.user_profile_agent import UserProfileAgent
from app.models.schemas import UserProfileUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])

_profile_agent = UserProfileAgent()


@router.get("/{user_id}")
async def get_profile(user_id: str) -> dict[str, Any]:
    return await _profile_agent.get_preferences(user_id)


@router.put("/{user_id}")
async def update_profile(user_id: str, body: UserProfileUpdate) -> dict[str, Any]:
    return await _profile_agent.update_preferences(user_id, body.model_dump(exclude_unset=True))
