"""
Network Brainstorm — Runner.

Orchestration Pattern: Group Chat (GroupChatBuilder)
4 peers collaborate in a shared conversation thread.
"""

import asyncio
import json
import threading
import time
from pathlib import Path

from shared.events import EventBus, EventType
from shared.ui.server import start_ui
from shared.runtime.orchestrations import run_group_chat
from demos.network_brainstorm.agents import create_agents

TOPOLOGY = json.loads((Path(__file__).parent / "topology.json").read_text())
LOG_DIR = str(Path(__file__).parent / "runs")

BRAINSTORM_TOPIC = "How should a mid-size SaaS company adopt on-device AI (like Foundry Local) to improve their product? Consider privacy, latency, cost, and user experience."


async def run_demo(event_bus: EventBus, input_text: str | None = None):
    topic = input_text or BRAINSTORM_TOPIC
    agents = create_agents(event_bus)

    event_bus.emit(EventType.AGENT_STARTED, {
        "agent": "Orchestrator", "pattern": "group_chat",
        "message": "Brainstorm session starting",
        "participants": [a.name for a in agents],
        "timestamp": time.time(),
    })

    results = await run_group_chat(
        agents=agents,
        input_text=topic,
        event_bus=event_bus,
    )

    event_bus.emit(EventType.AGENT_COMPLETED, {
        "agent": "Orchestrator", "pattern": "group_chat",
        "message": "Brainstorm session complete",
        "timestamp": time.time(),
    })


def main():
    event_bus = EventBus(log_dir=LOG_DIR)
    thread = threading.Thread(target=lambda: asyncio.run(run_demo(event_bus)), daemon=True)
    thread.start()
    start_ui(event_bus, topology=TOPOLOGY)


if __name__ == "__main__":
    main()
