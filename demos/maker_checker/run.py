"""
Maker–Checker PR Review — Runner.

Orchestration Pattern: Sequential (SequentialBuilder)
Runs Worker → Reviewer in a loop until APPROVED or max iterations.
"""

import asyncio
import json
import sys
import threading
from pathlib import Path

from shared.events import EventBus
from shared.ui.server import start_ui
from demos.maker_checker.agents import create_agents
from shared.runtime.orchestrations import run_sequential

TOPOLOGY = json.loads((Path(__file__).parent / "topology.json").read_text())
LOG_DIR = str(Path(__file__).parent / "runs")

INPUT_PROMPT = """\
Review this PR diff:
```python
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price'] * item['qty']
    return total
```
The function calculates order total. Review for correctness, edge cases, and improvements.
"""

MAX_ITERATIONS = 3


async def run_demo(event_bus: EventBus, input_text: str | None = None):
    """Run the Maker-Checker demo using Sequential orchestration."""
    agents = create_agents(event_bus)

    # Iteration loop: Sequential Worker→Reviewer, check for APPROVED
    current_input = input_text or INPUT_PROMPT
    for i in range(MAX_ITERATIONS):
        event_bus.emit(
            "agent_started",
            {"agent": "Orchestrator", "pattern": "sequential",
             "message": f"Iteration {i + 1}/{MAX_ITERATIONS}", "timestamp": __import__('time').time()},
        )

        results = await run_sequential(agents, current_input, event_bus=event_bus)

        # Check if reviewer approved
        reviewer_output = ""
        for r in results:
            if r.get("agent") == "Reviewer":
                reviewer_output = r.get("text", "")

        if reviewer_output.strip().upper().startswith("APPROVED"):
            event_bus.emit(
                "agent_completed",
                {"agent": "Orchestrator", "message": f"Approved after {i + 1} iteration(s)",
                 "timestamp": __import__('time').time()},
            )
            break

        # Feed reviewer feedback back as next input
        current_input = f"Reviewer feedback:\n{reviewer_output}\n\nPlease revise your PR review."
    else:
        event_bus.emit(
            "agent_completed",
            {"agent": "Orchestrator", "message": f"Max iterations ({MAX_ITERATIONS}) reached",
             "timestamp": __import__('time').time()},
        )


def main():
    event_bus = EventBus(log_dir=LOG_DIR)

    # Run orchestration in background
    def run_agents():
        asyncio.run(run_demo(event_bus))

    thread = threading.Thread(target=run_agents, daemon=True)
    thread.start()

    # Start UI (blocking)
    start_ui(event_bus, topology=TOPOLOGY)


if __name__ == "__main__":
    main()
