"""
FastAPI server providing:
- Static file serving for the dashboard UI
- WebSocket endpoint for live event streaming
- REST endpoints for topology, replay, and run control
"""

import os
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from shared.events import EventBus

STATIC_DIR = Path(__file__).parent / "static"


def create_app(event_bus: EventBus, topology: dict | None = None) -> FastAPI:
    app = FastAPI(title="Agent Patterns Visualizer")
    app.state.event_bus = event_bus
    app.state.topology = topology or {}

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    @app.get("/api/topology")
    async def get_topology():
        return JSONResponse(app.state.topology)

    @app.get("/api/events")
    async def get_events():
        return JSONResponse(event_bus.get_events())

    @app.post("/api/replay")
    async def load_replay(body: dict):
        path = body.get("path", "")
        if not path:
            return JSONResponse({"error": "Path required"}, status_code=400)
        replay_path = Path(path).resolve()
        # Restrict to project directory
        project_root = Path(__file__).resolve().parents[2]
        if not replay_path.is_relative_to(project_root):
            return JSONResponse({"error": "Access denied"}, status_code=403)
        if not replay_path.exists() or not replay_path.suffix == ".jsonl":
            return JSONResponse({"error": "File not found"}, status_code=404)
        events = EventBus.load_replay(str(replay_path))
        return JSONResponse(events)

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        event_bus.register_ws(ws)
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            event_bus.unregister_ws(ws)

    return app


def start_ui(event_bus: EventBus, topology: dict | None = None, port: int | None = None):
    """Start the UI server. Call from the demo's run.py."""
    ui_port = port or int(os.getenv("UI_PORT", "8765"))
    app = create_app(event_bus, topology)
    host = os.getenv("HOST", "127.0.0.1")
    print(f"\n  Agent Patterns Visualizer: http://localhost:{ui_port}\n")
    uvicorn.run(app, host=host, port=ui_port, log_level="warning")
