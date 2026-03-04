# Demo 7: Magentic One Feasibility Assessment

## Orchestration Pattern: **Magentic One** (MagenticBuilder)

> Uses `agent_framework.orchestrations.MagenticBuilder`: a MagenticManager agent intelligently sequences participant agents — deciding who speaks next and when the task is complete — rather than using fixed round-robin or explicit handoff signals. Based on the [Magentic-One](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/) design.

## Scenario & Value

A multi-perspective feasibility assessment is conducted by three specialists: a Researcher gathers facts, a Strategist proposes an adoption plan, and a Critic stress-tests it. The MagenticManager decides the flow — it may invoke agents in any order, re-invoke them for follow-up, and determines when the task is fully addressed.

Demonstrates how **Magentic One** differs from Group Chat (round-robin) and Handoff (signal-based): the manager uses LLM reasoning to orchestrate, making it suited for open-ended, multi-step tasks.

## Agent Cast

| Agent | Role | Responsibility |
|-------|------|---------------|
| **MagenticManager** | Orchestrator | Coordinates agents; decides order and termination |
| **Researcher** | Information Gathering | Current state, trends, and real-world examples |
| **Strategist** | Strategy Formation | Recommended approach, positioning, and milestones |
| **Critic** | Risk Assessment | Top risks, gaps, and mitigation recommendations |

## Run

```bash
python -m demos.magentic_one.run
```

Opens **http://localhost:8765** with the live agent graph.
