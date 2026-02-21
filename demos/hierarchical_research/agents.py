"""
Hierarchical Research Brief — Agent definitions.

Orchestration Patterns: Concurrent (ConcurrentBuilder) + Sequential (SequentialBuilder)
"""

from shared.runtime.foundry_client import get_foundry_client
from shared.runtime.agent_wrapper import create_agent
from shared.events import EventBus


MANAGER_INSTRUCTIONS = """\
You are a research manager. Given a topic, decompose it into exactly 2 specific sub-questions:
1. A technical/implementation sub-question
2. A market/business sub-question

Output them as a numbered list. Be specific and focused.
"""

SPECIALIST_A_INSTRUCTIONS = """\
You are a technical researcher. Given a research question, provide a concise
150-word analysis covering technical feasibility, key technologies involved,
and implementation considerations. Be specific with facts and examples.
"""

SPECIALIST_B_INSTRUCTIONS = """\
You are a market analyst. Given a research question, provide a concise
150-word analysis covering market size, competition landscape, and business
opportunity. Be specific with data points and trends.
"""

SYNTHESIZER_INSTRUCTIONS = """\
You are a senior analyst who writes executive briefs. Given technical and market
research reports, synthesize them into a cohesive 200-word brief with:
- Key Finding (1 sentence)
- Technical Summary (2-3 sentences)
- Market Summary (2-3 sentences)
- Recommendation (1-2 sentences)
"""


def create_manager(event_bus: EventBus):
    client = get_foundry_client()
    return create_agent(client, name="Manager", instructions=MANAGER_INSTRUCTIONS, event_bus=event_bus)


def create_specialists(event_bus: EventBus):
    client = get_foundry_client()
    spec_a = create_agent(client, name="Specialist_A", instructions=SPECIALIST_A_INSTRUCTIONS, event_bus=event_bus)
    spec_b = create_agent(client, name="Specialist_B", instructions=SPECIALIST_B_INSTRUCTIONS, event_bus=event_bus)
    return [spec_a, spec_b]


def create_synthesizer(event_bus: EventBus):
    client = get_foundry_client()
    return create_agent(client, name="Synthesizer", instructions=SYNTHESIZER_INSTRUCTIONS, event_bus=event_bus)
