"""
Orchestration helpers wrapping Agent Framework pattern builders.

Each function takes a list of agents (or InstrumentedAgents) and
runs the appropriate orchestration, emitting events through the event bus.
"""

import json
import time
from typing import Any

from shared.events import EventBus, EventType


def _unwrap(agent):
    """Get the inner AF agent from an InstrumentedAgent, or return as-is."""
    from shared.runtime.agent_wrapper import InstrumentedAgent
    return agent.inner if isinstance(agent, InstrumentedAgent) else agent


def _agents_by_name(agents) -> dict:
    """Map agent names to agents for lookup."""
    return {a.name: a for a in agents}


def _extract_text(msg) -> str:
    """Extract plain text from a Message, handling JSON-encoded content."""
    raw = getattr(msg, "text", None) or str(msg)
    # Sometimes the model returns JSON-wrapped content like [{'type':'text','text':'...'}]
    if raw.startswith("[{") or raw.startswith("[{'"):
        try:
            parts = json.loads(raw.replace("'", '"'))
            if isinstance(parts, list):
                return " ".join(p.get("text", str(p)) for p in parts if isinstance(p, dict))
        except (json.JSONDecodeError, TypeError):
            pass
    return raw


def _emit_output_messages(event_data, event_bus, event_type, results):
    """Process output event data — extract messages and emit events.

    Only processes final Message objects; skips AgentResponseUpdate streaming
    token chunks which fire on the same 'output' event type.
    """
    msgs = event_data if isinstance(event_data, list) else [event_data]
    for msg in msgs:
        # Skip streaming token chunks — only handle complete Message objects
        if type(msg).__name__ == "AgentResponseUpdate":
            continue
        role = getattr(msg, "role", None)
        if role == "user":
            continue
        author = getattr(msg, "author_name", None) or "unknown"
        text = _extract_text(msg)
        if not text or author == "group_chat_orchestrator":
            continue
        event_bus.emit(event_type, {
            "agent": author,
            "message": text[:500],
            "timestamp": time.time(),
        })
        results.append({"agent": author, "text": text})


def _emit_executor_events(event, event_bus):
    """Emit lifecycle events from executor_invoked / executor_completed."""
    if event.type == "executor_invoked":
        data = event.data
        # data can be a string (first agent input) or AgentExecutorResponse/Request
        executor_id = getattr(data, "executor_id", None)
        if executor_id:
            event_bus.emit(EventType.AGENT_STARTED, {
                "agent": executor_id,
                "timestamp": time.time(),
            })
    elif event.type == "executor_completed":
        data = event.data
        if isinstance(data, list) and data:
            first = data[0]
            executor_id = getattr(first, "executor_id", None)
            if executor_id:
                agent_resp = getattr(first, "agent_response", None)
                text = _extract_text(agent_resp) if agent_resp else ""
                event_bus.emit(EventType.AGENT_COMPLETED, {
                    "agent": executor_id,
                    "output": text[:500] if text else "",
                    "timestamp": time.time(),
                })


async def run_sequential(agents: list, input_text: str, event_bus: EventBus | None = None, **kwargs) -> Any:
    """Run agents in sequential order using SequentialBuilder."""
    from agent_framework.orchestrations import SequentialBuilder

    if event_bus:
        event_bus.emit(EventType.AGENT_STARTED, {
            "agent": "Orchestrator",
            "pattern": "sequential",
            "participants": [a.name for a in agents],
            "timestamp": time.time(),
        })

    raw_agents = [_unwrap(a) for a in agents]
    workflow = SequentialBuilder(participants=raw_agents).build()

    results = []
    async for event in workflow.run(input_text, stream=True):
        if not event_bus:
            continue
        if event.type == "output":
            _emit_output_messages(event.data, event_bus, EventType.AGENT_MESSAGE, results)
        elif event.type in ("executor_invoked", "executor_completed"):
            _emit_executor_events(event, event_bus)

    if event_bus:
        event_bus.emit(EventType.AGENT_COMPLETED, {
            "agent": "Orchestrator",
            "pattern": "sequential",
            "timestamp": time.time(),
        })

    return results


async def run_concurrent(agents: list, input_text: str, event_bus: EventBus | None = None, **kwargs) -> Any:
    """Run agents concurrently using ConcurrentBuilder (fan-out/fan-in)."""
    from agent_framework.orchestrations import ConcurrentBuilder

    if event_bus:
        event_bus.emit(EventType.AGENT_STARTED, {
            "agent": "Orchestrator",
            "pattern": "concurrent",
            "participants": [a.name for a in agents],
            "timestamp": time.time(),
        })

    raw_agents = [_unwrap(a) for a in agents]
    workflow = ConcurrentBuilder(participants=raw_agents).build()

    results = []
    async for event in workflow.run(input_text, stream=True):
        if not event_bus:
            continue
        if event.type == "output":
            _emit_output_messages(event.data, event_bus, EventType.AGENT_MESSAGE, results)
        elif event.type in ("executor_invoked", "executor_completed"):
            _emit_executor_events(event, event_bus)

    if event_bus:
        event_bus.emit(EventType.AGENT_COMPLETED, {
            "agent": "Orchestrator",
            "pattern": "concurrent",
            "timestamp": time.time(),
        })

    return results


async def run_handoff(agents: list, input_text: str, start_agent=None,
                      event_bus: EventBus | None = None,
                      max_rounds: int = 6, **kwargs) -> Any:
    """Run agents with handoff pattern using HandoffBuilder."""
    from agent_framework.orchestrations import HandoffBuilder

    if event_bus:
        event_bus.emit(EventType.AGENT_STARTED, {
            "agent": "Orchestrator",
            "pattern": "handoff",
            "participants": [a.name for a in agents],
            "timestamp": time.time(),
        })

    raw_agents = [_unwrap(a) for a in agents]
    start = _unwrap(start_agent) if start_agent else raw_agents[0]

    def _max_messages_reached(messages) -> bool:
        return len(messages) >= max_rounds * 2

    builder = HandoffBuilder(
        participants=raw_agents,
    ).with_start_agent(start).with_autonomous_mode()
    builder = builder.with_termination_condition(_max_messages_reached)

    workflow = builder.build()

    results = []
    max_events = max_rounds * 50  # Hard safety limit on events
    event_count = 0
    async for event in workflow.run(input_text, stream=True):
        event_count += 1
        if event_count > max_events:
            print(f"HandoffOrchestrator reached max events ({max_events}); forcing completion.")
            break
        if not event_bus:
            continue
        if event.type == "output":
            _emit_output_messages(event.data, event_bus, EventType.HANDOFF, results)
        elif event.type == "handoff_sent":
            event_bus.emit(EventType.HANDOFF, {
                "from_agent": str(event.data)[:200] if event.data else "unknown",
                "message": "Handoff",
                "timestamp": time.time(),
            })
        elif event.type in ("executor_invoked", "executor_completed"):
            _emit_executor_events(event, event_bus)

    if event_bus:
        event_bus.emit(EventType.AGENT_COMPLETED, {
            "agent": "Orchestrator",
            "pattern": "handoff",
            "timestamp": time.time(),
        })

    return results


async def run_group_chat(agents: list, input_text: str,
                         event_bus: EventBus | None = None,
                         max_rounds: int = 4, **kwargs) -> Any:
    """Run agents in group chat using GroupChatBuilder with round-robin selection."""
    from agent_framework.orchestrations import GroupChatBuilder

    if event_bus:
        event_bus.emit(EventType.AGENT_STARTED, {
            "agent": "Orchestrator",
            "pattern": "group_chat",
            "participants": [a.name for a in agents],
            "timestamp": time.time(),
        })

    raw_agents = [_unwrap(a) for a in agents]
    agent_names = [a.name for a in agents]

    def round_robin(state):
        return agent_names[state.current_round % len(agent_names)]

    workflow = GroupChatBuilder(
        participants=raw_agents,
        selection_func=round_robin,
        max_rounds=max_rounds,
    ).build()

    results = []
    async for event in workflow.run(input_text, stream=True):
        if not event_bus:
            continue
        if event.type == "output":
            _emit_output_messages(event.data, event_bus, EventType.AGENT_MESSAGE, results)
        elif event.type in ("executor_invoked", "executor_completed"):
            _emit_executor_events(event, event_bus)

    if event_bus:
        event_bus.emit(EventType.AGENT_COMPLETED, {
            "agent": "Orchestrator",
            "pattern": "group_chat",
            "timestamp": time.time(),
        })

    return results


async def run_magentic(agents: list, input_text: str,
                       event_bus: EventBus | None = None, **kwargs) -> Any:
    """Run agents with Magentic-One pattern using MagenticBuilder."""
    from agent_framework.orchestrations import MagenticBuilder
    from shared.runtime.foundry_client import get_foundry_client

    if event_bus:
        event_bus.emit(EventType.AGENT_STARTED, {
            "agent": "Orchestrator",
            "pattern": "magentic",
            "participants": [a.name for a in agents],
            "timestamp": time.time(),
        })

    raw_agents = [_unwrap(a) for a in agents]
    # Magentic-One needs a manager agent to orchestrate
    manager_client = get_foundry_client()
    manager = manager_client.as_agent(
        name="MagenticManager",
        instructions="You are the Magentic-One manager. Coordinate the participants to complete the task.",
    )

    workflow = MagenticBuilder(
        participants=raw_agents,
        manager_agent=manager,
        max_round_count=len(raw_agents) + 2,
    ).build()

    results = []
    async for event in workflow.run(input_text, stream=True):
        if not event_bus:
            continue
        if event.type == "output":
            _emit_output_messages(event.data, event_bus, EventType.AGENT_MESSAGE, results)
        elif event.type in ("executor_invoked", "executor_completed"):
            _emit_executor_events(event, event_bus)

    if event_bus:
        event_bus.emit(EventType.AGENT_COMPLETED, {
            "agent": "Orchestrator",
            "pattern": "magentic",
            "timestamp": time.time(),
        })

    return results
