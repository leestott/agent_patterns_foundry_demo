"""
Instrumented agent wrapper that emits trace events for visualization.

Wraps Agent Framework agents to emit events through the shared event bus
whenever agent lifecycle methods are called.
"""

import asyncio
import time
import uuid
from typing import Any

from shared.events import EventBus, EventType

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
_RETRYABLE_ERRORS = ("Connection error", "peer closed connection", "connection attempts failed")


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(phrase.lower() in msg for phrase in _RETRYABLE_ERRORS)


class InstrumentedAgent:
    """Wraps an Agent Framework agent to emit trace events."""

    def __init__(self, agent, event_bus: EventBus):
        self._agent = agent
        self._bus = event_bus
        self.name = agent.name

    @property
    def inner(self):
        return self._agent

    async def run(self, input_text: str, **kwargs) -> Any:
        run_id = str(uuid.uuid4())[:8]
        self._bus.emit(EventType.AGENT_STARTED, {
            "agent": self.name,
            "run_id": run_id,
            "input": input_text[:200],
            "timestamp": time.time(),
        })

        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = await self._agent.run(input_text, **kwargs)
                result_text = str(result) if result else ""

                self._bus.emit(EventType.AGENT_MESSAGE, {
                    "agent": self.name,
                    "run_id": run_id,
                    "message": result_text[:500],
                    "timestamp": time.time(),
                })

                self._bus.emit(EventType.AGENT_COMPLETED, {
                    "agent": self.name,
                    "run_id": run_id,
                    "output": result_text[:500],
                    "timestamp": time.time(),
                })

                return result

            except Exception as e:
                last_exc = e
                if attempt < MAX_RETRIES and _is_retryable(e):
                    print(f"[{self.name}] Retry {attempt}/{MAX_RETRIES} after connection error, waiting {RETRY_DELAY}s...")
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                self._bus.emit(EventType.ERROR, {
                    "agent": self.name,
                    "run_id": run_id,
                    "error": str(e),
                    "timestamp": time.time(),
                })
                raise

        raise last_exc  # should not reach here

    def __getattr__(self, name):
        return getattr(self._agent, name)


def create_agent(client, name: str, instructions: str, tools=None, event_bus: EventBus | None = None):
    """Create an agent from a client, optionally instrumented.

    Args:
        client: Agent Framework client (FoundryLocalClient, OpenAIChatClient, etc.)
        name: Agent name
        instructions: System instructions
        tools: Optional list of tool functions
        event_bus: If provided, wraps the agent with instrumentation
    """
    kwargs = {"name": name, "instructions": instructions}
    if tools:
        kwargs["tools"] = tools

    agent = client.as_agent(**kwargs)

    if event_bus:
        return InstrumentedAgent(agent, event_bus)
    return agent
