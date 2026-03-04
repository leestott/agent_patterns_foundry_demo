"""
Supervisor Router — Runner.

Orchestration Pattern: Handoff (HandoffBuilder)

Flow: Supervisor classifies the task → transfers to CodeExpert, DataExpert, or DocExpert
      via Agent Framework HandoffBuilder autonomous mode.
"""

import asyncio
import json
import threading
from pathlib import Path

from shared.events import EventBus
from shared.ui.server import start_ui
from shared.runtime.orchestrations import run_handoff
from demos.supervisor_router.agents import create_agents

TOPOLOGY = json.loads((Path(__file__).parent / "topology.json").read_text())
LOG_DIR = str(Path(__file__).parent / "runs")

TASK_INPUT = "Write a Python function that reads a CSV file, groups rows by category, and returns the top 3 categories by total revenue. Include docstrings."


async def run_demo(event_bus: EventBus, input_text: str | None = None):
    task = input_text or TASK_INPUT
    supervisor, code_expert, data_expert, doc_expert = create_agents(event_bus)

    await run_handoff(
        agents=[supervisor, code_expert, data_expert, doc_expert],
        input_text=task,
        start_agent=supervisor,
        event_bus=event_bus,
        max_rounds=4,
    )


def main():
    event_bus = EventBus(log_dir=LOG_DIR)
    thread = threading.Thread(target=lambda: asyncio.run(run_demo(event_bus)), daemon=True)
    thread.start()
    start_ui(event_bus, topology=TOPOLOGY)


if __name__ == "__main__":
    main()
