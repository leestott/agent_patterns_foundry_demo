"""
Hand-off Customer Support Triage — Runner.

Orchestration Pattern: Handoff (HandoffBuilder)
Triage classifies → hands off to Billing or TechSupport.
"""

import asyncio
import json
import threading
import time
from pathlib import Path

from shared.events import EventBus, EventType
from shared.ui.server import start_ui
from shared.runtime.orchestrations import run_handoff
from demos.handoff_support.agents import create_agents

TOPOLOGY = json.loads((Path(__file__).parent / "topology.json").read_text())
LOG_DIR = str(Path(__file__).parent / "runs")

CUSTOMER_QUERY = "I was charged twice for my subscription last month and I can't access the admin dashboard. Can you help?"


async def run_demo(event_bus: EventBus, input_text: str | None = None):
    query = input_text or CUSTOMER_QUERY
    triage, billing, tech = create_agents(event_bus)

    event_bus.emit(EventType.AGENT_STARTED, {
        "agent": "Orchestrator", "pattern": "handoff",
        "message": "Customer query received — starting triage",
        "participants": ["Triage", "Billing", "TechSupport"],
        "timestamp": time.time(),
    })

    results = await run_handoff(
        agents=[triage, billing, tech],
        input_text=query,
        start_agent=triage,
        event_bus=event_bus,
    )

    event_bus.emit(EventType.AGENT_COMPLETED, {
        "agent": "Orchestrator", "pattern": "handoff",
        "message": "Support session complete", "timestamp": time.time(),
    })


def main():
    event_bus = EventBus(log_dir=LOG_DIR)
    thread = threading.Thread(target=lambda: asyncio.run(run_demo(event_bus)), daemon=True)
    thread.start()
    start_ui(event_bus, topology=TOPOLOGY)


if __name__ == "__main__":
    main()
