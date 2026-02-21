"""
End-to-end validation for all 6 demos.

Runs each demo's run_demo() with an EventBus, collects events, and checks:
  1. No errors were emitted
  2. Expected agents produced output
  3. Agent messages are non-empty

Run:
    python -m pytest tests/test_demos.py -v   (marks slow, skipped by default unless -m e2e)
or for the full report:
    python tests/test_demos.py
"""

import asyncio
import subprocess
import sys
import time
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from shared.events import EventBus  # noqa: E402

DEMOS = [
    {
        "id": "maker_checker",
        "module": "demos.maker_checker.run",
        "expected_agents": {"Worker", "Reviewer"},
        "label": "1. Maker-Checker PR Review",
    },
    {
        "id": "hierarchical_research",
        "module": "demos.hierarchical_research.run",
        "expected_agents": {"Manager", "Specialist_A", "Specialist_B", "Synthesizer"},
        "label": "2. Hierarchical Research Brief",
    },
    {
        "id": "handoff_support",
        "module": "demos.handoff_support.run",
        "expected_agents": {"Triage", "Billing", "TechSupport"},
        "label": "3. Hand-off Customer Support",
    },
    {
        "id": "network_brainstorm",
        "module": "demos.network_brainstorm.run",
        "expected_agents": {"Innovator", "Pragmatist", "DevilsAdvocate", "Synthesizer"},
        "label": "4. Network Brainstorm",
    },
    {
        "id": "supervisor_router",
        "module": "demos.supervisor_router.run",
        "expected_agents": {"Supervisor", "CodeExpert", "DataExpert", "DocExpert"},
        "label": "5. Supervisor Router",
    },
    {
        "id": "swarm_auditor",
        "module": "demos.swarm_auditor.run",
        "expected_agents": {"Generator_A", "Generator_B", "Generator_C", "Auditor", "Selector"},
        "label": "6. Swarm + Auditor",
    },
]

DEMO_TIMEOUT = 120  # seconds per demo

SEPARATOR = "=" * 70


async def validate_demo(demo: dict) -> dict:
    """Run a single demo and return validation results."""
    import importlib

    label = demo["label"]
    print(f"\n{SEPARATOR}")
    print(f"  {label}")
    print(SEPARATOR)

    bus = EventBus()
    start = time.time()

    try:
        mod = importlib.import_module(demo["module"])
        await asyncio.wait_for(mod.run_demo(bus), timeout=DEMO_TIMEOUT)
        elapsed = time.time() - start
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"  TIMEOUT after {elapsed:.1f}s (limit: {DEMO_TIMEOUT}s)")
        events = bus.get_events()
        messages = [e for e in events if e["type"] == "agent_message"]
        if messages:
            print(f"  Got {len(messages)} messages before timeout")
            return {"demo": label, "status": "WARN", "issues": [f"Timed out after {DEMO_TIMEOUT}s"], "elapsed": elapsed, "event_count": len(events)}
        return {"demo": label, "status": "CRASH", "error": f"Timed out after {DEMO_TIMEOUT}s", "elapsed": elapsed}
    except Exception:
        elapsed = time.time() - start
        tb = traceback.format_exc()
        print(f"  CRASH after {elapsed:.1f}s:\n{tb}")
        return {"demo": label, "status": "CRASH", "error": tb, "elapsed": elapsed}

    events = bus.get_events()
    errors = [e for e in events if e["type"] == "error"]
    messages = [e for e in events if e["type"] == "agent_message"]
    started = [e for e in events if e["type"] == "agent_started"]
    completed = [e for e in events if e["type"] == "agent_completed"]
    handoffs = [e for e in events if e["type"] == "handoff"]

    agents_with_output = set()
    for e in messages:
        agent = e["data"].get("agent", "")
        if agent and agent != "Orchestrator":
            agents_with_output.add(agent)
    for e in completed:
        agent = e["data"].get("agent", "")
        output = e["data"].get("output", "")
        if agent and agent != "Orchestrator" and output:
            agents_with_output.add(agent)
    for e in handoffs:
        agent = e["data"].get("agent", "")
        if agent and agent != "Orchestrator":
            agents_with_output.add(agent)

    print(f"  Time: {elapsed:.1f}s")
    print(f"  Total events: {len(events)}")
    print(f"  Messages: {len(messages)} | Started: {len(started)} | Completed: {len(completed)} | Handoffs: {len(handoffs)} | Errors: {len(errors)}")

    issues = []
    if errors:
        for e in errors:
            err_msg = e["data"].get("error", e["data"].get("message", "unknown"))
            print(f"  ERROR: [{e['data'].get('agent', '?')}] {err_msg[:200]}")
            issues.append(f"Error from {e['data'].get('agent', '?')}: {err_msg[:100]}")

    if demo["id"] == "supervisor_router":
        if "Supervisor" not in agents_with_output:
            issues.append("Supervisor did not produce output")
            print(f"  MISSING: Supervisor did not produce output")
        specialists = {"CodeExpert", "DataExpert", "DocExpert"}
        if not agents_with_output & specialists:
            issues.append("No specialist produced output")
            print(f"  MISSING: No specialist produced output")
        else:
            print(f"  Routed to: {agents_with_output & specialists}")
    elif demo["id"] == "handoff_support":
        if "Triage" not in agents_with_output:
            issues.append("Triage did not produce output")
            print(f"  MISSING: Triage did not produce output")
        specialists = {"Billing", "TechSupport"}
        if not agents_with_output & specialists:
            issues.append("No support agent produced output")
            print(f"  MISSING: No support agent (Billing/TechSupport) produced output")
        else:
            print(f"  Handed off to: {agents_with_output & specialists}")
    else:
        missing = demo["expected_agents"] - agents_with_output
        if missing:
            issues.append(f"Missing agent output: {missing}")
            print(f"  MISSING agents: {missing}")

    print(f"\n  Agents with output: {agents_with_output}")
    for e in messages:
        agent = e["data"].get("agent", "?")
        msg = e["data"].get("message", "")
        if msg and agent != "Orchestrator":
            preview = msg[:120].replace("\n", " ")
            print(f"    [{agent}] {preview}...")

    if not issues and agents_with_output:
        print(f"\n  PASS")
        return {"demo": label, "status": "PASS", "agents": agents_with_output, "elapsed": elapsed, "event_count": len(events)}
    elif not agents_with_output:
        issues.append("No agent produced any output")
        print(f"\n  FAIL — no output")
        return {"demo": label, "status": "FAIL", "issues": issues, "elapsed": elapsed, "event_count": len(events)}
    else:
        print(f"\n  WARN — {len(issues)} issue(s)")
        return {"demo": label, "status": "WARN", "issues": issues, "agents": agents_with_output, "elapsed": elapsed, "event_count": len(events)}


async def main():
    print("\n" + SEPARATOR)
    print("  AGENT PATTERNS DEMO VALIDATION")
    print(SEPARATOR)

    results = []
    for i, demo in enumerate(DEMOS):
        result = await validate_demo(demo)
        results.append(result)

        if result["status"] == "CRASH":
            print("  Restarting Foundry Local service...")
            subprocess.run(["foundry", "service", "stop"], capture_output=True, timeout=15)
            time.sleep(2)
            subprocess.run(["foundry", "service", "start"], capture_output=True, timeout=15)
            time.sleep(5)
            from shared.runtime.foundry_client import reset_foundry_endpoint
            reset_foundry_endpoint()
            print("  Foundry Local restarted.")
        elif i < len(DEMOS) - 1:
            print("  Cooldown 5s before next demo...")
            await asyncio.sleep(5)

    print(f"\n\n{SEPARATOR}")
    print("  SUMMARY")
    print(SEPARATOR)
    for r in results:
        status = r["status"]
        icon = {"PASS": "OK", "WARN": "!!", "FAIL": "XX", "CRASH": "XX"}[status]
        elapsed = r.get("elapsed", 0)
        print(f"  [{icon}] {r['demo']} ({elapsed:.1f}s) — {status}")
        if "issues" in r:
            for issue in r["issues"]:
                print(f"       -> {issue}")

    passes = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print(f"\n  {passes}/{total} demos passed\n")

    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
