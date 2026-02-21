"""
Model client factory — supports Foundry Local and Azure AI Foundry.

Routes to the correct backend based on ``ModelConfig.provider``:
  - "foundry_local"  : uses the official ``foundry-local-sdk`` to discover
                       the service endpoint and resolve model IDs
  - "azure_foundry"  : connects to an Azure AI Foundry endpoint
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

# Default friendly model alias (Foundry Local catalog alias)
DEFAULT_MODEL = "qwen2.5-1.5b"


def _get_manager(bootstrap: bool = False):
    """Return a FoundryLocalManager, optionally bootstrapping the service."""
    from foundry_local import FoundryLocalManager
    return FoundryLocalManager(bootstrap=bootstrap)


@lru_cache(maxsize=1)
def get_foundry_endpoint() -> str:
    """Return the Foundry Local base service URI (without /v1).

    Priority:
    1. ModelConfig.local_endpoint_override (set via UI)
    2. FOUNDRY_LOCAL_ENDPOINT env var (legacy explicit override)
    3. SDK auto-discovery via FoundryLocalManager
    """
    try:
        from shared.runtime.model_config import get_model_config
        override = get_model_config().local_endpoint_override
        if override:
            return override.rstrip("/")
    except Exception:
        pass

    env_ep = os.getenv("FOUNDRY_LOCAL_ENDPOINT")
    if env_ep:
        return env_ep.rstrip("/")

    try:
        manager = _get_manager()
        if manager.is_service_running():
            # service_uri is the base URL, e.g. "http://127.0.0.1:58627"
            return manager.service_uri.rstrip("/")
    except Exception as e:
        print(f"[foundry_client] SDK discovery failed: {e}")

    raise RuntimeError(
        "Could not detect Foundry Local endpoint. "
        "Ensure Foundry Local is running ('foundry model run qwen2.5-1.5b') "
        "or set FOUNDRY_LOCAL_ENDPOINT in .env."
    )


def reset_foundry_endpoint():
    """Clear the cached endpoint so the next call re-discovers it."""
    get_foundry_endpoint.cache_clear()


def _normalize_azure_base_url(endpoint: str) -> str:
    """Convert any Azure endpoint format to the /openai/v1 base URL.

    Accepts:
    - Full deployment URL: https://host/openai/deployments/<name>/chat/completions?...
    - Resource root only: https://host.cognitiveservices.azure.com
    - Already correct:    https://host.cognitiveservices.azure.com/openai/v1
    """
    from urllib.parse import urlparse
    parsed = urlparse(endpoint.strip())
    base = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path.rstrip("/")

    if "/openai/deployments/" in path or "/openai/v1" in path:
        # Strip back to resource root + /openai/v1
        return f"{base}/openai/v1"
    if path.endswith("/openai"):
        return f"{base}/openai/v1"
    if not path or path == "/":
        return f"{base}/openai/v1"
    # Unknown path — append /v1 only if needed
    if not path.endswith("/v1"):
        return f"{base}{path}/v1"
    return f"{base}{path}"


def get_model_id() -> str:
    """Get the active model alias/ID from model_config (or env fallback)."""
    try:
        from shared.runtime.model_config import get_model_config
        cfg = get_model_config()
        if cfg.provider == "azure_foundry":
            return cfg.azure_deployment or cfg.azure_model
        return cfg.local_model
    except Exception:
        return os.getenv("FOUNDRY_MODEL", DEFAULT_MODEL)


def get_foundry_client():
    """Create an Agent Framework client for the active provider.

    Reads ModelConfig.provider and returns either:
      - A Foundry Local OpenAIChatClient (endpoint + model ID via SDK)
      - An Azure AI Foundry OpenAIChatClient
    """
    from agent_framework.openai import OpenAIChatClient

    try:
        from shared.runtime.model_config import get_model_config
        cfg = get_model_config()
        provider = cfg.provider
    except Exception:
        provider = "foundry_local"
        cfg = None

    # ── Azure AI Foundry ────────────────────────────────────────────────────
    if provider == "azure_foundry":
        if not cfg.azure_endpoint:
            raise RuntimeError(
                "Azure AI Foundry endpoint not configured. "
                "Set AZURE_FOUNDRY_ENDPOINT in .env or via the Model Settings UI."
            )
        if not cfg.azure_api_key:
            raise RuntimeError(
                "Azure AI Foundry API key not configured. "
                "Set AZURE_FOUNDRY_API_KEY in .env or via the Model Settings UI."
            )
        base_url = _normalize_azure_base_url(cfg.azure_endpoint)
        model_id = cfg.azure_deployment or cfg.azure_model
        print(f"[foundry_client] Azure AI Foundry: {base_url} -> '{model_id}'")
        return OpenAIChatClient(
            api_key=cfg.azure_api_key,
            base_url=base_url,
            model_id=model_id,
        )

    # ── Foundry Local (via official SDK) ────────────────────────────────────
    alias = cfg.local_model if cfg else os.getenv("FOUNDRY_MODEL", DEFAULT_MODEL)

    try:
        manager = _get_manager()
        if not manager.is_service_running():
            raise RuntimeError(
                "Foundry Local service is not running. "
                "Start it with: foundry model run qwen2.5-1.5b"
            )
        # endpoint already includes /v1 — e.g. "http://127.0.0.1:58627/v1"
        base_url = manager.endpoint
        api_key = manager.api_key
        # Resolve alias -> full catalog ID (e.g. "qwen2.5-1.5b" -> "qwen2.5-1.5b-instruct-qnn-npu:2")
        model_info = manager.get_model_info(alias)
        model_id = model_info.id if model_info else alias
        if model_id != alias:
            print(f"[foundry_client] Resolved '{alias}' -> '{model_id}'")
    except Exception as e:
        print(f"[foundry_client] SDK lookup failed ({e}), falling back to legacy endpoint")
        service_uri = get_foundry_endpoint()
        base_url = f"{service_uri}/v1"
        api_key = os.getenv("FOUNDRY_API_KEY", "foundry-local")
        model_id = alias

    print(f"[foundry_client] Foundry Local: {base_url} -> '{model_id}'")
    return OpenAIChatClient(
        api_key=api_key,
        base_url=base_url,
        model_id=model_id,
    )
