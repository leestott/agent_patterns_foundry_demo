"""
Model configuration — runtime-switchable provider settings.

Supports two providers:
  - "foundry_local"  : on-device Foundry Local service (auto-discovered)
  - "azure_foundry"  : Microsoft Foundry cloud endpoint

The active config is held in a module-level singleton and written
to/from the .env file so it persists across restarts.
"""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv, set_key

ENV_FILE = Path(__file__).parents[2] / ".env"
load_dotenv(ENV_FILE)

ProviderType = Literal["foundry_local", "azure_foundry"]


class ModelConfig:
    """Singleton that holds active model provider configuration."""

    # ---- Provider ----------------------------------------------------------
    provider: ProviderType = os.getenv("MODEL_PROVIDER", "foundry_local")  # type: ignore[assignment]

    # ---- Foundry Local settings --------------------------------------------
    local_model: str = os.getenv("FOUNDRY_MODEL", "qwen2.5-1.5b")
    local_endpoint_override: str = os.getenv("FOUNDRY_LOCAL_ENDPOINT", "")

    # ---- Microsoft Foundry settings ----------------------------------------
    azure_endpoint: str = os.getenv("AZURE_FOUNDRY_ENDPOINT", "")
    azure_api_key: str = os.getenv("AZURE_FOUNDRY_API_KEY", "")
    azure_model: str = os.getenv("AZURE_FOUNDRY_MODEL", "gpt-4o-mini")
    azure_deployment: str = os.getenv("AZURE_FOUNDRY_DEPLOYMENT", "")

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "foundry_local": {
                "model": self.local_model,
                "endpoint_override": self.local_endpoint_override,
                "available_models": _list_local_models(),
            },
            "azure_foundry": {
                "endpoint": self.azure_endpoint,
                "api_key": "***" if self.azure_api_key else "",
                "model": self.azure_model,
                "deployment": self.azure_deployment,
            },
        }

    def update(self, data: dict):
        """Apply a partial update from the UI and persist to .env."""
        if "provider" in data:
            prov = data["provider"]
            if prov not in ("foundry_local", "azure_foundry"):
                raise ValueError(f"Invalid provider: {prov!r}")
            self.provider = prov
            _set_env("MODEL_PROVIDER", prov)

        fl = data.get("foundry_local", {})
        if "model" in fl:
            self.local_model = str(fl["model"]).strip()
            _set_env("FOUNDRY_MODEL", self.local_model)
        if "endpoint_override" in fl:
            self.local_endpoint_override = str(fl["endpoint_override"]).strip()
            _set_env("FOUNDRY_LOCAL_ENDPOINT", self.local_endpoint_override)

        az = data.get("azure_foundry", {})
        if "endpoint" in az:
            self.azure_endpoint = str(az["endpoint"]).strip()
            _set_env("AZURE_FOUNDRY_ENDPOINT", self.azure_endpoint)
        if "api_key" in az and az["api_key"] != "***":
            self.azure_api_key = str(az["api_key"]).strip()
            _set_env("AZURE_FOUNDRY_API_KEY", self.azure_api_key)
        if "model" in az:
            self.azure_model = str(az["model"]).strip()
            _set_env("AZURE_FOUNDRY_MODEL", self.azure_model)
        if "deployment" in az:
            self.azure_deployment = str(az["deployment"]).strip()
            _set_env("AZURE_FOUNDRY_DEPLOYMENT", self.azure_deployment)

        # When provider changes, invalidate the cached endpoint
        from shared.runtime.foundry_client import reset_foundry_endpoint
        reset_foundry_endpoint()


# Module-level singleton
_config = ModelConfig()


def get_model_config() -> ModelConfig:
    return _config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_env(key: str, value: str):
    """Persist a key-value pair to the .env file."""
    if ENV_FILE.exists():
        set_key(str(ENV_FILE), key, value)
    os.environ[key] = value


def _list_local_models() -> list[str]:
    """Return aliases of models downloaded to the local Foundry cache."""
    try:
        from foundry_local import FoundryLocalManager
        manager = FoundryLocalManager(bootstrap=False)
        if not manager.is_service_running():
            return [_config.local_model]
        cached = manager.list_cached_models()
        aliases = list(dict.fromkeys(m.alias for m in cached if m.alias))  # deduplicated, order preserved
        return aliases if aliases else [_config.local_model]
    except Exception:
        return [_config.local_model]
