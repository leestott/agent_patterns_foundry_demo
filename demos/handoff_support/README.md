# Demo 3: Hand-off Customer Support Triage

## Orchestration Pattern: **Handoff** (HandoffBuilder)

> Uses `agent_framework.orchestrations.HandoffBuilder`: the Triage agent classifies the issue and explicitly hands off control to either the Billing agent or the Tech Support agent. Shows explicit `handoff` events in the trace.

## Scenario & Value
A Triage agent receives a customer query, classifies it, and hands off to the appropriate specialist. Demonstrates **agent-to-agent control transfer**, critical for support, routing, and escalation workflows.

## Agent Cast

| Agent | Role | Instructions | Tools | Termination |
|-------|------|-------------|-------|-------------|
| **Triage** | Classifier | "Classify customer issue as BILLING or TECH. Hand off to the right specialist." | None | After handoff |
| **Billing** | Billing Specialist | "Handle billing inquiries: refunds, charges, payment methods." | None | After resolution |
| **TechSupport** | Tech Specialist | "Handle technical issues: connectivity, errors, setup." | None | After resolution |

## Run
```bash
python -m demos.handoff_support.run
```
