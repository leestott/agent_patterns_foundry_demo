"""
Network Brainstorm — Agent definitions.

Orchestration Pattern: Group Chat (GroupChatBuilder)
"""

from shared.runtime.foundry_client import get_foundry_client
from shared.runtime.agent_wrapper import create_agent
from shared.events import EventBus


INNOVATOR_INSTRUCTIONS = """\
You are the Innovator in a brainstorming session. Your role:
- Propose bold, creative, unconventional ideas
- Build on others' suggestions to push boundaries
- Think 10x, not 10%
Keep responses to 100 words. Be specific with proposals.
"""

PRAGMATIST_INSTRUCTIONS = """\
You are the Pragmatist in a brainstorming session. Your role:
- Evaluate ideas for practical feasibility
- Suggest concrete implementation steps
- Estimate effort and resources needed
Keep responses to 100 words. Be constructive.
"""

DEVILS_ADVOCATE_INSTRUCTIONS = """\
You are the Devil's Advocate in a brainstorming session. Your role:
- Challenge assumptions behind proposed ideas
- Identify risks, edge cases, and potential failures
- Ask tough "what if" questions
Keep responses to 100 words. Be respectful but rigorous.
"""

SYNTHESIZER_INSTRUCTIONS = """\
You are the Synthesizer in a brainstorming session. Your role:
- Find common ground across different perspectives
- Combine the best elements into a coherent plan
- Propose a balanced recommendation
Keep responses to 100 words. Wrap up with a clear action item.
"""


def create_agents(event_bus: EventBus):
    client = get_foundry_client()

    innovator = create_agent(client, name="Innovator", instructions=INNOVATOR_INSTRUCTIONS, event_bus=event_bus)
    pragmatist = create_agent(client, name="Pragmatist", instructions=PRAGMATIST_INSTRUCTIONS, event_bus=event_bus)
    devils = create_agent(client, name="DevilsAdvocate", instructions=DEVILS_ADVOCATE_INSTRUCTIONS, event_bus=event_bus)
    synth = create_agent(client, name="Synthesizer", instructions=SYNTHESIZER_INSTRUCTIONS, event_bus=event_bus)

    return [innovator, pragmatist, devils, synth]
