# Walkthrough

Step-by-step guide to running and understanding each demo.

---

## Demo 1: Maker-Checker PR Review

**Pattern:** Sequential (`SequentialBuilder`)

1. **Worker** receives a Python function and drafts a code review.
2. **Reviewer** evaluates the review: either approves ("APPROVED") or gives feedback.
3. If not approved, the feedback loops back to the Worker (max 3 iterations).
4. The dashboard shows the sequential Worker → Reviewer edges lighting up each round.

**What to look for:** The iteration count in the timeline, and the "APPROVED" event ending the loop.

---

## Demo 2: Hierarchical Research Brief

**Pattern:** Concurrent + Sequential (`ConcurrentBuilder`, `SequentialBuilder`)

1. **Manager** decomposes a research topic into sub-questions.
2. **Specialist_A** and **Specialist_B** research in parallel (concurrent phase).
3. **Synthesizer** merges both findings into a final brief (sequential phase).

**What to look for:** Two specialist nodes activating simultaneously in the graph.

---

## Demo 3: Hand-off Customer Support

**Pattern:** Handoff (`HandoffBuilder`)

1. **Triage** agent reads the customer query and classifies it.
2. Triage hands off to **Billing** or **TechSupport** based on the classification.
3. The specialist handles the query and responds.

**What to look for:** The handoff event in the timeline, and the edge animation from Triage to the specialist.

---

## Demo 4: Network Brainstorm

**Pattern:** Group Chat (`GroupChatBuilder`)

1. Four peers join a shared conversation:
   - **Innovator**: blue-sky ideas
   - **Pragmatist**: reality check
   - **Devil's Advocate**: pokes holes
   - **Synthesizer**: distils consensus
2. Agents take turns contributing to the discussion.

**What to look for:** All four nodes activating in turn, and the stream panel showing the evolving conversation.

---

## Demo 5: Supervisor Router

**Pattern:** Sequential + Handoff (`SequentialBuilder`, `HandoffBuilder`)

1. **Supervisor** reads the task and classifies it (code / data / documentation).
2. Supervisor emits a "ROUTE: AgentName" decision.
3. The chosen specialist (**CodeExpert**, **DataExpert**, or **DocExpert**) handles the request.

**What to look for:** The handoff event showing which specialist was selected.

---

## Demo 6: Swarm + Auditor

**Pattern:** Concurrent + Sequential (`ConcurrentBuilder`, `SequentialBuilder`)

1. Three generators brainstorm solutions in parallel:
   - **Generator_A**: bold and creative
   - **Generator_B**: practical
   - **Generator_C**: safe and conservative
2. **Auditor** scores all three proposals on feasibility, impact, and cost.
3. **Selector** picks the winning proposal.

**What to look for:** Three generators activating simultaneously, then the sequential audit → select flow.

---

## Using the Launcher UI

Run `python app.py` and open http://localhost:8765.

- **Home page:** Cards for all 6 demos. Click any card to start it and open the dashboard.
- **Dashboard:** Live graph, stream, timeline, and detail panels.
- **Re-run:** Restart the current demo without leaving the page.
- **← All Demos:** Navigate back to the launcher to pick a different demo.
- **Replay:** Load a saved `.jsonl` file to replay a previous run.
