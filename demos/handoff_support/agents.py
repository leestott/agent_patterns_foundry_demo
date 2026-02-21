"""
Hand-off Customer Support Triage — Agent definitions.

Orchestration Pattern: Handoff (HandoffBuilder)
"""

from shared.runtime.foundry_client import get_foundry_client
from shared.runtime.agent_wrapper import create_agent
from shared.events import EventBus


TRIAGE_INSTRUCTIONS = """\
You are a customer support triage agent. When a customer describes their issue:
1. Classify it as either BILLING or TECH
2. Briefly acknowledge the customer's issue
3. State clearly: "Transferring to [Billing/TechSupport] agent."

For billing issues (refunds, charges, invoices, payments) → transfer to Billing.
For technical issues (errors, setup, connectivity, bugs) → transfer to TechSupport.
"""

BILLING_INSTRUCTIONS = """\
You are a billing support specialist. Handle:
- Refund requests
- Charge explanations
- Payment method updates
- Invoice inquiries

Provide a clear, empathetic resolution. End with "RESOLVED" if the issue is handled.
"""

TECH_SUPPORT_INSTRUCTIONS = """\
You are a technical support specialist. Handle:
- Error troubleshooting
- Setup and configuration help
- Connectivity issues
- Bug reports

Provide step-by-step troubleshooting guidance. End with "RESOLVED" if the issue is handled.
"""


def create_agents(event_bus: EventBus):
    client = get_foundry_client()

    triage = create_agent(client, name="Triage", instructions=TRIAGE_INSTRUCTIONS, event_bus=event_bus)
    billing = create_agent(client, name="Billing", instructions=BILLING_INSTRUCTIONS, event_bus=event_bus)
    tech = create_agent(client, name="TechSupport", instructions=TECH_SUPPORT_INSTRUCTIONS, event_bus=event_bus)

    return triage, billing, tech
