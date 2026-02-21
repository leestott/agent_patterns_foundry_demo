"""
Swarm + Auditor Custom — Runner.

Orchestration Patterns:
  - Concurrent (ConcurrentBuilder) — Generators brainstorm in parallel
  - Sequential (SequentialBuilder) — Auditor scores, Selector picks winner

Flow: [Generator_A || Generator_B || Generator_C] → Auditor → Selector
"""

import asyncio
import json
import threading
import time
from pathlib import Path

from shared.events import EventBus, EventType
from shared.ui.server import start_ui
from demos.swarm_auditor.agents import create_agents

TOPOLOGY = json.loads((Path(__file__).parent / "topology.json").read_text())
LOG_DIR = str(Path(__file__).parent / "runs")

TASK_INPUT = "Our mid-size SaaS company wants to reduce cloud infrastructure costs by 40% while maintaining 99.9% uptime and improving developer velocity. What should we do?"


async def run_demo(event_bus: EventBus, input_text: str | None = None):
    task = input_text or TASK_INPUT
    gen_a, gen_b, gen_c, auditor, selector = create_agents(event_bus)

    event_bus.emit(EventType.AGENT_STARTED, {
        "agent": "Orchestrator", "pattern": "concurrent + sequential",
        "message": "Starting swarm generation phase",
        "timestamp": time.time(),
    })

    # Phase 1: Concurrent — all generators run in parallel
    results = await asyncio.gather(
        gen_a.run(task),
        gen_b.run(task),
        gen_c.run(task),
    )

    proposals = "\n\n".join(str(r) for r in results)

    # Phase 2: Sequential — Auditor scores proposals
    audit_input = f"Here are three proposals to evaluate:\n\n{proposals}"
    audit_result = await auditor.run(audit_input)

    # Phase 3: Sequential — Selector picks the winner
    selector_input = f"Proposals:\n{proposals}\n\nAudit Scores:\n{audit_result}"
    await selector.run(selector_input)

    event_bus.emit(EventType.AGENT_COMPLETED, {
        "agent": "Orchestrator", "pattern": "concurrent + sequential",
        "message": "Swarm + audit cycle complete",
        "timestamp": time.time(),
    })


def main():
    event_bus = EventBus(log_dir=LOG_DIR)
    thread = threading.Thread(target=lambda: asyncio.run(run_demo(event_bus)), daemon=True)
    thread.start()
    start_ui(event_bus, topology=TOPOLOGY)


if __name__ == "__main__":
    main()
