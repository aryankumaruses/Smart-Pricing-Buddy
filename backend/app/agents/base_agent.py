"""
Abstract base class for all specialized agents.

This class defines the contract for all agents in the system. Each specialized 
agent inherits from this base class and implements its own platform-specific logic.

Integrates with LangChain tools for function calling and LangGraph for orchestration.

Methods:
- handle: Receive a message, process it, and return a response message.
- execute: Core logic to be implemented by subclasses.
- as_tool: Returns a LangChain Tool for the agent.

"""

from __future__ import annotations

import abc
import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Optional, Type

import structlog
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from app.models.schemas import AgentMessage, SearchResultItem

logger = structlog.get_logger()


class BaseAgent(abc.ABC):
    """Every agent in the system inherits from this base.
    
    Provides integration with LangChain tools for function calling.
    """

    name: str = "base_agent"
    description: str = "Base agent - override in subclass"
    
    # Override in subclass to specify the input schema for the tool
    tool_input_schema: Type[BaseModel] | None = None

    def __init__(self) -> None:
        self.agent_id = str(uuid.uuid4())
        self.log = logger.bind(agent=self.name, agent_id=self.agent_id)

    # ── Public interface ─────────────────────────────────
    async def handle(self, message: AgentMessage) -> list[SearchResultItem]:
        """Entry-point called by the orchestrator."""
        self.log.info("handling_message", action=message.action)
        start = datetime.utcnow()
        try:
            results = await self.execute(message)
            elapsed = (datetime.now() - start).total_seconds()
            self.log.info("completed", results=len(results), elapsed_s=round(elapsed, 2))
            return results
        except Exception as exc:
            self.log.error("agent_error", error=str(exc))
            return []

    @abc.abstractmethod
    async def execute(self, message: AgentMessage) -> list[SearchResultItem]:
        """Subclasses implement platform-specific logic here."""
        ...

    @abc.abstractmethod
    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[SearchResultItem]:
        """Execute a search with the given query and filters."""
        ...

    # ── LangChain Tool Integration ───────────────────────
    def as_tool(self) -> BaseTool:
        """Return this agent as a LangChain Tool for function calling."""
        
        async def _run_async(**kwargs: Any) -> list[dict]:
            """Async execution wrapper."""
            query = kwargs.pop("query", "")
            filters = kwargs  # remaining kwargs become filters
            results = await self.search(query, filters)
            return [r.model_dump(mode="json") for r in results]
        
        def _run_sync(**kwargs: Any) -> list[dict]:
            """Sync execution wrapper."""
            return asyncio.get_event_loop().run_until_complete(_run_async(**kwargs))
        
        return StructuredTool(
            name=self.name,
            description=self.description,
            func=_run_sync,
            coroutine=_run_async,
            args_schema=self.tool_input_schema,
        )

    # ── Helpers ──────────────────────────────────────────
    def _build_message(self, to: str, action: str, payload: dict, context: dict | None = None) -> AgentMessage:
        return AgentMessage(
            agent_from=self.name,
            agent_to=to,
            action=action,
            payload=payload,
            context=context or {},
        )

