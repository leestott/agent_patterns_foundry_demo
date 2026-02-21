"""
Supervisor Router — Runner.

Orchestration Patterns:
  - Sequential (SequentialBuilder) — Supervisor classifies the task
  - Handoff (HandoffBuilder) — Supervisor routes to selected specialist

Flow: Supervisor classifies → routes to CodeExpert / DataExpert / DocExpert
"""

import asyncio
import json
import threading
import time
from pathlib import Path

from shared.events import EventBus, EventType
from shared.ui.server import start_ui
from demos.supervisor_router.agents import create_agents

TOPOLOGY = json.loads((Path(__file__).parent / "topology.json").read_text())
LOG_DIR = str(Path(__file__).parent / "runs")

TASK_INPUT = "Write a Python function that reads a CSV file, groups rows by category, and returns the top 3 categories by total revenue. Include docstrings."


async def run_demo(event_bus: EventBus, input_text: str | None = None):
    task = input_text or TASK_INPUT
    supervisor, code_expert, data_expert, doc_expert = create_agents(event_bus)

    specialists = {"CodeExpert": code_expert, "DataExpert": data_expert, "DocExpert": doc_expert}

    # Step 1: Supervisor classifies (Sequential pattern)
    event_bus.emit(EventType.AGENT_STARTED, {
        "agent": "Orchestrator", "pattern": "sequential + handoff",
        "message": "Supervisor classifying task",
        "timestamp": time.time(),
    })

    classification = await supervisor.run(task)
    classification_text = str(classification)

    # Parse routing decision
    target_agent = None
    for line in classification_text.split("\n"):
        line = line.strip()
        if line.upper().startswith("ROUTE:"):
            agent_name = line.split(":", 1)[1].strip()
            target_agent = specialists.get(agent_name)
            if target_agent:
                event_bus.emit(EventType.HANDOFF, {
                    "from_agent": "Supervisor",
                    "to_agent": agent_name,
                    "message": f"Routing to {agent_name}",
                    "timestamp": time.time(),
                })
            break

    if not target_agent:
        # Default to CodeExpert if routing unclear
        target_agent = code_expert
        event_bus.emit(EventType.HANDOFF, {
            "from_agent": "Supervisor",
            "to_agent": "CodeExpert",
            "message": "Defaulting to CodeExpert (routing unclear)",
            "timestamp": time.time(),
        })

    # Step 2: Selected specialist handles the task (Handoff)
    await target_agent.run(task)

    event_bus.emit(EventType.AGENT_COMPLETED, {
        "agent": "Orchestrator", "pattern": "sequential + handoff",
        "message": "Task complete", "timestamp": time.time(),
    })


def main():
    event_bus = EventBus(log_dir=LOG_DIR)
    thread = threading.Thread(target=lambda: asyncio.run(run_demo(event_bus)), daemon=True)
    thread.start()
    start_ui(event_bus, topology=TOPOLOGY)


if __name__ == "__main__":
    main()
