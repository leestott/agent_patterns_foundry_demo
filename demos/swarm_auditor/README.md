# Demo 6: Swarm + Auditor

## Orchestration Pattern: **Concurrent + Sequential**

> Uses `agent_framework.orchestrations.ConcurrentBuilder` for parallel proposal generation, then `SequentialBuilder` for auditing and selection. This combines **swarm diversity** with **structured evaluation**.

## Scenario & Value
Three Generator agents brainstorm proposals from different angles (creative, practical, risk-averse) in parallel. An Auditor scores each proposal, then a Selector picks the winner. This demonstrates how to separate *generation* from *evaluation* — a key principle for reliable agentic systems.

## Agent Cast

| Agent | Role | Instructions | Tools | Termination |
|-------|------|-------------|-------|-------------|
| **Generator_A** | Creative proposer | "Propose bold, creative solutions." | None | After one proposal |
| **Generator_B** | Practical proposer | "Propose cost-effective, practical solutions." | None | After one proposal |
| **Generator_C** | Risk-averse proposer | "Propose safe, risk-averse solutions." | None | After one proposal |
| **Auditor** | Scorer | "Score each proposal on feasibility, impact, and cost." | None | After scoring all |
| **Selector** | Decision maker | "Pick the winning proposal based on auditor scores." | None | After selection |

## Visual Topology
Three parallel generator nodes fan into Auditor, then into Selector. See `topology.json`.

## Run
```bash
cd agentpatterns
python -m demos.swarm_auditor.run
# Open http://localhost:8765
```

## Demo Script (2-3 min)
1. **Show**: Graph with three parallel Generator nodes flowing into Auditor then Selector
2. **Run**: Generators produce three proposals simultaneously -> Auditor scores each -> Selector picks winner
3. **Highlight**: The concurrent phase animates all three generators at once; the timeline shows parallel execution followed by sequential evaluation
