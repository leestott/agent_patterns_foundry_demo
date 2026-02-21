# Demo 5: Supervisor Router

## Orchestration Pattern: **Sequential + Handoff**

> Uses `agent_framework.orchestrations.SequentialBuilder` for the Supervisor's classification step, then `HandoffBuilder` to route to the selected specialist. This is a **Supervisor** architecture where a single agent acts as a classifier/router.

## Scenario & Value
A Supervisor agent receives tasks, classifies them, and routes to the most qualified specialist. Demonstrates **intelligent routing**: the Supervisor makes an explicit selection decision visible in the trace.

## Agent Cast

| Agent | Role | Instructions | Tools | Termination |
|-------|------|-------------|-------|-------------|
| **Supervisor** | Router/Classifier | "Classify the task and select the best specialist." | None | After routing decision |
| **CodeExpert** | Code Specialist | "Handle code generation, debugging, and review tasks." | None | After response |
| **DataExpert** | Data Specialist | "Handle data analysis, SQL queries, and visualization tasks." | None | After response |
| **DocExpert** | Documentation Specialist | "Handle documentation writing, editing, and structure tasks." | None | After response |

## Run
```bash
python -m demos.supervisor_router.run
```
