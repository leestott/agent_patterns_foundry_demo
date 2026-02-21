# Demo 4: Network Brainstorm (Peer Group Chat)

## Orchestration Pattern: **Group Chat** (GroupChatBuilder)

> Uses `agent_framework.orchestrations.GroupChatBuilder`: 4 peer agents collaborate in a shared conversation thread. The orchestrator manages turn-taking across the group. This is a **Network/Peer** architecture.

## Scenario & Value
Four peers with different perspectives brainstorm ideas collaboratively. Each agent sees the full conversation and builds on others' ideas. Demonstrates **group chat** dynamics, essential for creative collaboration, committee review, and multi-stakeholder discussions.

## Agent Cast

| Agent | Role | Instructions | Tools | Termination |
|-------|------|-------------|-------|-------------|
| **Innovator** | Creative Thinker | "Propose bold, unconventional ideas. Build on others' suggestions." | None | After 2 turns |
| **Pragmatist** | Practical Evaluator | "Evaluate feasibility. Suggest practical implementations." | None | After 2 turns |
| **Devil's Advocate** | Critic | "Challenge assumptions. Identify risks and weaknesses." | None | After 2 turns |
| **Synthesizer** | Integrator | "Find common ground. Synthesize the best elements into a plan." | None | After summary |

## Run
```bash
python -m demos.network_brainstorm.run
```
