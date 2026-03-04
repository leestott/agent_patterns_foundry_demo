"""
Magentic One Feasibility Assessment — Runner.

Orchestration Pattern: Magentic One (MagenticBuilder)

The MagenticManager intelligently sequences the Researcher, Strategist, and Critic
to produce a comprehensive feasibility assessment. Unlike Group Chat (round-robin),
the manager decides which agent speaks next and when the task is complete.
"""

import asyncio
import json
import threading
from pathlib import Path

from shared.events import EventBus
from shared.ui.server import start_ui
from shared.runtime.orchestrations import run_magentic
from demos.magentic_one.agents import create_agents

TOPOLOGY = json.loads((Path(__file__).parent / "topology.json").read_text())
LOG_DIR = str(Path(__file__).parent / "runs")

TASK_INPUT = (
    "Assess the feasibility of adopting on-device AI models (like Foundry Local) "
    "for a mid-size enterprise. Cover: current state of the technology, a recommended "
    "adoption strategy, and the top risks to watch out for."
)


async def run_demo(event_bus: EventBus, input_text: str | None = None):
    task = input_text or TASK_INPUT
    agents = create_agents(event_bus)

    await run_magentic(
        agents=agents,
        input_text=task,
        event_bus=event_bus,
    )


def main():
    event_bus = EventBus(log_dir=LOG_DIR)
    thread = threading.Thread(target=lambda: asyncio.run(run_demo(event_bus)), daemon=True)
    thread.start()
    start_ui(event_bus, topology=TOPOLOGY)


if __name__ == "__main__":
    main()
