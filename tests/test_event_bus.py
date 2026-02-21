"""
Unit tests for the EventBus.

Run:
    python -m pytest tests/test_event_bus.py -v
or:
    python tests/test_event_bus.py
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from shared.events.event_bus import EventBus
from shared.events.event_types import EventType


class TestEventBus(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()

    def test_emit_adds_event(self):
        self.bus.emit(EventType.AGENT_STARTED, {"agent": "TestAgent"})
        events = self.bus.get_events()
        self.assertEqual(len(events), 1)

    def test_event_has_required_fields(self):
        self.bus.emit(EventType.AGENT_MESSAGE, {"agent": "Worker", "message": "Hello"})
        event = self.bus.get_events()[0]
        self.assertIn("type", event)
        self.assertIn("data", event)
        self.assertIn("seq", event)
        self.assertIn("timestamp", event)

    def test_event_type_is_string(self):
        self.bus.emit(EventType.HANDOFF, {"agent": "Triage", "to": "Billing"})
        event = self.bus.get_events()[0]
        self.assertIsInstance(event["type"], str)
        self.assertEqual(event["type"], "handoff")

    def test_event_type_string_passthrough(self):
        self.bus.emit("custom_event", {"agent": "X"})
        event = self.bus.get_events()[0]
        self.assertEqual(event["type"], "custom_event")

    def test_seq_increments(self):
        for i in range(5):
            self.bus.emit(EventType.AGENT_STARTED, {"agent": f"Agent{i}"})
        events = self.bus.get_events()
        seqs = [e["seq"] for e in events]
        self.assertEqual(seqs, list(range(5)))

    def test_get_events_returns_copy(self):
        self.bus.emit(EventType.AGENT_STARTED, {"agent": "A"})
        events1 = self.bus.get_events()
        self.bus.emit(EventType.AGENT_COMPLETED, {"agent": "A"})
        events2 = self.bus.get_events()
        self.assertEqual(len(events1), 1)
        self.assertEqual(len(events2), 2)

    def test_subscribe_callback_called(self):
        received = []
        self.bus.subscribe(received.append)
        self.bus.emit(EventType.AGENT_MESSAGE, {"agent": "Bot", "message": "hi"})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["type"], "agent_message")

    def test_unsubscribe(self):
        received = []
        self.bus.subscribe(received.append)
        self.bus.unsubscribe(received.append)
        self.bus.emit(EventType.AGENT_STARTED, {"agent": "X"})
        self.assertEqual(len(received), 0)

    def test_clear_empties_events(self):
        self.bus.emit(EventType.AGENT_STARTED, {"agent": "A"})
        self.bus.emit(EventType.AGENT_COMPLETED, {"agent": "A"})
        self.bus.clear()
        self.assertEqual(len(self.bus.get_events()), 0)

    def test_multiple_event_types(self):
        self.bus.emit(EventType.AGENT_STARTED, {"agent": "A"})
        self.bus.emit(EventType.TOOL_CALLED, {"agent": "A", "tool": "search"})
        self.bus.emit(EventType.TOOL_RESULT, {"agent": "A", "result": "done"})
        self.bus.emit(EventType.AGENT_MESSAGE, {"agent": "A", "message": "found it"})
        self.bus.emit(EventType.AGENT_COMPLETED, {"agent": "A"})
        events = self.bus.get_events()
        self.assertEqual(len(events), 5)
        types = [e["type"] for e in events]
        self.assertEqual(types, ["agent_started", "tool_called", "tool_result", "agent_message", "agent_completed"])

    def test_faulty_subscriber_does_not_propagate(self):
        def bad_cb(event):
            raise RuntimeError("subscriber error")

        self.bus.subscribe(bad_cb)
        # Should not raise
        try:
            self.bus.emit(EventType.AGENT_STARTED, {"agent": "X"})
        except RuntimeError:
            self.fail("EventBus propagated subscriber exception")

    def test_load_replay(self):
        import json
        import tempfile
        import os

        events = [
            {"type": "agent_started", "data": {"agent": "A"}, "seq": 0, "timestamp": 1.0},
            {"type": "agent_completed", "data": {"agent": "A"}, "seq": 1, "timestamp": 2.0},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")
            fname = f.name

        try:
            loaded = EventBus.load_replay(fname)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]["type"], "agent_started")
            self.assertEqual(loaded[1]["type"], "agent_completed")
        finally:
            os.unlink(fname)


if __name__ == "__main__":
    unittest.main(verbosity=2)
