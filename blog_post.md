# Building with Multi-Agent AI: A Visual Guide to Agent Orchestration Patterns

*A hands-on introduction for developers new to agentic AI systems*

---

## Why Agent Patterns Matter

You've probably heard the phrase "multi-agent AI" thrown around a lot lately. But what does it actually *look* like when multiple AI agents collaborate to solve a problem? How do they hand off work to each other? How do you spot a bottleneck? How do you know if the system is actually doing what you designed it to do?

The **Agent Patterns Demo Pack** answers these questions visually and interactively. It gives you six runnable demonstrations, each a different collaboration pattern, with a web UI that lets you watch each agent think, communicate, and hand off in real time.

This post walks you through the app, what each demo teaches, and how to get started in under five minutes.

---

## What Is the Agent Patterns Demo Pack?

The Demo Pack is an open-source, self-contained Python web application that showcases **six common multi-agent orchestration patterns** built with:

- **[Microsoft Agent Framework](https://github.com/microsoft/agent-framework)**: the orchestration engine that wires agents together using patterns like Sequential, Concurrent, Handoff, and Group Chat
- **[Foundry Local](https://www.foundrylocal.ai/)**: Microsoft's on-device model runtime, so everything runs on your laptop without API keys or cloud costs
- **[Microsoft Foundry](https://ai.azure.com/)**: optionally swap in a cloud model for higher-capability tasks, with a single `.env` change
- **FastAPI + WebSocket + D3.js**: a live dashboard that animates agent interactions as they happen

The goal is not to build a production app, but to help you *see* and *understand* how agents work together at a structural level, so you can apply those patterns in your own projects.

---

## Getting Started in 5 Minutes

### Prerequisites

- Python 3.10 or later
- [Foundry Local](https://www.foundrylocal.ai/) installed (free, runs local models on-device)

```bash
# Windows — install Foundry Local
winget install Microsoft.FoundryLocal

# Pull a small, fast model (this is all you need for local runs)
foundry model run qwen2.5-1.5b
```

### Install and Launch

```bash
# Clone the repo and create a virtual environment
git clone https://github.com/leestott/agentpatterns
cd agentpatterns
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

# Start the web app
python app.py
```

Open **http://localhost:8765** in your browser. That is it; you will see the launcher:

![Launcher showing all six demo cards](screenshots/01_launcher.png)

Each card shows the pattern name, a one-line description, and the agents involved. Click any card to start that demo and open its live dashboard.

---

## Navigating the Dashboard

Every demo shares the same three-panel dashboard:

| Panel | What It Shows |
|-------|--------------|
| **Graph** | Force-directed graph: nodes are agents, edges are interaction routes. The active agent animates as it runs. Zoom in/out with the +/- controls. |
| **Stream** | Live messages arriving in real time as agents communicate, each labelled with the sending agent's name |
| **Timeline** | Chronological trace of every event (agent started, message sent, handoff, output) with expandable detail |

To re-run a demo, hit **Re-run** in the header. To go back to the launcher, hit **← All Demos**.

You can also **load a saved run**: every execution is logged to `demos/<demo_id>/runs/run_<timestamp>.jsonl` and you can replay the animation without needing the model running.

---

## The Six Patterns: What You Will Learn

### 1. Maker-Checker (Sequential loop with a quality gate)

![Maker-Checker dashboard](screenshots/03_maker_checker_dashboard.png)

**The pattern:** A Worker drafts output. A Reviewer critiques it and assigns a score. If the score is below threshold, the Worker revises. Loop until quality passes.

**What you'll learn:**
- How to implement a quality gate in an agentic workflow
- Why sequential loops are the right tool for iterative refinement
- How to visualise revision cycles in the graph (the edge between Worker and Reviewer animates on each pass)
- How to use `SequentialBuilder` from Microsoft Agent Framework

**Real-world use:** Code review automation, document drafting, compliance checking, any workflow needing an approval step.

---

### 2. Hierarchical Research (Concurrent fan-out + sequential synthesis)

![Hierarchical Research dashboard](screenshots/04_hierarchical_research_dashboard.png)

**The pattern:** A Manager agent decomposes a research question into sub-tasks. Two Specialist agents run *in parallel*, each researching a different angle. A Synthesizer merges their findings into a final report.

**What you'll learn:**
- How concurrent fan-out dramatically reduces wall-clock time for parallel-safe tasks
- The difference between `ConcurrentBuilder` (parallel) and `SequentialBuilder` (serial)
- How a hierarchical manager–worker structure maps to a real team
- How to combine two orchestration builders in one pipeline

**Real-world use:** Market research, technical due diligence, multi-source data aggregation.

---

### 3. Hand-off Customer Support (Explicit control transfer)

![Handoff Support dashboard](screenshots/05_handoff_support_dashboard.png)

**The pattern:** A Triage agent receives a customer query, classifies it as BILLING or TECH, then *explicitly hands off* to the correct specialist. The specialist resolves the issue and the conversation ends.

**What you'll learn:**
- What a handoff event looks like in the trace; the green edge animation shows control transferring
- How `HandoffBuilder` enables clean routing without a centrally managed loop
- Why explicit handoffs are better than passing context as text in escalation workflows
- How to design triage logic as its own agent rather than control flow

**Real-world use:** Helpdesk automation, HR query routing, escalation pipelines.

---

### 4. Network Brainstorm (Peer group chat)

![Network Brainstorm dashboard](screenshots/06_network_brainstorm_dashboard.png)

**The pattern:** Four peer agents (Innovator, Pragmatist, Devil's Advocate, and Synthesizer) share a single conversation thread. Each sees everything the others say and builds on it. The orchestrator manages turn-taking.

**What you'll learn:**
- How group chat differs from sequential pipelines: all agents are equal peers
- How to use `GroupChatBuilder` and control how many turns each agent takes
- How emergent consensus develops across multiple agents with different "personalities"
- Why this pattern works well for brainstorming but poorly for tasks requiring strict ordering

**Real-world use:** Idea generation, committee review, adversarial red-teaming, design critique.

---

### 5. Supervisor Router (Classification + routing)

![Supervisor Router dashboard](screenshots/07_supervisor_router_dashboard.png)

**The pattern:** A Supervisor agent receives a task, classifies it into a category (Code, Data, or Docs), and routes to the most qualified specialist. The routing decision is visible in the trace.

**What you'll learn:**
- The Supervisor pattern as a building block for any multi-skill agent system
- How combining `SequentialBuilder` (classification step) with `HandoffBuilder` (routing) gives you a clean separation of concerns
- How to make routing decisions transparent: the timeline shows exactly what the Supervisor decided and why
- Why a dedicated Supervisor is better than baking routing logic into every agent

**Real-world use:** Task dispatching, intent classification, tool selection, API routing.

---

### 6. Swarm + Auditor (Parallel generation + sequential evaluation)

![Swarm + Auditor dashboard](screenshots/08_swarm_auditor_dashboard.png)

**The pattern:** Three Generator agents run concurrently, each producing a proposal from a different angle (creative, practical, risk-averse). An Auditor then scores all proposals. A Selector picks the winner based on scores.

**What you'll learn:**
- How to separate *generation* from *evaluation*, a key principle in reliable agentic systems
- How concurrent swarm generation followed by sequential auditing gives you diversity *and* quality control
- How to compose two `ConcurrentBuilder` stages into a coherent pipeline
- How auditor-based selection compares to simply asking one agent to "pick the best"

**Real-world use:** A/B content generation, solution exploration, risk scoring, automated tenders.

---

## Switching to a Cloud Model

When you want higher-capability responses (longer reasoning chains, larger context, better instruction following), you can switch to **Microsoft Foundry** with a single change to `.env`:

```bash
# .env
MODEL_PROVIDER=azure_foundry
AZURE_FOUNDRY_ENDPOINT=https://<your-project>.openai.azure.com/
AZURE_FOUNDRY_API_KEY=<your-key>
AZURE_FOUNDRY_MODEL=gpt-4o-mini   # or model-router, gpt-4o, etc.
```

Restart `app.py` and all demos now use Azure. The model settings panel in the launcher (click the gear icon ⚙) reflects the active provider live, so you always know which model is running.

No code changes: the `ModelConfig` singleton reads from `.env` once at startup and all demos call the same `get_foundry_client()` function.

---

## What's in the Code

For developers who want to go beyond clicking buttons, here's the architecture at a glance:

```
agentpatterns/
├── app.py                          # FastAPI + WebSocket server (start here)
├── shared/
│   ├── runtime/
│   │   ├── foundry_client.py       # Routes to Foundry Local or Microsoft Foundry
│   │   ├── model_config.py         # Provider config singleton (reads .env)
│   │   ├── agent_wrapper.py        # Wraps agents to emit trace events
│   │   └── orchestrations.py       # Pattern helpers using AF orchestration builders
│   ├── events/
│   │   ├── event_types.py          # Event type definitions (agent_started, handoff, etc.)
│   │   └── event_bus.py            # In-process pub/sub + WebSocket bridge + JSONL logger
│   └── ui/static/
│       ├── launcher.html / dashboard.html
│       ├── graph.js                # D3.js force-directed graph with zoom
│       ├── timeline.js / stream.js / dashboard.js
│       └── styles.css
└── demos/
    ├── maker_checker/              # agents.py + run.py + topology.json
    ├── hierarchical_research/
    ├── handoff_support/
    ├── network_brainstorm/
    ├── supervisor_router/
    └── swarm_auditor/
```

Every demo follows the same structure:

- **`agents.py`**: defines the agent cast and wires them together using an AF builder
- **`run.py`**: entry point; wraps the orchestration in the shared runtime
- **`topology.json`**: declares nodes and edges for the graph renderer (no code needed)

To build your own pattern: copy any demo folder, edit `agents.py` to change the agents and builder, update `topology.json` to match, and you're done.

---

## What You'll Take Away

After spending an hour with this demo pack, you'll be able to answer:

- **When do I use Sequential vs Concurrent vs Handoff vs Group Chat?** You'll have seen all four in action and understand the trade-offs.
- **How do I make agent routing explicit and traceable?** The Supervisor Router and Handoff demos show two complementary approaches.
- **How do I add quality gates to agentic pipelines?** The Maker–Checker loop is the template.
- **How do I separate generation from evaluation?** The Swarm + Auditor demo is the answer.
- **How do I move from on-device to cloud?** One `.env` change.

These patterns appear directly in production systems. Recognising these patterns early means you will reach for the right tool instead of reinventing it.

---

## Further Reading

- [Microsoft Agent Framework: Orchestration Patterns](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/)
- [Foundry Local Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/)
- [Foundry Local SDK (PyPI)](https://pypi.org/project/foundry-local-sdk/)
- [Microsoft Foundry](https://ai.azure.com/)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
- [Foundry Local GitHub](https://github.com/microsoft/Foundry-Local)

---

## Quick Reference

| Demo | Pattern | Agents | Builder |
|------|---------|--------|---------|
| Maker-Checker | Sequential loop | 2 | `SequentialBuilder` |
| Hierarchical Research | Concurrent + Sequential | 4 | `ConcurrentBuilder` + `SequentialBuilder` |
| Hand-off Support | Handoff | 3 | `HandoffBuilder` |
| Network Brainstorm | Group Chat | 4 peers | `GroupChatBuilder` |
| Supervisor Router | Sequential + Handoff | 4 | `SequentialBuilder` + `HandoffBuilder` |
| Swarm + Auditor | Concurrent + Sequential | 5 | `ConcurrentBuilder` + `SequentialBuilder` |

---

*Built with Microsoft Agent Framework and Foundry Local. MIT licensed.*
