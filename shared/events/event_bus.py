"""
In-process event bus with WebSocket bridge for live UI updates.

Supports:
- Synchronous in-process pub/sub (for agent instrumentation)
- Async WebSocket broadcasting (for the UI server)
- JSONL logging for replay
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Callable

from shared.events.event_types import EventType


class EventBus:
    """Pub/sub event bus with WebSocket bridge and JSONL logging."""

    def __init__(self, log_dir: str | None = None):
        self._subscribers: list[Callable] = []
        self._ws_clients: set[Any] = set()
        self._events: list[dict] = []
        self._log_path: Path | None = None

        if log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            self._log_path = log_path / f"run_{ts}.jsonl"

    def subscribe(self, callback: Callable):
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        self._subscribers.remove(callback)

    def register_ws(self, ws):
        self._ws_clients.add(ws)

    def unregister_ws(self, ws):
        self._ws_clients.discard(ws)

    def emit(self, event_type: EventType | str, data: dict):
        type_str = event_type.value if isinstance(event_type, EventType) else str(event_type)
        event = {
            "type": type_str,
            "data": data,
            "seq": len(self._events),
            "timestamp": data.get("timestamp", time.time()),
        }
        self._events.append(event)

        # Log to JSONL
        if self._log_path:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")

        # Notify in-process subscribers
        for cb in self._subscribers:
            try:
                cb(event)
            except Exception:
                pass

        # Broadcast to WebSocket clients (fire-and-forget)
        if self._ws_clients:
            msg = json.dumps(event)
            disconnected = set()
            for ws in self._ws_clients:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(ws.send_text(msg))
                    else:
                        loop.run_until_complete(ws.send_text(msg))
                except Exception:
                    disconnected.add(ws)
            self._ws_clients -= disconnected

    def get_events(self) -> list[dict]:
        return list(self._events)

    def clear(self):
        self._events.clear()

    @property
    def log_path(self) -> str | None:
        return str(self._log_path) if self._log_path else None

    @staticmethod
    def load_replay(jsonl_path: str) -> list[dict]:
        events = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events
