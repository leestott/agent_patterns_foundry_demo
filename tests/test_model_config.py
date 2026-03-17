"""
Unit tests for ModelConfig.

Tests defaults, update logic, and provider validation without
requiring a live Foundry Local service (available_models is mocked).

Run:
    python -m pytest tests/test_model_config.py -v
or:
    python tests/test_model_config.py
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


class TestModelConfig(unittest.TestCase):

    def _make_config(self, env_overrides: dict | None = None):
        """Return a fresh ModelConfig instance with known defaults, isolated from .env.

        ModelConfig reads env vars at class definition (import) time, so we patch
        the instance attributes directly after construction to guarantee isolation.
        """
        from shared.runtime.model_config import ModelConfig
        cfg = ModelConfig()
        defaults = {
            "provider": "foundry_local",
            "local_model": "qwen2.5-1.5b",
            "local_endpoint_override": "",
            "azure_endpoint": "",
            "azure_api_key": "",
            "azure_model": "gpt-4o-mini",
            "azure_deployment": "",
        }
        if env_overrides:
            # accept either instance-attr names or env-var names
            key_map = {
                "MODEL_PROVIDER": "provider",
                "FOUNDRY_MODEL": "local_model",
                "FOUNDRY_LOCAL_ENDPOINT": "local_endpoint_override",
                "AZURE_FOUNDRY_ENDPOINT": "azure_endpoint",
                "AZURE_FOUNDRY_API_KEY": "azure_api_key",
                "AZURE_FOUNDRY_MODEL": "azure_model",
                "AZURE_FOUNDRY_DEPLOYMENT": "azure_deployment",
            }
            for k, v in env_overrides.items():
                attr = key_map.get(k, k)
                defaults[attr] = v
        for attr, val in defaults.items():
            setattr(cfg, attr, val)
        return cfg

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

    # ------------------------------------------------------------------
    # Tests for _list_local_models_detailed (new model picker backend)
    # ------------------------------------------------------------------

    def test_list_local_models_detailed_service_not_running(self):
        from shared.runtime.model_config import _list_local_models_detailed, _config
        original = _config.local_model
        _config.local_model = "phi-4"
        with patch("foundry_local.FoundryLocalManager") as MockMgr:
            MockMgr.return_value.is_service_running.return_value = False
            result = _list_local_models_detailed()
        _config.local_model = original
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["alias"], "phi-4")
        self.assertEqual(result[0]["status"], "cached")

    def test_list_local_models_detailed_status_priority(self):
        """Loaded > Cached > Catalog when same alias appears multiple times."""
        from shared.runtime.model_config import _list_local_models_detailed

        class FakeModel:
            def __init__(self, alias, id_, device="CPU"):
                self.alias = alias
                self.id = id_
                self.device_type = device
                self.file_size_mb = 512
                self.supports_tool_calling = False
                self.publisher = "Microsoft"
                self.task = "text-generation"

        cpu = FakeModel("phi-4", "phi-4-cpu")
        npu = FakeModel("phi-4", "phi-4-npu")

        with patch("foundry_local.FoundryLocalManager") as MockMgr:
            inst = MockMgr.return_value
            inst.is_service_running.return_value = True
            inst.list_loaded_models.return_value = [cpu]       # cpu variant loaded
            inst.list_cached_models.return_value = [cpu, npu]  # both cached
            inst.list_catalog_models.return_value = [cpu, npu]

            result = _list_local_models_detailed()

        phi = next(m for m in result if m["alias"] == "phi-4")
        self.assertEqual(phi["status"], "loaded")  # cpu loaded → wins

    def test_list_local_models_detailed_status_values(self):
        """Catalog-only model gets status='catalog'."""
        from shared.runtime.model_config import _list_local_models_detailed

        class FakeModel:
            def __init__(self, alias):
                self.alias = alias
                self.id = alias
                self.device_type = "CPU"
                self.file_size_mb = 1024
                self.supports_tool_calling = True
                self.publisher = "Qwen"
                self.task = "text-generation"

        with patch("foundry_local.FoundryLocalManager") as MockMgr:
            inst = MockMgr.return_value
            inst.is_service_running.return_value = True
            inst.list_loaded_models.return_value = []
            inst.list_cached_models.return_value = []
            inst.list_catalog_models.return_value = [FakeModel("qwen2.5-1.5b")]

            result = _list_local_models_detailed()

        self.assertEqual(len(result), 1)
        m = result[0]
        self.assertEqual(m["status"], "catalog")
        self.assertTrue(m["supports_tool_calling"])
        self.assertEqual(m["file_size_mb"], 1024)

    def test_list_local_models_detailed_sorted_order(self):
        """Loaded models appear before cached before catalog."""
        from shared.runtime.model_config import _list_local_models_detailed

        class FakeModel:
            def __init__(self, alias):
                self.alias = alias
                self.id = alias
                self.device_type = "CPU"
                self.file_size_mb = 100
                self.supports_tool_calling = False
                self.publisher = "Test"
                self.task = "text-gen"

        loaded_m  = FakeModel("loaded-model")
        cached_m  = FakeModel("cached-model")
        catalog_m = FakeModel("catalog-model")

        with patch("foundry_local.FoundryLocalManager") as MockMgr:
            inst = MockMgr.return_value
            inst.is_service_running.return_value = True
            inst.list_loaded_models.return_value  = [loaded_m]
            inst.list_cached_models.return_value  = [loaded_m, cached_m]
            inst.list_catalog_models.return_value = [loaded_m, cached_m, catalog_m]

            result = _list_local_models_detailed()

        statuses = [m["status"] for m in result]
        self.assertEqual(statuses[0], "loaded")
        self.assertIn("cached",  statuses)
        self.assertIn("catalog", statuses)
        loaded_idx  = statuses.index("loaded")
        cached_idx  = statuses.index("cached")
        catalog_idx = statuses.index("catalog")
        self.assertLess(loaded_idx,  cached_idx)
        self.assertLess(cached_idx, catalog_idx)

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
        """When service is not running, returns the configured model alias."""
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
