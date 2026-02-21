"""
Agent Patterns Demo Pack — Unified Web Launcher.

Serves a single-page app where users select a demo from cards,
then view the live visualization dashboard for the running demo.
"""

import asyncio
import importlib
import json
import os
import sys
import threading
import traceback
from pathlib import Path

import html as html_mod

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from shared.events import EventBus
from shared.runtime.model_config import get_model_config

# -- Startup sanity check --
try:
    import agent_framework.orchestrations  # noqa: F401
except ModuleNotFoundError:
    _venv = Path(__file__).parent / ".venv"
    print(
        "\n  ERROR: 'agent-framework-orchestrations' package not found.\n"
        "  You are likely running with the system Python instead of the venv.\n\n"
        f"  Activate the virtual-env first:\n"
        f"    .venv\\Scripts\\activate   (Windows)\n"
        f"    source .venv/bin/activate  (macOS/Linux)\n\n"
        f"  Or run directly:\n"
        f"    .venv\\Scripts\\python app.py\n"
    )
    sys.exit(1)

DEMOS_DIR = Path(__file__).parent / "demos"
STATIC_DIR = Path(__file__).parent / "shared" / "ui" / "static"

# Registry of available demos
DEMO_REGISTRY = [
    {
        "id": "maker_checker",
        "title": "Maker-Checker PR Review",
        "pattern": "sequential",
        "description": "Worker drafts a PR review, Reviewer approves or requests changes. Iterates up to 3 rounds.",
        "agents": ["Worker", "Reviewer"],
        "module": "demos.maker_checker.run",
        "suggested_prompt": "Review this PR diff:\n```python\ndef calculate_total(items):\n    total = 0\n    for item in items:\n        total += item['price'] * item['qty']\n    return total\n```\nThe function calculates order total. Review for correctness, edge cases, and improvements.",
    },
    {
        "id": "hierarchical_research",
        "title": "Hierarchical Research Brief",
        "pattern": "concurrent + sequential",
        "description": "Manager decomposes a topic, specialists research in parallel, synthesizer merges findings.",
        "agents": ["Manager", "Specialist_A", "Specialist_B", "Synthesizer"],
        "module": "demos.hierarchical_research.run",
        "suggested_prompt": "The potential of on-device AI models (like Foundry Local) for enterprise applications",
    },
    {
        "id": "handoff_support",
        "title": "Hand-off Customer Support",
        "pattern": "handoff",
        "description": "Triage agent classifies a customer query, then hands off to Billing or TechSupport.",
        "agents": ["Triage", "Billing", "TechSupport"],
        "module": "demos.handoff_support.run",
        "suggested_prompt": "I was charged twice for my subscription last month and I can't access the admin dashboard. Can you help?",
    },
    {
        "id": "network_brainstorm",
        "title": "Network Brainstorm",
        "pattern": "group chat",
        "description": "Four peers collaborate in a shared conversation: Innovator, Pragmatist, Devil's Advocate, Synthesizer.",
        "agents": ["Innovator", "Pragmatist", "DevilsAdvocate", "Synthesizer"],
        "module": "demos.network_brainstorm.run",
        "suggested_prompt": "How should a mid-size SaaS company adopt on-device AI (like Foundry Local) to improve their product? Consider privacy, latency, cost, and user experience.",
    },
    {
        "id": "supervisor_router",
        "title": "Supervisor Router",
        "pattern": "sequential + handoff",
        "description": "Supervisor classifies the task type, then routes to a specialist: Code, Data, or Docs.",
        "agents": ["Supervisor", "CodeExpert", "DataExpert", "DocExpert"],
        "module": "demos.supervisor_router.run",
        "suggested_prompt": "Write a Python function that reads a CSV file, groups rows by category, and returns the top 3 categories by total revenue. Include docstrings.",
    },
    {
        "id": "swarm_auditor",
        "title": "Swarm + Auditor",
        "pattern": "concurrent + sequential",
        "description": "Three generators brainstorm in parallel, Auditor scores proposals, Selector picks the winner.",
        "agents": ["Generator_A", "Generator_B", "Generator_C", "Auditor", "Selector"],
        "module": "demos.swarm_auditor.run",
        "suggested_prompt": "Our mid-size SaaS company wants to reduce cloud infrastructure costs by 40% while maintaining 99.9% uptime and improving developer velocity. What should we do?",
    },
]

# Global state for the currently running demo
_current_demo_id: str | None = None
_current_event_bus: EventBus | None = None
_current_topology: dict | None = None
_demo_thread: threading.Thread | None = None


def _load_topology(demo_id: str) -> dict:
    topo_path = DEMOS_DIR / demo_id / "topology.json"
    if topo_path.exists():
        return json.loads(topo_path.read_text(encoding="utf-8"))
    return {}


def _run_demo_in_thread(demo_id: str, event_bus: EventBus, prompt: str | None = None):
    """Import and run the demo's run_demo coroutine."""
    demo_info = next((d for d in DEMO_REGISTRY if d["id"] == demo_id), None)
    if not demo_info:
        return
    try:
        mod = importlib.import_module(demo_info["module"])
        asyncio.run(mod.run_demo(event_bus, input_text=prompt))
    except Exception:
        tb = traceback.format_exc()
        event_bus.emit("error", {
            "agent": "System",
            "error": tb,
            "message": f"Demo crashed: {tb.splitlines()[-1]}",
        })


app = FastAPI(title="Agent Patterns Demo Pack")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def launcher_page():
    return (Path(__file__).parent / "shared" / "ui" / "static" / "launcher.html").read_text(encoding="utf-8")


@app.get("/demo/{demo_id}", response_class=HTMLResponse)
async def demo_page(demo_id: str):
    # Validate demo_id against known demos to prevent path traversal
    demo_info = next((d for d in DEMO_REGISTRY if d["id"] == demo_id), None)
    if not demo_info:
        return HTMLResponse("<h1>Demo not found</h1>", status_code=404)
    template = (STATIC_DIR / "dashboard.html").read_text(encoding="utf-8")
    # Inject suggested prompt so the textarea is pre-filled on load
    suggested = html_mod.escape(demo_info.get("suggested_prompt", ""))
    template = template.replace(
        'id="prompt-input" placeholder=',
        f'id="prompt-input" placeholder=',
    )
    template = template.replace(
        '</textarea>\n        <button id="btn-send"',
        f'{suggested}</textarea>\n        <button id="btn-send"',
    )
    return HTMLResponse(template)


@app.get("/api/demos")
async def list_demos():
    return JSONResponse(DEMO_REGISTRY)


@app.get("/api/topology")
async def get_topology():
    return JSONResponse(_current_topology or {})


@app.get("/api/events")
async def get_events():
    if _current_event_bus:
        return JSONResponse(_current_event_bus.get_events())
    return JSONResponse([])


@app.get("/api/status")
async def get_status():
    running = _demo_thread is not None and _demo_thread.is_alive()
    return JSONResponse({
        "demo_id": _current_demo_id,
        "running": running,
    })


@app.post("/api/run/{demo_id}")
async def run_demo_endpoint(demo_id: str, body: dict | None = None):
    global _current_demo_id, _current_event_bus, _current_topology, _demo_thread

    # Validate demo exists
    demo_info = next((d for d in DEMO_REGISTRY if d["id"] == demo_id), None)
    if not demo_info:
        return JSONResponse({"error": "Unknown demo"}, status_code=404)

    # Extract optional prompt from request body
    prompt = None
    if body and isinstance(body.get("prompt"), str):
        prompt = body["prompt"].strip() or None

    # If same demo is already running, return current status
    if _current_demo_id == demo_id and _demo_thread and _demo_thread.is_alive():
        return JSONResponse({"status": "already_running", "demo_id": demo_id})

    # Stop previous demo (event bus clear)
    if _current_event_bus:
        _current_event_bus.clear()

    # Set up new demo
    log_dir = str(DEMOS_DIR / demo_id / "runs")
    _current_event_bus = EventBus(log_dir=log_dir)
    _current_topology = _load_topology(demo_id)
    _current_demo_id = demo_id

    # Re-register existing WebSocket clients
    for ws in list(_ws_clients):
        _current_event_bus.register_ws(ws)

    # Start demo in background thread
    _demo_thread = threading.Thread(
        target=_run_demo_in_thread,
        args=(demo_id, _current_event_bus, prompt),
        daemon=True,
    )
    _demo_thread.start()

    return JSONResponse({"status": "started", "demo_id": demo_id})


@app.post("/api/replay")
async def load_replay(body: dict):
    path = body.get("path", "")
    if not path:
        return JSONResponse({"error": "Path required"}, status_code=400)
    # Restrict replay files to the demos/*/runs/ directories
    replay_path = Path(path).resolve()
    allowed_root = DEMOS_DIR.resolve()
    if not replay_path.is_relative_to(allowed_root):
        return JSONResponse({"error": "Access denied"}, status_code=403)
    if not replay_path.exists() or not replay_path.suffix == ".jsonl":
        return JSONResponse({"error": "File not found"}, status_code=404)
    events = EventBus.load_replay(str(replay_path))
    return JSONResponse(events)


@app.post("/api/stop")
async def stop_demo():
    global _current_demo_id, _current_event_bus, _current_topology, _demo_thread
    _current_demo_id = None
    if _current_event_bus:
        _current_event_bus.clear()
    _current_event_bus = None
    _current_topology = None
    _demo_thread = None
    return JSONResponse({"status": "stopped"})


@app.get("/api/model-config")
async def get_model_config_endpoint():
    return JSONResponse(get_model_config().to_dict())


@app.post("/api/model-config")
async def update_model_config_endpoint(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    try:
        get_model_config().update(data)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return JSONResponse(get_model_config().to_dict())


# WebSocket management
_ws_clients: set = set()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _ws_clients.add(ws)
    if _current_event_bus:
        _current_event_bus.register_ws(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(ws)
        if _current_event_bus:
            _current_event_bus.unregister_ws(ws)


if __name__ == "__main__":
    port = int(os.getenv("UI_PORT", "8765"))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"\n  Agent Patterns Demo Pack: http://localhost:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")
