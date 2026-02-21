# Architecture

## Overview

The Visual Agent Patterns Demo Pack is a collection of six demos that showcase
different **Microsoft Agent Framework** orchestration patterns running against
**Foundry Local** (on-device AI runtime).

## Layers

```
┌──────────────────────────────────────────────────────┐
│                  Demo Runners (demos/)                │
│  maker_checker │ hierarchical │ handoff │ network …  │
├──────────────────────────────────────────────────────┤
│               Shared Runtime (shared/runtime/)       │
│  foundry_client · agent_wrapper · orchestrations     │
├──────────────────────────────────────────────────────┤
│               Event Layer (shared/events/)           │
│  event_bus · event_types · JSONL logging             │
├──────────────────────────────────────────────────────┤
│               Visual UI (shared/ui/)                 │
│  FastAPI + WebSocket · D3.js graph · timeline/stream │
├──────────────────────────────────────────────────────┤
│               Foundry Local Runtime                  │
│  On-device model serving · dynamic port              │
└──────────────────────────────────────────────────────┘
```

## Agent Framework Patterns Used

| Pattern | Builder | Demos |
|---------|---------|-------|
| Sequential | `SequentialBuilder` | 1 (Maker-Checker), 2 (Research synthesis), 5 (Supervisor classify), 6 (Audit+Select) |
| Concurrent | `ConcurrentBuilder` | 2 (Parallel research), 6 (Swarm generators) |
| Handoff | `HandoffBuilder` | 3 (Customer Support triage), 5 (Route to specialist) |
| Group Chat | `GroupChatBuilder` | 4 (Brainstorm network) |
| Magentic | `MagenticBuilder` | Available in `orchestrations.py` for custom demos |

## Runtime Flow

1. Each demo's `run.py` calls `create_agents()` from its `agents.py`.
2. Agents are wrapped in `InstrumentedAgent` which emits events to the `EventBus`.
3. The `EventBus` broadcasts events over WebSocket to the D3-powered dashboard.
4. Events are also written to JSONL files under each demo's `runs/` folder for replay.

## Dynamic Port Detection

Foundry Local serves models on a dynamic port. The shared runtime calls
`foundry service status` to discover the endpoint at startup. Override via
`FOUNDRY_LOCAL_ENDPOINT` in `.env` if needed.

## Key Imports

```python
from agent_framework.openai import OpenAIChatClient
from agent_framework.orchestrations import (
    SequentialBuilder, ConcurrentBuilder,
    HandoffBuilder, GroupChatBuilder,
    MagenticBuilder,
)
```
