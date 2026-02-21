# Demo 2: Hierarchical Research Brief

## Orchestration Pattern: **Concurrent** (fan-out) + **Sequential** (synthesize)

> Uses `agent_framework.orchestrations.ConcurrentBuilder` for parallel specialist research, then `SequentialBuilder` to feed results into a Synthesizer. This is a **Hierarchical** architecture with a Manager decomposing tasks, specialists running in parallel, and a synthesizer merging.

## Scenario & Value
A Manager agent decomposes a research question into sub-tasks. Two Specialist agents research in parallel (concurrent fan-out). A Synthesizer merges their findings into a final brief. Demonstrates **hierarchical delegation** with parallel execution.

## Agent Cast

| Agent | Role | Instructions | Tools | Termination |
|-------|------|-------------|-------|-------------|
| **Manager** | Task Decomposer | "Decompose the research topic into 2 specific sub-questions." | None | After decomposition |
| **Specialist_A** | Researcher (Technical) | "Research the technical aspects of the given topic." | None | After response |
| **Specialist_B** | Researcher (Market) | "Research the market/business aspects of the given topic." | None | After response |
| **Synthesizer** | Report Writer | "Combine the specialist reports into a cohesive 200-word brief." | None | After synthesis |

## Run
```bash
python -m demos.hierarchical_research.run
```
