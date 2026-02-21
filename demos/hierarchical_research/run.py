"""
Hierarchical Research Brief — Runner.

Orchestration Patterns:
  - Concurrent (ConcurrentBuilder) — specialists research in parallel
  - Sequential (SequentialBuilder) — synthesizer merges results

Flow: Manager → [Specialist_A || Specialist_B] → Synthesizer
"""

import asyncio
import json
import threading
import time
from pathlib import Path

from shared.events import EventBus, EventType
from shared.ui.server import start_ui
from shared.runtime.orchestrations import run_concurrent, run_sequential
from demos.hierarchical_research.agents import (
    create_manager, create_specialists, create_synthesizer,
)

TOPOLOGY = json.loads((Path(__file__).parent / "topology.json").read_text())
LOG_DIR = str(Path(__file__).parent / "runs")

INPUT_TOPIC = "The potential of on-device AI models (like Foundry Local) for enterprise applications"


async def run_demo(event_bus: EventBus, input_text: str | None = None):
    topic = input_text or INPUT_TOPIC
    manager = create_manager(event_bus)
    specialists = create_specialists(event_bus)
    synthesizer = create_synthesizer(event_bus)

    # Step 1: Manager decomposes the topic
    event_bus.emit(EventType.AGENT_STARTED, {
        "agent": "Orchestrator", "pattern": "sequential",
        "message": "Phase 1: Manager decomposes topic", "timestamp": time.time(),
    })
    decomposition = await manager.run(f"Decompose this research topic: {topic}")

    # Step 2: Specialists research in parallel (Concurrent)
    event_bus.emit(EventType.AGENT_STARTED, {
        "agent": "Orchestrator", "pattern": "concurrent",
        "message": "Phase 2: Specialists research in parallel", "timestamp": time.time(),
    })
    specialist_results = await run_concurrent(
        specialists,
        f"Research topic context:\n{topic}\n\nManager's decomposition:\n{decomposition}",
        event_bus=event_bus,
    )

    # Step 3: Synthesizer merges (Sequential)
    combined_input = "Specialist reports:\n\n"
    for r in specialist_results:
        combined_input += f"--- {r['agent']} ---\n{r['text']}\n\n"

    event_bus.emit(EventType.AGENT_STARTED, {
        "agent": "Orchestrator", "pattern": "sequential",
        "message": "Phase 3: Synthesizer merges findings", "timestamp": time.time(),
    })
    await synthesizer.run(combined_input)

    event_bus.emit(EventType.AGENT_COMPLETED, {
        "agent": "Orchestrator", "message": "Research brief complete", "timestamp": time.time(),
    })


def main():
    event_bus = EventBus(log_dir=LOG_DIR)
    thread = threading.Thread(target=lambda: asyncio.run(run_demo(event_bus)), daemon=True)
    thread.start()
    start_ui(event_bus, topology=TOPOLOGY)


if __name__ == "__main__":
    main()
