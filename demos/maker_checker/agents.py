"""
Maker–Checker PR Review — Agent definitions.

Orchestration Pattern: Sequential (SequentialBuilder)
"""

from shared.runtime.foundry_client import get_foundry_client
from shared.runtime.agent_wrapper import create_agent
from shared.events import EventBus

WORKER_INSTRUCTIONS = """\
You are a senior software developer performing a PR code review.
Draft a concise, actionable review covering:
- Correctness: any bugs or logic errors
- Clarity: readability and naming
- Suggestions: concrete improvements

If you receive reviewer feedback, revise your review to address every point raised.
Keep the review under 200 words.
"""

REVIEWER_INSTRUCTIONS = """\
You are a code review lead. Evaluate the draft PR review against this rubric:
1. Correctness — does it identify real issues? (1-5)
2. Clarity — is the feedback clear and specific? (1-5)
3. Actionability — can the author act on it? (1-5)

Provide an overall score (average) and specific feedback.
If the overall score is 4 or above, respond with "APPROVED" at the start.
Otherwise, list what needs improvement.
"""


def create_agents(event_bus: EventBus):
    client = get_foundry_client()

    worker = create_agent(
        client,
        name="Worker",
        instructions=WORKER_INSTRUCTIONS,
        event_bus=event_bus,
    )

    reviewer = create_agent(
        client,
        name="Reviewer",
        instructions=REVIEWER_INSTRUCTIONS,
        event_bus=event_bus,
    )

    return [worker, reviewer]
