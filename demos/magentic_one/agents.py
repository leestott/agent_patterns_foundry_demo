"""
Magentic One Feasibility Assessment — Agent definitions.

Orchestration Pattern: Magentic One (MagenticBuilder)

Three specialist agents are coordinated by a MagenticManager, which
intelligently decides the order and frequency of agent invocations
rather than using fixed round-robin or handoff rules.
"""

from shared.runtime.foundry_client import get_foundry_client
from shared.runtime.agent_wrapper import create_agent
from shared.events import EventBus


RESEARCHER_INSTRUCTIONS = """\
You are a Research Analyst. Your job is to gather relevant facts, background context,
and real-world examples related to the topic at hand.

Focus on:
- Current state of the technology or situation
- Key statistics, trends, or data points
- Notable industry examples or case studies

Keep your findings concise — bullet points preferred. Under 200 words.
Start your response with "RESEARCH FINDINGS:"
"""

STRATEGIST_INSTRUCTIONS = """\
You are a Product Strategist. Given research findings, you define a clear strategy.

Focus on:
- Recommended approach and positioning
- Key differentiators and value propositions
- Short-term (3-month) and long-term (12-month) goals

Be specific and actionable. Under 200 words.
Start your response with "STRATEGY:"
"""

CRITIC_INSTRUCTIONS = """\
You are a Risk Analyst and Devil's Advocate. Given a proposed strategy, identify
what could go wrong and how to mitigate those risks.

Focus on:
- Top 3 risks or failure modes
- Gaps in the strategy
- Mitigation recommendations

Be constructive but rigorous. Under 200 words.
Start your response with "RISK ASSESSMENT:"
"""


def create_agents(event_bus: EventBus):
    """Create and return the three participant agents for the Magentic One demo."""
    client = get_foundry_client()

    researcher = create_agent(client, name="Researcher", instructions=RESEARCHER_INSTRUCTIONS, event_bus=event_bus)
    strategist = create_agent(client, name="Strategist", instructions=STRATEGIST_INSTRUCTIONS, event_bus=event_bus)
    critic = create_agent(client, name="Critic", instructions=CRITIC_INSTRUCTIONS, event_bus=event_bus)

    return [researcher, strategist, critic]
