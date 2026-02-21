# Demo Day Checklist

## Pre-Demo Setup

- [ ] Install Foundry Local: `winget install Microsoft.FoundryLocal`
- [ ] Pull a model: `foundry model run qwen2.5-1.5b`
- [ ] Verify Foundry is running: `foundry service status`
- [ ] Create and activate venv: `python -m venv .venv && .venv\Scripts\activate`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env` (auto-detect is usually fine)

## Running the Launcher UI

```bash
python app.py
```

Open **http://localhost:8765**: you will see a card-based launcher to select any demo.

## Running Individual Demos

Each demo can also run standalone:

```bash
python -m demos.maker_checker.run
python -m demos.hierarchical_research.run
python -m demos.handoff_support.run
python -m demos.network_brainstorm.run
python -m demos.supervisor_router.run
python -m demos.swarm_auditor.run
```

## During the Demo

1. Click a demo card → the dashboard opens
2. Watch the D3 agent graph light up as agents activate
3. Point out the **pattern badge** in the header (Sequential, Handoff, etc.)
4. Open the **timeline panel** to show event ordering
5. Click timeline entries to show the **trace detail** panel
6. Hit **Re-run** to restart the same demo live
7. Navigate back with **← All Demos** to switch to another pattern

## Talking Points

- "Each card shows which Agent Framework orchestration pattern it uses"
- "All agents run on-device via Foundry Local by default, no cloud calls required"
- "The graph, timeline, and stream panels update in real time over WebSocket"
- "Events are logged to JSONL files for replay after the demo"

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ConnectionRefusedError` | Ensure Foundry Local is running: `foundry service status` |
| Port already in use | Change `UI_PORT` in `.env` or kill the existing process |
| Model not found | Run `foundry model run qwen2.5-1.5b` to pull and start the model |
| Import errors | Ensure venv is active and `pip install -r requirements.txt` was run |
