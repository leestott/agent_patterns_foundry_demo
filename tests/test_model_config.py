"""
Unit tests for ModelConfig.

Tests defaults, update logic, and provider validation without
requiring a live Foundry Local service (available_models is mocked).

Run:
    python -m pytest tests/test_model_config.py -v
or:
    python tests/test_model_config.py
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


class TestModelConfig(unittest.TestCase):

    def _make_config(self):
        """Return a fresh ModelConfig instance for each test."""
        from shared.runtime.model_config import ModelConfig
        return ModelConfig()

    def test_default_provider_is_foundry_local(self):
        cfg = self._make_config()
        self.assertEqual(cfg.provider, "foundry_local")

    def test_default_azure_model(self):
        cfg = self._make_config()
        self.assertEqual(cfg.azure_model, "gpt-4o-mini")

    def test_to_dict_structure(self):
        cfg = self._make_config()
        with patch("shared.runtime.model_config._list_local_models", return_value=["phi-4"]):
            d = cfg.to_dict()
        self.assertIn("provider", d)
        self.assertIn("foundry_local", d)
        self.assertIn("azure_foundry", d)
        self.assertIn("model", d["foundry_local"])
        self.assertIn("available_models", d["foundry_local"])
        self.assertIn("endpoint", d["azure_foundry"])
        self.assertIn("model", d["azure_foundry"])

    def test_api_key_masked_in_to_dict(self):
        cfg = self._make_config()
        cfg.azure_api_key = "super-secret-key"
        with patch("shared.runtime.model_config._list_local_models", return_value=[]):
            d = cfg.to_dict()
        self.assertEqual(d["azure_foundry"]["api_key"], "***")

    def test_api_key_empty_when_not_set(self):
        cfg = self._make_config()
        cfg.azure_api_key = ""
        with patch("shared.runtime.model_config._list_local_models", return_value=[]):
            d = cfg.to_dict()
        self.assertEqual(d["azure_foundry"]["api_key"], "")

    def test_update_provider(self):
        cfg = self._make_config()
        with patch("shared.runtime.model_config._set_env"), \
             patch("shared.runtime.foundry_client.reset_foundry_endpoint"):
            cfg.update({"provider": "azure_foundry"})
        self.assertEqual(cfg.provider, "azure_foundry")

    def test_update_invalid_provider_raises(self):
        cfg = self._make_config()
        with self.assertRaises(ValueError):
            cfg.update({"provider": "unsupported_provider"})

    def test_update_local_model(self):
        cfg = self._make_config()
        with patch("shared.runtime.model_config._set_env"), \
             patch("shared.runtime.foundry_client.reset_foundry_endpoint"):
            cfg.update({"foundry_local": {"model": "phi-4"}})
        self.assertEqual(cfg.local_model, "phi-4")

    def test_update_azure_fields(self):
        cfg = self._make_config()
        with patch("shared.runtime.model_config._set_env"), \
             patch("shared.runtime.foundry_client.reset_foundry_endpoint"):
            cfg.update({
                "azure_foundry": {
                    "endpoint": "https://my.azure.com",
                    "api_key": "abc123",
                    "model": "gpt-4o",
                    "deployment": "my-deployment",
                }
            })
        self.assertEqual(cfg.azure_endpoint, "https://my.azure.com")
        self.assertEqual(cfg.azure_api_key, "abc123")
        self.assertEqual(cfg.azure_model, "gpt-4o")
        self.assertEqual(cfg.azure_deployment, "my-deployment")

    def test_update_api_key_masked_value_not_overwritten(self):
        """Sending '***' back should not overwrite the actual key."""
        cfg = self._make_config()
        cfg.azure_api_key = "real-key"
        with patch("shared.runtime.model_config._set_env"), \
             patch("shared.runtime.foundry_client.reset_foundry_endpoint"):
            cfg.update({"azure_foundry": {"api_key": "***"}})
        self.assertEqual(cfg.azure_api_key, "real-key")

    def test_list_local_models_fallback(self):
        """When service is not running, returns the configured model."""
        from shared.runtime.model_config import _list_local_models, _config

        original_model = _config.local_model
        _config.local_model = "test-model"
        with patch("foundry_local.FoundryLocalManager") as MockManager:
            MockManager.return_value.is_service_running.return_value = False
            result = _list_local_models()
        _config.local_model = original_model
        self.assertEqual(result, ["test-model"])

    def test_list_local_models_deduplicates(self):
        """Duplicate aliases (e.g. CPU+NPU variants) are collapsed."""
        from shared.runtime.model_config import _list_local_models

        class FakeModel:
            def __init__(self, alias):
                self.alias = alias

        with patch("foundry_local.FoundryLocalManager") as MockManager:
            MockManager.return_value.is_service_running.return_value = True
            MockManager.return_value.list_cached_models.return_value = [
                FakeModel("phi-3.5-mini"),
                FakeModel("phi-3.5-mini"),  # duplicate (CPU vs NPU)
                FakeModel("phi-4"),
            ]
            result = _list_local_models()
        self.assertEqual(result, ["phi-3.5-mini", "phi-4"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
