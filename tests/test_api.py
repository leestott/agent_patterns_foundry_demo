"""
Unit tests for the FastAPI application endpoints.

Tests API routes including:
  - GET /api/demos
  - GET /api/topology
  - GET /api/status
  - GET /api/model-config
  - POST /api/model-config
  - GET /api/models/local
  - GET /api/models/azure

Run:
    python -m pytest tests/test_api.py -v
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def _get_test_client():
    """Import app and return a TestClient, patching agent_framework on import."""
    # Patch the startup import check so app.py loads without agent_framework installed
    import importlib
    import types

    # Provide a stub for agent_framework.orchestrations so the import guard passes
    af_stub = types.ModuleType("agent_framework")
    af_stub.orchestrations = types.ModuleType("agent_framework.orchestrations")
    sys.modules.setdefault("agent_framework", af_stub)
    sys.modules.setdefault("agent_framework.orchestrations", af_stub.orchestrations)

    from fastapi.testclient import TestClient
    import app as app_module  # noqa: PLC0415

    return TestClient(app_module.app)


class TestDemosEndpoint(unittest.TestCase):
    """Tests for GET /api/demos."""

    def setUp(self):
        self.client = _get_test_client()

    def test_returns_list(self):
        resp = self.client.get("/api/demos")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_each_demo_has_required_fields(self):
        resp = self.client.get("/api/demos")
        for demo in resp.json():
            with self.subTest(demo=demo.get("id")):
                self.assertIn("id", demo)
                self.assertIn("title", demo)
                self.assertIn("pattern", demo)
                self.assertIn("agents", demo)
                self.assertIn("module", demo)

    def test_all_seven_demos_present(self):
        resp = self.client.get("/api/demos")
        ids = {d["id"] for d in resp.json()}
        expected = {
            "maker_checker", "hierarchical_research", "handoff_support",
            "network_brainstorm", "supervisor_router", "swarm_auditor", "magentic_one",
        }
        self.assertEqual(ids, expected)


class TestStatusEndpoint(unittest.TestCase):
    """Tests for GET /api/status."""

    def setUp(self):
        self.client = _get_test_client()

    def test_returns_status_fields(self):
        resp = self.client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("demo_id", data)
        self.assertIn("running", data)
        self.assertIsInstance(data["running"], bool)


class TestTopologyEndpoint(unittest.TestCase):
    """Tests for GET /api/topology."""

    def setUp(self):
        self.client = _get_test_client()

    def test_returns_dict(self):
        resp = self.client.get("/api/topology")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), dict)


class TestModelConfigEndpoint(unittest.TestCase):
    """Tests for GET and POST /api/model-config."""

    def setUp(self):
        self.client = _get_test_client()

    def test_get_returns_provider_and_sections(self):
        with patch("shared.runtime.model_config._list_local_models", return_value=["phi-4"]):
            resp = self.client.get("/api/model-config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("provider", data)
        self.assertIn("foundry_local", data)
        self.assertIn("azure_foundry", data)

    def test_post_valid_provider_change(self):
        with patch("shared.runtime.model_config._set_env"), \
             patch("shared.runtime.foundry_client.reset_foundry_endpoint"), \
             patch("shared.runtime.model_config._list_local_models", return_value=[]):
            resp = self.client.post(
                "/api/model-config",
                json={"provider": "foundry_local", "foundry_local": {}, "azure_foundry": {}},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["provider"], "foundry_local")

    def test_post_invalid_provider_returns_400(self):
        resp = self.client.post("/api/model-config", json={"provider": "bad_provider"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())

    def test_post_bad_json_returns_400(self):
        resp = self.client.post(
            "/api/model-config",
            content="not-json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_post_updates_local_model(self):
        with patch("shared.runtime.model_config._set_env"), \
             patch("shared.runtime.foundry_client.reset_foundry_endpoint"), \
             patch("shared.runtime.model_config._list_local_models", return_value=["phi-4"]):
            resp = self.client.post(
                "/api/model-config",
                json={"provider": "foundry_local",
                      "foundry_local": {"model": "phi-4"},
                      "azure_foundry": {}},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["foundry_local"]["model"], "phi-4")


class TestModelsLocalEndpoint(unittest.TestCase):
    """Tests for GET /api/models/local (new model picker endpoint)."""

    def setUp(self):
        self.client = _get_test_client()

    def _fake_model(self, alias, status="catalog"):
        return {
            "alias": alias,
            "id": alias,
            "status": status,
            "device_type": "CPU",
            "file_size_mb": 512,
            "supports_tool_calling": False,
            "publisher": "Test",
            "task": "text-generation",
        }

    def test_returns_models_and_selected(self):
        fake_models = [self._fake_model("qwen2.5-1.5b", "loaded"),
                       self._fake_model("phi-4", "cached")]
        with patch("shared.runtime.model_config._list_local_models_detailed",
                   return_value=fake_models):
            resp = self.client.get("/api/models/local")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("models", data)
        self.assertIn("selected", data)
        self.assertEqual(len(data["models"]), 2)

    def test_model_entry_has_status_field(self):
        fake = [self._fake_model("phi-4", "loaded")]
        with patch("shared.runtime.model_config._list_local_models_detailed",
                   return_value=fake):
            resp = self.client.get("/api/models/local")
        model = resp.json()["models"][0]
        self.assertIn("status", model)
        self.assertEqual(model["status"], "loaded")

    def test_model_entry_has_required_fields(self):
        fake = [self._fake_model("phi-4", "cached")]
        with patch("shared.runtime.model_config._list_local_models_detailed",
                   return_value=fake):
            resp = self.client.get("/api/models/local")
        model = resp.json()["models"][0]
        for field in ("alias", "id", "status", "device_type", "file_size_mb",
                      "supports_tool_calling", "publisher", "task"):
            with self.subTest(field=field):
                self.assertIn(field, model)

    def test_selected_matches_current_config(self):
        fake = [self._fake_model("qwen2.5-1.5b", "loaded")]
        with patch("shared.runtime.model_config._list_local_models_detailed",
                   return_value=fake):
            resp = self.client.get("/api/models/local")
        import app as app_module
        cfg = app_module.get_model_config()
        self.assertEqual(resp.json()["selected"], cfg.local_model)


class TestModelsAzureEndpoint(unittest.TestCase):
    """Tests for GET /api/models/azure (new model picker endpoint)."""

    def setUp(self):
        self.client = _get_test_client()

    def test_returns_error_when_not_configured(self):
        """If endpoint/key are blank, should return graceful error in response body."""
        import app as app_module
        cfg = app_module.get_model_config()
        original_ep = cfg.azure_endpoint
        original_key = cfg.azure_api_key
        cfg.azure_endpoint = ""
        cfg.azure_api_key = ""
        try:
            resp = self.client.get("/api/models/azure")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("error", data)
            self.assertIsInstance(data["models"], list)
        finally:
            cfg.azure_endpoint = original_ep
            cfg.azure_api_key = original_key

    def test_returns_models_list_on_success(self):
        """When endpoint is configured, response is always a well-formed dict."""
        import app as app_module
        cfg = app_module.get_model_config()
        original_ep  = cfg.azure_endpoint
        original_key = cfg.azure_api_key
        cfg.azure_endpoint = "https://fake.services.ai.azure.com"
        cfg.azure_api_key  = "fake-key"
        try:
            resp = self.client.get("/api/models/azure")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            # Whether the live call succeeds or fails gracefully, these keys must exist
            self.assertIn("models",   data)
            self.assertIn("selected", data)
            self.assertIsInstance(data["models"], list)
        finally:
            cfg.azure_endpoint = original_ep
            cfg.azure_api_key  = original_key


class TestRunDemoEndpoint(unittest.TestCase):
    """Tests for POST /api/run/{demo_id}."""

    def setUp(self):
        self.client = _get_test_client()

    def test_unknown_demo_returns_404(self):
        resp = self.client.post("/api/run/nonexistent_demo", json={})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("error", resp.json())

    def test_valid_demo_returns_started(self):
        import threading
        with patch("threading.Thread") as MockThread:
            MockThread.return_value.start = MagicMock()
            MockThread.return_value.is_alive = MagicMock(return_value=True)
            MockThread.return_value.daemon = True
            resp = self.client.post("/api/run/maker_checker", json={"prompt": "test"})
        self.assertIn(resp.status_code, (200,))
        self.assertIn(resp.json()["status"], ("started", "already_running"))


class TestReplayEndpoint(unittest.TestCase):
    """Tests for POST /api/replay — path traversal prevention."""

    def setUp(self):
        self.client = _get_test_client()

    def test_path_outside_demos_rejected(self):
        resp = self.client.post("/api/replay", json={"path": "../../secrets.env"})
        self.assertEqual(resp.status_code, 403)

    def test_path_with_dotdot_rejected(self):
        resp = self.client.post("/api/replay",
                                json={"path": "demos/../../../etc/passwd"})
        self.assertEqual(resp.status_code, 403)

    def test_empty_path_returns_400(self):
        resp = self.client.post("/api/replay", json={"path": ""})
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
