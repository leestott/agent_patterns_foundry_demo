# Agent Patterns Demo Pack — Agent Reference

This document describes every agent across all seven demos, the orchestration pattern each demo uses, and how to configure the model they run on.

---

## Model Configuration

All agents are powered by a single, runtime-switchable model provider. Choose between **Foundry Local** (on-device, no API key) or **Microsoft Foundry** (cloud). Switch providers and models live from the **⚙ Model Settings** panel in the launcher UI without restarting the app.

### Foundry Local (on-device)

Models run entirely on your device. The UI model picker shows every model in three states:

| Status | Meaning |
|--------|---------|
| **Loaded** | Model is currently in memory — fastest start |
| **Cached** | Downloaded to disk, will load in seconds |
| **Available** | In the catalog, will download on first use |

Cards show device type (GPU/CPU), size in MB, tool-calling support, publisher, and task type.

### Microsoft Foundry (cloud)

Enter your Foundry endpoint URL and API key. Click **List Models** to browse your deployed models and click any entry to select it. The **Deployment Name** field is optional — leave blank to use the model name as the deployment identifier.

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/models/local` | Returns catalog models with live `loaded`/`cached`/`catalog` status |
| `GET /api/models/azure` | Lists deployed models from the configured Foundry endpoint |
| `GET /api/model-config` | Current provider, model, and endpoint settings |
| `POST /api/model-config` | Update provider/model settings (persists to `.env`) |

---

## Demo 1 — Maker-Checker PR Review

**Pattern:** Sequential — iterative review loop  
**Builder:** `SequentialBuilder`  
**File:** [demos/maker_checker/agents.py](demos/maker_checker/agents.py)

### Agents

| Agent | Role | Behaviour |
|-------|------|-----------|
| **Worker** | Drafter | "You are a senior developer. Draft a concise PR review addressing code quality, bugs, and suggestions." Produces the initial review. |
| **Reviewer** | Quality gate | "You are a code review lead. Critique the draft against: correctness, clarity, actionability. Score 1-5." If score < 4, Worker revises. |

### Topology

```
Worker ──draft──► Reviewer ──score < 4?──► Worker (revision)
                     │
                  score ≥ 4
                     ▼
                    Done
```

### When to use this pattern

Quality gates, approval steps, iterative document drafting, compliance checking, code review automation. Any task where the first attempt rarely meets the bar and a structured feedback loop improves quality.

---

## Demo 2 — Hierarchical Research Brief

**Pattern:** Concurrent fan-out + Sequential synthesis  
**Builder:** `ConcurrentBuilder` (specialists) + `SequentialBuilder` (synthesis)  
**File:** [demos/hierarchical_research/agents.py](demos/hierarchical_research/agents.py)

### Agents

| Agent | Role | Behaviour |
|-------|------|-----------|
| **Manager** | Decomposer | "Decompose the research topic into 2 specific sub-questions." Produces the task list. |
| **Specialist_A** | Technical researcher | "Research the technical aspects of the given topic." Runs in parallel with Specialist_B. |
| **Specialist_B** | Market researcher | "Research the market/business aspects of the given topic." Runs in parallel with Specialist_A. |
| **Synthesizer** | Report writer | "Combine the specialist reports into a cohesive 200-word brief." Runs after both specialists complete. |

### Topology

```
Manager ──► Specialist_A ──┐
        └──► Specialist_B ──┴──► Synthesizer ──► Done
```

### When to use this pattern

Multi-source research, technical due diligence, market analysis, any task where independent sub-questions can be explored in parallel and merged into a single output.

---

## Demo 3 — Hand-off Customer Support

**Pattern:** Explicit agent-to-agent control transfer  
**Builder:** `HandoffBuilder`  
**File:** [demos/handoff_support/agents.py](demos/handoff_support/agents.py)

### Agents

| Agent | Role | Behaviour |
|-------|------|-----------|
| **Triage** | Classifier | "Classify customer issue as BILLING or TECH. Hand off to the right specialist." Emits a `handoff` event. |
| **Billing** | Billing specialist | "Handle billing inquiries: refunds, charges, payment methods." Receives control from Triage when issue is billing-related. |
| **TechSupport** | Tech specialist | "Handle technical issues: connectivity, errors, setup." Receives control from Triage when issue is technical. |

### Topology

```
Triage ──BILLING──► Billing ──► Done
       └──TECH────► TechSupport ──► Done
```

### When to use this pattern

Helpdesk automation, intent-based routing, HR query routing, escalation pipelines. Use when control must transfer cleanly to a specialist without a shared conversation buffer.

---

## Demo 4 — Network Brainstorm

**Pattern:** Peer group chat — all agents share one conversation thread  
**Builder:** `GroupChatBuilder`  
**File:** [demos/network_brainstorm/agents.py](demos/network_brainstorm/agents.py)

### Agents

| Agent | Role | Behaviour |
|-------|------|-----------|
| **Innovator** | Creative thinker | "Propose bold, unconventional ideas. Build on others' suggestions." |
| **Pragmatist** | Feasibility evaluator | "Evaluate feasibility. Suggest practical implementations." |
| **DevilsAdvocate** | Critic | "Challenge assumptions. Identify risks and weaknesses." |
| **Synthesizer** | Integrator | "Find common ground. Synthesize the best elements into a plan." |

### Topology

```
┌─────────────────────────────────────────────┐
│  Innovator ◄──► Pragmatist                  │
│       ▲              ▲                       │
│       └───────────────┘                     │
│  DevilsAdvocate ◄──► Synthesizer            │
│  (all-to-all shared conversation)           │
└─────────────────────────────────────────────┘
```

### When to use this pattern

Brainstorming, committee review, adversarial red-teaming, design critique. Best suited where emergent consensus is the goal and strict ordering would suppress contributions.

---

## Demo 5 — Supervisor Router

**Pattern:** Classify then route  
**Builder:** `HandoffBuilder` (autonomous mode)  
**File:** [demos/supervisor_router/agents.py](demos/supervisor_router/agents.py)

### Agents

| Agent | Role | Behaviour |
|-------|------|-----------|
| **Supervisor** | Router | "Classify the task and select the best specialist." Emits a `handoff` to the matching expert. |
| **CodeExpert** | Code specialist | "Handle code generation, debugging, and review tasks." |
| **DataExpert** | Data specialist | "Handle data analysis, SQL queries, and visualization tasks." |
| **DocExpert** | Documentation specialist | "Handle documentation writing, editing, and structure tasks." |

### Topology

```
Supervisor ──Code──► CodeExpert ──► Done
           ──Data──► DataExpert ──► Done
           ──Docs──► DocExpert  ──► Done
```

### When to use this pattern

Task dispatching, intent classification, tool selection, multi-skill agent systems. Separating the routing decision (Supervisor) from the execution (specialists) keeps each agent focused.

---

## Demo 6 — Swarm + Auditor

**Pattern:** Concurrent generation + sequential audit + selection  
**Builder:** `ConcurrentBuilder` (generators) + `SequentialBuilder` (audit/select)  
**File:** [demos/swarm_auditor/agents.py](demos/swarm_auditor/agents.py)

### Agents

| Agent | Role | Behaviour |
|-------|------|-----------|
| **Generator_A** | Creative proposer | "Propose bold, creative solutions." Runs concurrently with B and C. |
| **Generator_B** | Practical proposer | "Propose cost-effective, practical solutions." Runs concurrently with A and C. |
| **Generator_C** | Risk-averse proposer | "Propose safe, risk-averse solutions." Runs concurrently with A and B. |
| **Auditor** | Scorer | "Score each proposal on feasibility, impact, and cost." Runs sequentially after all generators. |
| **Selector** | Decision maker | "Pick the winning proposal based on auditor scores." Final sequential step. |

### Topology

```
Generator_A ──┐
Generator_B ──┴──► Auditor ──► Selector ──► Done
Generator_C ──┘
(concurrent)        (sequential evaluation phase)
```

### When to use this pattern

A/B content generation, solution exploration, risk scoring, automated tenders, any scenario where generating diverse options in parallel and then evaluating them systematically yields better outcomes than picking a single path upfront.

---

## Demo 7 — Magentic One Assessment

**Pattern:** Adaptive orchestration — manager decides flow dynamically  
**Builder:** `MagenticBuilder`  
**File:** [demos/magentic_one/agents.py](demos/magentic_one/agents.py)

### Agents

| Agent | Role | Behaviour |
|-------|------|-----------|
| **MagenticManager** | Orchestrator | Reads the conversation state and decides which agent to invoke next, how many times, and when the task is complete. Not a participant in the output. |
| **Researcher** | Information gatherer | "Research the current state, trends, and real-world examples for the given topic." |
| **Strategist** | Strategy former | "Propose a recommended approach, adoption roadmap, and positioning for the given topic." |
| **Critic** | Risk assessor | "Identify the top risks, gaps, and mitigation recommendations." |

### Topology

```
         ┌──► Researcher ──┐
MagenticManager            ├──► MagenticManager (re-evaluates) ──► Done
         ├──► Strategist ──┤
         └──► Critic ──────┘
(dynamic routing — Manager decides order and repetition)
```

### How Magentic One differs from other patterns

| | Group Chat | Handoff | Magentic One |
|-|------------|---------|--------------|
| **Turn order** | Round-robin | Signal-based | LLM-decided |
| **Re-invocation** | Fixed rounds | No | Yes |
| **Termination** | Max rounds | Agent signals | Manager decides |
| **Best for** | Brainstorming | Clean routing | Open-ended tasks |

### When to use this pattern

Strategy assessment, feasibility analysis, research synthesis, open-ended tasks where the required steps, their order, and how many iterations are needed are not known in advance.

---

## Summary Table

| # | Demo | Pattern | Builder | Agents |
|---|------|---------|---------|--------|
| 1 | Maker-Checker PR Review | Sequential loop | `SequentialBuilder` | Worker, Reviewer |
| 2 | Hierarchical Research Brief | Concurrent + Sequential | `ConcurrentBuilder` + `SequentialBuilder` | Manager, Specialist_A, Specialist_B, Synthesizer |
| 3 | Hand-off Customer Support | Handoff | `HandoffBuilder` | Triage, Billing, TechSupport |
| 4 | Network Brainstorm | Group Chat | `GroupChatBuilder` | Innovator, Pragmatist, DevilsAdvocate, Synthesizer |
| 5 | Supervisor Router | Classify + Route | `HandoffBuilder` | Supervisor, CodeExpert, DataExpert, DocExpert |
| 6 | Swarm + Auditor | Concurrent + Sequential | `ConcurrentBuilder` + `SequentialBuilder` | Generator_A, Generator_B, Generator_C, Auditor, Selector |
| 7 | Magentic One Assessment | Adaptive / Magentic | `MagenticBuilder` | MagenticManager, Researcher, Strategist, Critic |

---

## Pattern Decision Guide

```
Does the task have a fixed sequence of steps?
  └── YES → SequentialBuilder
  └── NO  → Can steps run in parallel?
              └── YES → ConcurrentBuilder (+ SequentialBuilder to merge)
              └── NO  → Does it need explicit routing to one specialist?
                          └── YES → HandoffBuilder
                          └── NO  → Are agents peers with equal contribution?
                                      └── YES → GroupChatBuilder
                                      └── NO  → Is the flow open-ended / unknown upfront?
                                                  └── YES → MagenticBuilder
```

---

## Reference

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Foundry Local](https://foundrylocal.ai)
- [Microsoft Foundry](https://ai.azure.com/)
- [Foundry Local SDK (PyPI)](https://pypi.org/project/foundry-local-sdk/)
