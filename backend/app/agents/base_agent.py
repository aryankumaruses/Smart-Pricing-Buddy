""""""Abstract base class for all specialized agents."""







































































        return uuid.uuid4()    def _result_id() -> uuid.UUID:    @staticmethod    # ── helpers ──────────────────────────────────────────────────────        ...        """Execute a platform search and return normalised results."""    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[SearchResultItem]:    @abc.abstractmethod        ...        """Core logic – implemented per agent."""    async def process(self, message: AgentMessage) -> dict[str, Any]:    @abc.abstractmethod    # ── to be implemented by subclasses ──────────────────────────────            )                correlation_id=message.correlation_id,                context=message.context,                payload={"error": str(exc)},                action=f"{message.action}.error",                agent_to=message.agent_from,                agent_from=self.name,            return AgentMessage(            log.error("agent.handle.error", error=str(exc))        except Exception as exc:            )                correlation_id=message.correlation_id,                context=message.context,                payload=result,                action=f"{message.action}.response",                agent_to=message.agent_from,                agent_from=self.name,            return AgentMessage(            log.info("agent.handle.done", elapsed_ms=elapsed_ms)            elapsed_ms = int((time.monotonic() - start) * 1000)            result = await self.process(message)        try:        log.info("agent.handle.start")        log = logger.bind(agent=self.name, action=message.action, cid=str(message.correlation_id))        start = time.monotonic()        """Receive a message, process it, and return a response message."""    async def handle(self, message: AgentMessage) -> AgentMessage:    # ── public interface ─────────────────────────────────────────────    name: str = "base"    """Abstract base for every Smart Dealer agent."""class BaseAgent(abc.ABC):logger = structlog.get_logger()from app.models.schemas import AgentMessage, SearchResultItemimport structlogfrom typing import Anyimport uuidimport timeimport abcfrom __future__ import annotations"""Base agent contract.  Every specialised agent inherits from this class.
from __future__ import annotations

import abc
import asyncio
import uuid
from datetime import datetime
from typing import Any, Optional

import structlog

from app.models.schemas import AgentMessage, SearchResultItem

logger = structlog.get_logger()


class BaseAgent(abc.ABC):
    """Every agent in the system inherits from this base."""

    name: str = "base_agent"
    description: str = ""

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
            elapsed = (datetime.utcnow() - start).total_seconds()
            self.log.info("completed", results=len(results), elapsed_s=round(elapsed, 2))
            return results
        except Exception as exc:
            self.log.error("agent_error", error=str(exc))
            return []

    @abc.abstractmethod
    async def execute(self, message: AgentMessage) -> list[SearchResultItem]:
        """Subclasses implement platform-specific logic here."""
        ...

    # ── Helpers ──────────────────────────────────────────
    def _build_message(self, to: str, action: str, payload: dict, context: dict | None = None) -> AgentMessage:
        return AgentMessage(
            agent_from=self.name,
            agent_to=to,
            action=action,
            payload=payload,
            context=context or {},
        )
