# Demo 1: Maker–Checker PR Review

## Orchestration Pattern: **Sequential**

> Uses `agent_framework.orchestrations.SequentialBuilder`: the Worker agent produces output first, then the Reviewer agent critiques it, then the Worker revises. This is a **Sequential** pipeline with a review loop.

## Scenario & Value
A Worker agent drafts a code review response. A Reviewer agent critiques it against a rubric. The Worker then revises based on feedback. This demonstrates the **Maker-Checker** architecture pattern, essential for quality gates in agentic workflows.

## Agent Cast

| Agent | Role | Instructions | Tools | Termination |
|-------|------|-------------|-------|-------------|
| **Worker** | Drafter | "You are a senior developer. Draft a concise PR review addressing code quality, bugs, and suggestions." | None | After revision pass |
| **Reviewer** | Critic | "You are a code review lead. Critique the draft against: correctness, clarity, actionability. Score 1-5." | None | Score ≥ 4 |

## Visual Topology
Tight loop between two nodes with a "review gate" edge. See `topology.json`.

## Run
```bash
cd agentpatterns
python -m demos.maker_checker.run
# Open http://localhost:8765
```

## Demo Script (2-3 min)
1. **Show**: Graph with Worker ↔ Reviewer loop
2. **Run**: Worker drafts review → Reviewer scores 2/5 → Worker revises → Reviewer scores 4/5 → Done
3. **Highlight**: The review gate edge animates on each pass; timeline shows iteration count
