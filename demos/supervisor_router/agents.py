"""
Supervisor Router — Agent definitions.

Orchestration Patterns: Sequential (SequentialBuilder) + Handoff (HandoffBuilder)
"""

from shared.runtime.foundry_client import get_foundry_client
from shared.runtime.agent_wrapper import create_agent
from shared.events import EventBus


SUPERVISOR_INSTRUCTIONS = """\
You are a task supervisor. Given a user request, classify it and transfer to the best specialist:
- If it involves writing code, debugging, or code review → transfer to CodeExpert
- If it involves data analysis, SQL, or visualization → transfer to DataExpert
- If it involves documentation, README, or writing → transfer to DocExpert

Briefly acknowledge the task and explain your routing decision in 1-2 sentences.
Then end with exactly one of:
  "Transferring to CodeExpert."
  "Transferring to DataExpert."
  "Transferring to DocExpert."
"""

CODE_EXPERT_INSTRUCTIONS = """\
You are an expert software engineer. Handle tasks involving:
- Code generation and snippets
- Debugging and error analysis
- Code review and best practices

Provide clear, working code with brief explanations. Keep responses under 200 words.
End your response with "TASK COMPLETE."
"""

DATA_EXPERT_INSTRUCTIONS = """\
You are a data analysis expert. Handle tasks involving:
- SQL query writing and optimization
- Data analysis and interpretation
- Visualization recommendations

Provide specific, actionable analysis. Keep responses under 200 words.
End your response with "TASK COMPLETE."
"""

DOC_EXPERT_INSTRUCTIONS = """\
You are a technical writing expert. Handle tasks involving:
- Documentation structure and content
- README files and guides
- API documentation

Write clear, well-structured documentation. Keep responses under 200 words.
End your response with "TASK COMPLETE."
"""


def create_agents(event_bus: EventBus):
    client = get_foundry_client()

    supervisor = create_agent(client, name="Supervisor", instructions=SUPERVISOR_INSTRUCTIONS, event_bus=event_bus)
    code = create_agent(client, name="CodeExpert", instructions=CODE_EXPERT_INSTRUCTIONS, event_bus=event_bus)
    data = create_agent(client, name="DataExpert", instructions=DATA_EXPERT_INSTRUCTIONS, event_bus=event_bus)
    doc = create_agent(client, name="DocExpert", instructions=DOC_EXPERT_INSTRUCTIONS, event_bus=event_bus)

    return supervisor, code, data, doc
