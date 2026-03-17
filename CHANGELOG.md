# Changelog

All notable changes to the Agent Patterns Demo Pack are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — 2026-03-17

### Added

#### Model Picker UI
- **Live model picker** in the launcher settings panel — switch models without editing `.env` or restarting the app.
- **`GET /api/models/local`** — returns all Foundry Local catalog models with live status per model: `loaded` (in memory), `cached` (on disk), or `catalog` (available to download). Each entry includes device type, size in MB, tool-calling support, publisher, and task.
- **`GET /api/models/azure`** — queries the configured Microsoft Foundry endpoint for deployed model names; click any row to select.
- **`_list_local_models_detailed()`** helper in `shared/runtime/model_config.py` — deduplicates by alias, promotes highest-priority status (loaded > cached > catalog), sorts loaded first.
- **`_minimal_model_entry()`** fallback helper for when the Foundry Local service is not running.
- Foundry Local tab redesigned from a `<select>` dropdown to **card-based model picker** with colour-coded status badges, metadata tags, and a **↻ Refresh** button.
- Microsoft Foundry tab: **↻ List Models** button queries live deployments; click-to-select list  below the model text field.
- Provider chip and gear icon in the launcher header now show the selected model name.
- `switchTab()` auto-refreshes the local model list when switching to the Foundry Local tab.

#### Tests
- **`tests/test_api.py`** — comprehensive FastAPI endpoint unit tests covering `/api/demos`, `/api/status`, `/api/topology`, `/api/model-config` (GET + POST), `/api/models/local`, `/api/models/azure`, `/api/run/{id}`, and `/api/replay`.
- **`tests/test_model_config.py`** — four new tests for `_list_local_models_detailed`: service-not-running fallback, valid status values, status priority ordering, and sort order (loaded → cached → catalog).
- `tests/test_topology.py` now validates all **seven** demos (added `magentic_one`).
- Test suite: **57 tests, 64 subtests — 0 failures**.

#### Documentation
- **`agents.md`** — full agent reference covering every agent across all seven demos: roles, instructions, topology diagrams, pattern decision guide, model picker API docs.
- **`CHANGELOG.md`** — this file.
- README: new **Model Picker UI** section with screenshot table, updated architecture tree (added `agents.md`, `tests/test_api.py`), updated testing commands, added agent reference link.
- Blog post: new **Choosing Your Model** section with model picker screenshots and explanation of `Loaded`/`Cached`/`Available` status badges.
- Screenshots: `02_model_settings_foundry_local.png` and `03_model_settings_azure_foundry.png` captured and added to `screenshots/`.

### Changed

- `shared/runtime/model_config.py` — `to_dict()` still returns `available_models` (list of aliases) via `_list_local_models()` for backwards compatibility; new `/api/models/local` endpoint uses the richer `_list_local_models_detailed()`.
- `shared/ui/static/launcher.html` — model settings panel markup reworked; JS brace balance verified (95 open / 95 close).
- `tests/test_model_config.py` — `_make_config()` now overrides instance attributes directly after construction (avoids `.env`-dependent class-level `os.getenv()` evaluated at import time).

### Fixed

- `tests/test_model_config.py`: two tests (`test_default_provider_is_foundry_local`, `test_default_azure_model`) previously failed when run against a `.env` with `MODEL_PROVIDER=azure_foundry`. Fixed by overriding attributes on the instantiated object rather than relying on environment patching.
- `tests/test_api.py`: initial `test_returns_models_list_on_success` used deprecated `asyncio.coroutine` (removed in Python 3.13). Replaced with `AsyncMock`-based patching of `httpx.AsyncClient.get`.

---

## [1.0.0] — 2026-03-04

### Added

- Initial release of the Agent Patterns Demo Pack.
- Seven runnable multi-agent demos: Maker-Checker, Hierarchical Research, Hand-off Customer Support, Network Brainstorm, Supervisor Router, Swarm + Auditor, Magentic One.
- Unified FastAPI web app at `http://localhost:8765` with card-based launcher and per-demo live dashboard.
- **Graph panel**: D3.js force-directed agent graph, zoom in/out, active agent highlight.
- **Live Stream panel**: real-time agent messages via WebSocket.
- **Timeline panel**: chronological trace with expandable event details.
- **Replay**: load any saved `.jsonl` run file and replay the graph animation without a live model.
- `shared/runtime/foundry_client.py` — auto-discovers Foundry Local dynamic port via `FoundryLocalManager`; falls back to `FOUNDRY_LOCAL_ENDPOINT` override.
- `shared/runtime/model_config.py` — `ModelConfig` singleton persists provider settings to `.env` via `python-dotenv`.
- `shared/events/event_bus.py` — in-process pub/sub with WebSocket bridge and JSONL logger.
- `shared/runtime/orchestrations.py` — thin helpers wrapping all five Agent Framework builders.
- Demo topology files (`topology.json`) for graph renderer — no code needed for layout.
- Test suite: `test_topology.py`, `test_event_bus.py`, `test_model_config.py`, `test_demos.py`.
- `validate_demos.py` backwards-compatible shim forwarding to `tests/test_demos.py`.
- `capture_screenshots.py` — Playwright-based screenshot and video capture.
- `docs/architecture.md`, `docs/walkthrough.md`, `docs/demo-day-checklist.md`.
- `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE` (MIT).
