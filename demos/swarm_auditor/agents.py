"""
Swarm + Auditor Custom — Agent Definitions.

Orchestration Patterns:
  - Concurrent (ConcurrentBuilder) — Generators brainstorm in parallel
  - Sequential (SequentialBuilder) — Auditor scores, Selector picks winner
"""

from shared.events import EventBus
from shared.runtime.foundry_client import get_foundry_client
from shared.runtime.agent_wrapper import create_agent

GENERATOR_A_INSTRUCTIONS = (
    "You are Generator A — the BOLD thinker. "
    "Given a business challenge, propose ONE creative and ambitious solution. "
    "Be inventive. Take risks. Think big. "
    "Format: start with 'PROPOSAL A:' then describe your solution in 3-5 sentences."
)

GENERATOR_B_INSTRUCTIONS = (
    "You are Generator B — the PRACTICAL thinker. "
    "Given a business challenge, propose ONE pragmatic and cost-effective solution. "
    "Focus on ROI, proven approaches, and quick wins. "
    "Format: start with 'PROPOSAL B:' then describe your solution in 3-5 sentences."
)

GENERATOR_C_INSTRUCTIONS = (
    "You are Generator C — the SAFE thinker. "
    "Given a business challenge, propose ONE low-risk, conservative solution. "
    "Prioritize stability, compliance, and minimal disruption. "
    "Format: start with 'PROPOSAL C:' then describe your solution in 3-5 sentences."
)

AUDITOR_INSTRUCTIONS = (
    "You are the Auditor. You will receive three proposals (A, B, C). "
    "Score each on three criteria (1-10 scale): Feasibility, Impact, Cost-Efficiency. "
    "Format your output as:\n"
    "SCORES:\n"
    "  A: Feasibility=X Impact=Y Cost=Z Total=SUM\n"
    "  B: Feasibility=X Impact=Y Cost=Z Total=SUM\n"
    "  C: Feasibility=X Impact=Y Cost=Z Total=SUM\n"
    "Provide a one-sentence rationale for each score."
)

SELECTOR_INSTRUCTIONS = (
    "You are the Selector. You receive auditor scores for three proposals. "
    "Pick the winning proposal (highest total score). "
    "Format: 'WINNER: [A/B/C]' followed by a short justification."
)


def create_agents(event_bus: EventBus):
    """Create and return all agents for Demo 6."""
    client = get_foundry_client()

    gen_a = create_agent(client, "Generator_A", GENERATOR_A_INSTRUCTIONS, event_bus=event_bus)
    gen_b = create_agent(client, "Generator_B", GENERATOR_B_INSTRUCTIONS, event_bus=event_bus)
    gen_c = create_agent(client, "Generator_C", GENERATOR_C_INSTRUCTIONS, event_bus=event_bus)
    auditor = create_agent(client, "Auditor", AUDITOR_INSTRUCTIONS, event_bus=event_bus)
    selector = create_agent(client, "Selector", SELECTOR_INSTRUCTIONS, event_bus=event_bus)

    return gen_a, gen_b, gen_c, auditor, selector
