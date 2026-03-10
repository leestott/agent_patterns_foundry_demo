"""
Unit tests for foundry_client helper functions.

Covers _ensure_v1_suffix, get_foundry_endpoint (with /v1 normalization),
and the endpoint-override branch in get_foundry_client().

Run:
    python -m pytest tests/test_foundry_client.py -v
or:
    python tests/test_foundry_client.py
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from shared.runtime.foundry_client import _ensure_v1_suffix


class TestEnsureV1Suffix(unittest.TestCase):
    """Tests for _ensure_v1_suffix URL normalization."""

    def test_appends_v1_when_missing(self):
        self.assertEqual(
            _ensure_v1_suffix("http://localhost:5273"),
            "http://localhost:5273/v1",
        )

    def test_no_double_v1_when_already_present(self):
        self.assertEqual(
            _ensure_v1_suffix("http://localhost:5273/v1"),
            "http://localhost:5273/v1",
        )

    def test_strips_trailing_slash_before_appending(self):
        self.assertEqual(
            _ensure_v1_suffix("http://localhost:5273/"),
            "http://localhost:5273/v1",
        )

    def test_no_double_v1_with_trailing_slash(self):
        self.assertEqual(
            _ensure_v1_suffix("http://localhost:5273/v1/"),
            "http://localhost:5273/v1",
        )


class TestGetFoundryEndpoint(unittest.TestCase):
    """Tests for get_foundry_endpoint /v1 stripping."""

    def setUp(self):
        # Clear the lru_cache before each test
        from shared.runtime.foundry_client import reset_foundry_endpoint
        reset_foundry_endpoint()

    def test_env_var_without_v1(self):
        from shared.runtime.foundry_client import get_foundry_endpoint
        with patch.dict("os.environ", {"FOUNDRY_LOCAL_ENDPOINT": "http://localhost:5273"}, clear=False), \
             patch("shared.runtime.model_config.get_model_config", side_effect=Exception("no config")):
            result = get_foundry_endpoint()
        self.assertEqual(result, "http://localhost:5273")

    def test_env_var_with_v1_is_stripped(self):
        from shared.runtime.foundry_client import get_foundry_endpoint
        with patch.dict("os.environ", {"FOUNDRY_LOCAL_ENDPOINT": "http://localhost:5273/v1"}, clear=False), \
             patch("shared.runtime.model_config.get_model_config", side_effect=Exception("no config")):
            result = get_foundry_endpoint()
        self.assertEqual(result, "http://localhost:5273")

    def test_env_var_with_v1_trailing_slash_is_stripped(self):
        from shared.runtime.foundry_client import get_foundry_endpoint
        with patch.dict("os.environ", {"FOUNDRY_LOCAL_ENDPOINT": "http://localhost:5273/v1/"}, clear=False), \
             patch("shared.runtime.model_config.get_model_config", side_effect=Exception("no config")):
            result = get_foundry_endpoint()
        self.assertEqual(result, "http://localhost:5273")


class TestGetFoundryClientEndpointOverride(unittest.TestCase):
    """Tests for endpoint-override branch in get_foundry_client."""

    def _patch_model_config(self, local_endpoint_override=None, local_model="qwen2.5-1.5b"):
        """Return a mock ModelConfig."""
        cfg = MagicMock()
        cfg.provider = "foundry_local"
        cfg.local_endpoint_override = local_endpoint_override
        cfg.local_model = local_model
        return cfg

    def _make_mock_client_class(self):
        """Return a mock OpenAIChatClient class that records constructor args."""
        mock_cls = MagicMock()
        # When called as constructor, return a mock with recorded kwargs
        def capture_init(**kwargs):
            instance = MagicMock()
            instance._base_url = kwargs.get("base_url")
            instance._model_id = kwargs.get("model_id")
            instance._api_key = kwargs.get("api_key")
            return instance
        mock_cls.side_effect = capture_init
        return mock_cls

    @patch("shared.runtime.foundry_client._get_manager")
    def test_override_without_v1_gets_v1_appended(self, mock_get_manager):
        mock_manager = MagicMock()
        mock_manager.get_model_info.return_value = None
        mock_get_manager.return_value = mock_manager

        mock_client_cls = self._make_mock_client_class()
        cfg = self._patch_model_config(local_endpoint_override="http://localhost:5273")
        with patch("shared.runtime.model_config.get_model_config", return_value=cfg), \
             patch.dict("sys.modules", {"agent_framework": MagicMock(), "agent_framework.openai": MagicMock(OpenAIChatClient=mock_client_cls)}), \
             patch.dict("os.environ", {}, clear=False):
            from shared.runtime.foundry_client import get_foundry_client
            client = get_foundry_client()
        self.assertEqual(client._base_url, "http://localhost:5273/v1")

    @patch("shared.runtime.foundry_client._get_manager")
    def test_override_with_v1_no_double_suffix(self, mock_get_manager):
        mock_manager = MagicMock()
        mock_manager.get_model_info.return_value = None
        mock_get_manager.return_value = mock_manager

        mock_client_cls = self._make_mock_client_class()
        cfg = self._patch_model_config(local_endpoint_override="http://localhost:5273/v1")
        with patch("shared.runtime.model_config.get_model_config", return_value=cfg), \
             patch.dict("sys.modules", {"agent_framework": MagicMock(), "agent_framework.openai": MagicMock(OpenAIChatClient=mock_client_cls)}), \
             patch.dict("os.environ", {}, clear=False):
            from shared.runtime.foundry_client import get_foundry_client
            client = get_foundry_client()
        self.assertEqual(client._base_url, "http://localhost:5273/v1")

    @patch("shared.runtime.foundry_client._get_manager")
    def test_override_resolves_model_alias_via_sdk(self, mock_get_manager):
        mock_model_info = MagicMock()
        mock_model_info.id = "qwen2.5-1.5b-instruct-trtrtx-gpu:2"
        mock_manager = MagicMock()
        mock_manager.get_model_info.return_value = mock_model_info
        mock_get_manager.return_value = mock_manager

        mock_client_cls = self._make_mock_client_class()
        cfg = self._patch_model_config(local_endpoint_override="http://localhost:5273/v1")
        with patch("shared.runtime.model_config.get_model_config", return_value=cfg), \
             patch.dict("sys.modules", {"agent_framework": MagicMock(), "agent_framework.openai": MagicMock(OpenAIChatClient=mock_client_cls)}), \
             patch.dict("os.environ", {}, clear=False):
            from shared.runtime.foundry_client import get_foundry_client
            client = get_foundry_client()
        self.assertEqual(client._model_id, "qwen2.5-1.5b-instruct-trtrtx-gpu:2")

    @patch("shared.runtime.foundry_client._get_manager")
    def test_override_falls_back_to_raw_alias_when_sdk_fails(self, mock_get_manager):
        mock_get_manager.side_effect = Exception("SDK unavailable")

        mock_client_cls = self._make_mock_client_class()
        cfg = self._patch_model_config(local_endpoint_override="http://localhost:5273/v1")
        with patch("shared.runtime.model_config.get_model_config", return_value=cfg), \
             patch.dict("sys.modules", {"agent_framework": MagicMock(), "agent_framework.openai": MagicMock(OpenAIChatClient=mock_client_cls)}), \
             patch.dict("os.environ", {}, clear=False):
            from shared.runtime.foundry_client import get_foundry_client
            client = get_foundry_client()
        self.assertEqual(client._model_id, "qwen2.5-1.5b")

    @patch("shared.runtime.foundry_client._get_manager")
    def test_env_var_override_with_v1_no_double_suffix(self, mock_get_manager):
        mock_manager = MagicMock()
        mock_manager.get_model_info.return_value = None
        mock_get_manager.return_value = mock_manager

        mock_client_cls = self._make_mock_client_class()
        cfg = self._patch_model_config(local_endpoint_override=None)
        with patch("shared.runtime.model_config.get_model_config", return_value=cfg), \
             patch.dict("sys.modules", {"agent_framework": MagicMock(), "agent_framework.openai": MagicMock(OpenAIChatClient=mock_client_cls)}), \
             patch.dict("os.environ", {"FOUNDRY_LOCAL_ENDPOINT": "http://localhost:5273/v1"}, clear=False):
            from shared.runtime.foundry_client import get_foundry_client
            client = get_foundry_client()
        self.assertEqual(client._base_url, "http://localhost:5273/v1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
