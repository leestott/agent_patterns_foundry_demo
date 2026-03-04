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
    """Run agents with handoff pattern.

    Demonstrates explicit handoff: the start agent classifies input and signals
    transfer via "Transferring to <AgentName>." in its response. The orchestrator
    parses this signal and routes to the named specialist, passing full context.

    Note: HandoffBuilder autonomous mode only emits streaming AgentResponseUpdate
    chunks which cannot be captured per-agent. This implementation calls agents
    directly and parses the transfer signal for reliable output capture.
    """
    if event_bus:
        event_bus.emit(EventType.AGENT_STARTED, {
            "agent": "Orchestrator",
            "pattern": "handoff",
            "participants": [a.name for a in agents],
            "timestamp": time.time(),
        })

    agent_map = {a.name: a for a in agents}
    current = start_agent or agents[0]
    results = []
    context = input_text

    for round_num in range(max_rounds):
        agent_name = current.name

        if event_bus:
            event_bus.emit(EventType.AGENT_STARTED, {
                "agent": agent_name,
                "timestamp": time.time(),
            })

        try:
            raw = _unwrap(current)
            response = await raw.run(context)
            text = _extract_text(response) if response else ""
        except Exception as e:
            if event_bus:
                event_bus.emit(EventType.ERROR, {
                    "agent": agent_name, "error": str(e), "timestamp": time.time(),
                })
            break

        if event_bus:
            event_bus.emit(EventType.AGENT_MESSAGE, {
                "agent": agent_name, "message": text[:500], "timestamp": time.time(),
            })
            event_bus.emit(EventType.AGENT_COMPLETED, {
                "agent": agent_name, "output": text[:500], "timestamp": time.time(),
            })

        results.append({"agent": agent_name, "text": text})

        # Termination signals from specialist agents
        if any(sig in text.upper() for sig in ("TASK COMPLETE", "RESOLVED")):
            break

        # Parse handoff signal: "Transferring to <AgentName>."
        next_name = None
        for name in agent_map:
            if f"Transferring to {name}" in text:
                next_name = name
                break

        if next_name and next_name != agent_name:
            if event_bus:
                event_bus.emit(EventType.HANDOFF, {
                    "from_agent": agent_name,
                    "to_agent": next_name,
                    "message": f"{agent_name} → {next_name}",
                    "timestamp": time.time(),
                })
            current = agent_map[next_name]
            # Give the specialist the original request plus the routing agent's context
            context = f"{input_text}\n\n[{agent_name} assessment]: {text}"
        elif round_num > 0:
            # Specialist has responded with no further handoff — done
            break

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


# Explicit progress ledger prompt with a concrete example to handle small models (e.g. qwen2.5-1.5b)
# that return flattened booleans instead of the required nested {"reason": ..., "answer": ...} objects.
_MAGENTIC_PROGRESS_LEDGER_PROMPT = """Recall we are working on the following request:

{task}

And we have assembled the following team:

{team}

Assess the current progress and answer the questions below.

CRITICAL FORMATTING RULE: Every field in your JSON response MUST be an object with exactly
two keys: "reason" (a string) and "answer" (the value). NEVER output a bare boolean or string
at the top level — always wrap it in the object structure.

Here is the EXACT format you must follow (copy this structure exactly):

{{
    "is_request_satisfied": {{"reason": "Explain why the task is or is not complete.", "answer": false}},
    "is_in_loop": {{"reason": "Explain whether you are repeating the same steps.", "answer": false}},
    "is_progress_being_made": {{"reason": "Explain whether new progress is being made.", "answer": true}},
    "next_speaker": {{"reason": "Explain why this person should speak next.", "answer": "{names}"}},
    "instruction_or_question": {{"reason": "Explain the goal of this instruction.", "answer": "Your specific instruction to the next speaker."}}
}}

Now produce the JSON object for the current situation. Select next_speaker from: {names}
Output ONLY the JSON object. Do not include any explanation, markdown, or text outside the JSON.
"""


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
        instructions=(
            "You are the Magentic-One orchestration manager. Your only job is to assess progress "
            "and output a JSON progress ledger when asked. Always follow the exact JSON schema provided. "
            "Never output bare booleans — always wrap values in {\"reason\": ..., \"answer\": ...} objects."
        ),
    )

    workflow = MagenticBuilder(
        participants=raw_agents,
        manager_agent=manager,
        max_round_count=len(raw_agents) * 3 + 3,
        progress_ledger_prompt=_MAGENTIC_PROGRESS_LEDGER_PROMPT,
    ).build()

    results = []
    async for event in workflow.run(input_text, stream=True):
        if not event_bus:
            continue
        if event.type == "output":
            _emit_output_messages(event.data, event_bus, EventType.AGENT_MESSAGE, results)
        elif event.type in ("executor_invoked", "executor_completed"):
            _emit_executor_events(event, event_bus)

    # Fallback: if MagenticManager absorbed all output without routing to specialists
    # (common with small models that can't follow the JSON progress ledger format),
    # invoke each specialist directly with a role-focused prompt so all agents produce output.
    specialist_names = {a.name for a in agents}
    specialists_seen = {r["agent"] for r in results if r["agent"] in specialist_names}
    if not specialists_seen:
        print("[run_magentic] MagenticManager did not route to specialists; invoking them directly.")
        for agent in agents:
            role_prompt = (
                f"Task: {input_text}\n\n"
                f"You are the {agent.name}. Apply your specific expertise to this task."
            )
            if event_bus:
                event_bus.emit(EventType.AGENT_STARTED, {
                    "agent": agent.name, "timestamp": time.time(),
                })
            try:
                raw = _unwrap(agent)
                response = await raw.run(role_prompt)
                text = _extract_text(response) if response else ""
            except Exception as e:
                if event_bus:
                    event_bus.emit(EventType.ERROR, {
                        "agent": agent.name, "error": str(e), "timestamp": time.time(),
                    })
                continue
            if text:
                if event_bus:
                    event_bus.emit(EventType.AGENT_MESSAGE, {
                        "agent": agent.name, "message": text[:500], "timestamp": time.time(),
                    })
                    event_bus.emit(EventType.AGENT_COMPLETED, {
                        "agent": agent.name, "output": text[:500], "timestamp": time.time(),
                    })
                results.append({"agent": agent.name, "text": text})

    if event_bus:
        event_bus.emit(EventType.AGENT_COMPLETED, {
            "agent": "Orchestrator",
            "pattern": "magentic",
            "timestamp": time.time(),
        })

    return results
