"""
E2E screenshot and video capture for the Agent Patterns Demo Pack.

Launches the app, navigates through the launcher and each demo dashboard,
captures screenshots and records a walkthrough video.

Usage:
    python capture_screenshots.py              # screenshots only
    python capture_screenshots.py --video      # screenshots + video
"""

import argparse
import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.async_api import async_playwright

APP_PORT = int(os.getenv("UI_PORT", "8765"))
BASE_URL = f"http://localhost:{APP_PORT}"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
VIDEO_DIR = Path(__file__).parent / "screenshots" / "video"

DEMOS = [
    "maker_checker",
    "hierarchical_research",
    "handoff_support",
    "network_brainstorm",
    "supervisor_router",
    "swarm_auditor",
]


async def wait_for_server(url: str, timeout: int = 30):
    """Wait until the server is reachable."""
    import urllib.request
    import urllib.error

    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=3)
            return True
        except (urllib.error.URLError, ConnectionError, OSError):
            await asyncio.sleep(1)
    raise TimeoutError(f"Server at {url} did not start within {timeout}s")


async def capture_screenshots(page, screenshot_dir: Path):
    """Navigate through all pages and capture screenshots."""
    # 1. Launcher page
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    await page.screenshot(path=str(screenshot_dir / "01_launcher.png"), full_page=True, timeout=60000)
    print("  [+] Captured: 01_launcher.png")

    # 2. Each demo card hover state
    cards = await page.query_selector_all(".demo-card")
    for i, card in enumerate(cards):
        await card.hover()
        await page.wait_for_timeout(300)

    await page.screenshot(path=str(screenshot_dir / "02_launcher_hover.png"), full_page=True, timeout=60000)
    print("  [+] Captured: 02_launcher_hover.png")

    # 3. Navigate to each demo, run to completion, capture with full output visible
    for idx, demo_id in enumerate(DEMOS, start=1):
        num = str(idx + 2).zfill(2)

        # Navigate to the demo dashboard (suggested prompt is pre-filled by the server)
        await page.goto(f"{BASE_URL}/demo/{demo_id}", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)  # let WebSocket connect and graph initialise

        # Fire the run (sendPrompt is the global function in dashboard.js)
        await page.evaluate("sendPrompt()")

        # Wait for the demo to fully complete
        await _wait_for_demo_complete(page, demo_id, max_wait_s=180)
        await page.wait_for_timeout(1000)  # allow final renders to settle

        # Scroll stream and agent-output panels to show completed output
        await page.evaluate("""
            const s = document.getElementById('stream-messages');
            if (s) s.scrollTop = s.scrollHeight;
            const a = document.getElementById('agent-outputs');
            if (a) a.scrollTop = a.scrollHeight;
        """)
        await page.wait_for_timeout(500)

        # Viewport screenshot — captures the full grid layout showing all panels
        await page.screenshot(
            path=str(screenshot_dir / f"{num}_{demo_id}_dashboard.png"),
            full_page=False,
            timeout=60000,
        )
        print(f"  [+] Captured: {num}_{demo_id}_dashboard.png")

    # 4. Back to launcher showing completed state
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(1000)
    await page.screenshot(path=str(screenshot_dir / "09_launcher_final.png"), full_page=True, timeout=60000)
    print("  [+] Captured: 09_launcher_final.png")


DEMO_TITLES = {
    "maker_checker":          "Demo 1: Maker-Checker (Sequential)",
    "hierarchical_research":  "Demo 2: Hierarchical Research (Concurrent + Sequential)",
    "handoff_support":        "Demo 3: Hand-off Support (Handoff)",
    "network_brainstorm":     "Demo 4: Network Brainstorm (Group Chat)",
    "supervisor_router":      "Demo 5: Supervisor Router (Sequential + Handoff)",
    "swarm_auditor":          "Demo 6: Swarm + Auditor (Concurrent + Sequential)",
}


async def _wait_for_demo_complete(page, demo_id: str, max_wait_s: int = 180) -> bool:
    """Two-phase poll: wait for demo to START, then wait for it to FINISH."""
    # Phase 1: wait until running=True with matching demo_id (up to 20s)
    start_deadline = time.time() + 20
    while time.time() < start_deadline:
        try:
            status = await page.evaluate("fetch('/api/status').then(r => r.json())")
            if status.get("running") and status.get("demo_id") == demo_id:
                break
        except Exception:
            pass
        await page.wait_for_timeout(500)

    # Phase 2: wait until running=False
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        try:
            status = await page.evaluate("fetch('/api/status').then(r => r.json())")
            if not status.get("running", True):
                return True
        except Exception:
            pass
        await page.wait_for_timeout(1500)
    return False  # timed out


async def record_video(page, video_dir: Path):
    """Record a walkthrough of all six demos, each shown from start to completion.

    After each demo finishes the stream panel slow-scrolls top-to-bottom so viewers
    can read every event, then the agent-output panel does the same, before holding
    at the fully-populated final state.
    """
    # --- Launcher intro -------------------------------------------------------
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)

    cards = await page.query_selector_all(".demo-card")
    for card in cards:
        await card.hover()
        await page.wait_for_timeout(400)
    await page.wait_for_timeout(800)

    # --- Each demo: navigate, run, wait for full completion, show output ------
    for demo_id in DEMOS:
        print(f"  [video] Starting: {DEMO_TITLES[demo_id]}")

        # Navigate to the demo dashboard (suggested prompt is pre-filled)
        await page.goto(f"{BASE_URL}/demo/{demo_id}", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)  # let WebSocket connect and graph render

        # Trigger the run via page.evaluate (DevTools protocol bypasses CSP)
        await page.evaluate("sendPrompt()")

        # Two-phase wait: start confirmed, then wait for finish
        completed = await _wait_for_demo_complete(page, demo_id, max_wait_s=180)
        if completed:
            print(f"  [video] Completed: {DEMO_TITLES[demo_id]}")
        else:
            print(f"  [video] Timed out: {DEMO_TITLES[demo_id]}")

        # Allow final DOM renders to settle
        await page.wait_for_timeout(1000)

        # Slow-scroll the stream panel from top to bottom (~4s) so every event is visible
        await page.evaluate("""
            const s = document.getElementById('stream-messages');
            if (s) s.scrollTop = 0;
        """)
        await page.wait_for_timeout(400)
        await page.evaluate("""
            (function() {
                const s = document.getElementById('stream-messages');
                if (!s) return;
                const total = Math.max(0, s.scrollHeight - s.clientHeight);
                if (total === 0) return;
                let pos = 0;
                const steps = 40;
                const inc = total / steps;
                const tick = () => {
                    pos = Math.min(pos + inc, total);
                    s.scrollTop = pos;
                    if (pos < total) setTimeout(tick, 100);
                };
                tick();
            })();
        """)
        await page.wait_for_timeout(4500)

        # Slow-scroll the agent-output panel from top to bottom (~4s)
        await page.evaluate("""
            const a = document.getElementById('agent-outputs');
            if (a) a.scrollTop = 0;
        """)
        await page.wait_for_timeout(400)
        await page.evaluate("""
            (function() {
                const a = document.getElementById('agent-outputs');
                if (!a) return;
                const total = Math.max(0, a.scrollHeight - a.clientHeight);
                if (total === 0) return;
                let pos = 0;
                const steps = 40;
                const inc = total / steps;
                const tick = () => {
                    pos = Math.min(pos + inc, total);
                    a.scrollTop = pos;
                    if (pos < total) setTimeout(tick, 100);
                };
                tick();
            })();
        """)
        await page.wait_for_timeout(4500)

        # Ensure both panels rest at the bottom (full output visible)
        await page.evaluate("""
            const s = document.getElementById('stream-messages');
            if (s) s.scrollTop = s.scrollHeight;
            const a = document.getElementById('agent-outputs');
            if (a) a.scrollTop = a.scrollHeight;
        """)

        # Hold on the completed, fully-scrolled state so viewers can read the results
        await page.wait_for_timeout(8000)

    # --- Return to launcher ---------------------------------------------------
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)


async def record_short_demo(page, video_dir: Path):
    """Record a ~60s video showing all six completed dashboards using instant JSONL replay.

    Each demo is loaded from the most recent saved run file, replayed instantly so
    all panels (stream, timeline, agent outputs, graph) are fully populated, then
    held on screen long enough for viewers to read the output before moving on.
    If no saved run exists for a demo it is pre-run first.
    """
    import urllib.request
    import json as _json

    # --- Collect most recent JSONL for each demo ------------------------------
    run_files: dict[str, str] = {}
    for demo_id in DEMOS:
        runs_dir = Path(__file__).parent / "demos" / demo_id / "runs"
        files = list(runs_dir.glob("*.jsonl")) if runs_dir.exists() else []
        if files:
            run_files[demo_id] = str(max(files, key=lambda f: f.stat().st_mtime))

    # --- Pre-run any demos that have no saved replay file ---------------------
    missing = [d for d in DEMOS if d not in run_files]
    if missing:
        print(f"  [short] Pre-running {len(missing)} demo(s) to generate replay files...")
        for demo_id in missing:
            print(f"  [short] Pre-running: {DEMO_TITLES[demo_id]}")
            runs_dir = Path(__file__).parent / "demos" / demo_id / "runs"
            before = set(runs_dir.glob("*.jsonl")) if runs_dir.exists() else set()
            req = urllib.request.Request(
                f"{BASE_URL}/api/run/{demo_id}",
                data=b'{}', headers={"Content-Type": "application/json"}, method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
            started = False
            deadline = time.time() + 180
            while time.time() < deadline:
                try:
                    status = _json.loads(
                        urllib.request.urlopen(f"{BASE_URL}/api/status", timeout=5).read()
                    )
                    if status.get("running"):
                        started = True
                    elif started:
                        break
                except Exception:
                    pass
                time.sleep(1.5)
            after = set(runs_dir.glob("*.jsonl")) if runs_dir.exists() else set()
            new = after - before
            candidates = new or set(runs_dir.glob("*.jsonl"))
            if candidates:
                run_files[demo_id] = str(max(candidates, key=lambda f: f.stat().st_mtime))

    # --- Launcher intro (1.5s) --------------------------------------------------
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(1500)

    # --- Each demo: instant replay → render settle → slow-scroll panels → hold ---
    # Per-demo budget ~8s × 6 = 48s + 4s framing ≈ 52s total
    for demo_id in DEMOS:
        jsonl_path = run_files.get(demo_id, "")
        if not jsonl_path:
            print(f"  [short] Skipping {demo_id}: no replay file found")
            continue
        print(f"  [short] Showing: {DEMO_TITLES[demo_id]}")

        # Navigate to dashboard (empty start state briefly visible)
        await page.goto(f"{BASE_URL}/demo/{demo_id}", wait_until="domcontentloaded")
        await page.wait_for_timeout(500)

        # Instant replay: load all events at once so every panel populates fully
        safe_path = jsonl_path.replace("\\", "\\\\")
        await page.evaluate(f"""
            (async () => {{
                const res = await fetch('/api/replay', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{path: '{safe_path}'}})
                }});
                if (!res.ok) return;
                const events = await res.json();
                if (typeof clearAll === 'function') clearAll();
                for (const ev of events) {{
                    if (typeof handleEvent === 'function') handleEvent(ev);
                }}
            }})();
        """)

        # Wait for all DOM updates and renders to settle (graph, stream, outputs)
        await page.wait_for_timeout(1500)

        # --- Stream panel: scroll from top to bottom slowly (~2s) ---
        await page.evaluate("""
            const s = document.getElementById('stream-messages');
            if (s) s.scrollTop = 0;
        """)
        await page.evaluate("""
            (function() {
                const s = document.getElementById('stream-messages');
                if (!s) return;
                const total = Math.max(0, s.scrollHeight - s.clientHeight);
                if (total === 0) return;
                let pos = 0; const steps = 20; const inc = total / steps;
                const tick = () => {
                    pos = Math.min(pos + inc, total);
                    s.scrollTop = pos;
                    if (pos < total) setTimeout(tick, 80);
                };
                tick();
            })();
        """)
        await page.wait_for_timeout(1800)

        # --- Agent-output panel: scroll from top to bottom slowly (~3s) ---
        await page.evaluate("""
            const a = document.getElementById('agent-outputs');
            if (a) a.scrollTop = 0;
        """)
        await page.evaluate("""
            (function() {
                const a = document.getElementById('agent-outputs');
                if (!a) return;
                const total = Math.max(0, a.scrollHeight - a.clientHeight);
                if (total === 0) return;
                let pos = 0; const steps = 30; const inc = total / steps;
                const tick = () => {
                    pos = Math.min(pos + inc, total);
                    a.scrollTop = pos;
                    if (pos < total) setTimeout(tick, 100);
                };
                tick();
            })();
        """)
        await page.wait_for_timeout(3200)

        # Rest both panels at bottom showing all completed output
        await page.evaluate("""
            const s = document.getElementById('stream-messages');
            if (s) s.scrollTop = s.scrollHeight;
            const a = document.getElementById('agent-outputs');
            if (a) a.scrollTop = a.scrollHeight;
        """)

        # Hold on the fully-populated final state
        await page.wait_for_timeout(800)

    # --- Return to launcher (1.5s) ----------------------------------------------
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(1500)


async def _scroll_panel_frames(page, panel_id: str, snap_fn, hold: float = 1.5):
    """Capture frames while scrolling a panel from top to bottom in steps."""
    info = await page.evaluate(f"""
        (() => {{
            const el = document.getElementById('{panel_id}');
            if (!el) return {{ scrollable: 0, client: 0 }};
            return {{ scrollable: el.scrollHeight - el.clientHeight, client: el.clientHeight }};
        }})()
    """)
    scrollable = info.get("scrollable", 0)
    if scrollable <= 0:
        await snap_fn(hold)
        return
    step = max(info.get("client", 300) * 0.8, 100)
    positions = []
    pos = 0
    while pos < scrollable:
        positions.append(int(pos))
        pos += step
    positions.append(int(scrollable))

    for p in positions:
        await page.evaluate(f"document.getElementById('{panel_id}').scrollTop = {p}")
        await page.wait_for_timeout(300)
        await snap_fn(hold)


async def _zoom_panel(page, panel_id: str):
    """Make a single panel fill the whole viewport with enlarged font."""
    await page.evaluate(f"""(() => {{
        const hdr = document.querySelector('header');
        const bar = document.querySelector('.prompt-bar');
        if (hdr) hdr.style.display = 'none';
        if (bar) bar.style.display = 'none';
        const main = document.querySelector('main');
        if (main) {{
            main.style.display = 'block';
            main.style.height = '100vh';
            main.style.overflow = 'hidden';
        }}
        document.querySelectorAll('main > section').forEach(s => {{
            if (s.id === '{panel_id}') {{
                s.style.display = 'block';
                s.style.height = '100vh';
                s.style.overflow = 'auto';
                s.style.padding = '32px 48px';
            }} else {{
                s.style.display = 'none';
            }}
        }});
        // Enlarge all text inside the zoomed panel so it is readable in the video
        const sec = document.getElementById('{panel_id}');
        if (sec) {{
            sec.style.fontSize = '18px';
            sec.querySelectorAll('*').forEach(el => {{
                const cs = getComputedStyle(el);
                const px = parseFloat(cs.fontSize);
                if (px && px < 16) el.style.fontSize = '16px';
            }});
        }}
    }})()""")
    await page.wait_for_timeout(400)


async def _restore_layout(page):
    """Restore the original grid layout after a panel zoom."""
    await page.evaluate("""(() => {
        const hdr = document.querySelector('header');
        const bar = document.querySelector('.prompt-bar');
        if (hdr) hdr.style.display = '';
        if (bar) bar.style.display = '';
        const main = document.querySelector('main');
        if (main) {
            main.style.display = '';
            main.style.height = '';
            main.style.overflow = '';
        }
        document.querySelectorAll('main > section').forEach(s => {
            s.style.display = '';
            s.style.height = '';
            s.style.overflow = '';
            s.style.padding = '';
            s.style.fontSize = '';
            // Reset any inline font-size overrides on children
            s.querySelectorAll('*').forEach(el => { el.style.fontSize = ''; });
        });
    })()""")
    await page.wait_for_timeout(400)


async def _capture_video_frames(page, video_dir: Path) -> Path:
    """Run every demo end-to-end, capturing frames throughout execution.

    For each demo the video shows:
    1. The empty dashboard with the agent graph
    2. The demo running — periodic snapshots while events stream in
    3. The completed dashboard overview
    4. A zoomed full-viewport view of the stream panel (scrolled)
    5. A zoomed full-viewport view of the agent-output panel (scrolled)
    6. A zoomed full-viewport view of the timeline panel (scrolled)

    No length constraint — every demo runs to completion and all content is shown.
    """
    temp = Path(tempfile.mkdtemp(prefix="agentpat_frames_"))
    frames: list[tuple[Path, float]] = []
    idx = 0

    async def snap(duration: float):
        nonlocal idx
        idx += 1
        p = temp / f"frame_{idx:04d}.png"
        await page.screenshot(path=str(p), full_page=False)
        frames.append((p, duration))

    # --- Launcher intro ---
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    await snap(4)

    cards = await page.query_selector_all(".demo-card")
    for card in cards:
        await card.hover()
        await page.wait_for_timeout(400)
    await snap(3)

    # --- Each demo: full end-to-end ---
    for demo_id in DEMOS:
        title = DEMO_TITLES[demo_id]
        print(f"  [video] Starting: {title}")

        # Navigate to demo dashboard
        await page.goto(f"{BASE_URL}/demo/{demo_id}", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await snap(3)  # empty dashboard showing agent graph topology

        # Trigger the demo
        await page.evaluate("sendPrompt()")
        await page.wait_for_timeout(2000)  # let it start

        # --- Capture periodic frames WHILE the demo is running ---
        deadline = time.time() + 300  # 5 min max per demo
        running = True
        snap_interval = 4  # seconds between live captures
        while running and time.time() < deadline:
            # Scroll stream to bottom so latest events are visible
            await page.evaluate("""
                const s = document.getElementById('stream-messages');
                if (s) s.scrollTop = s.scrollHeight;
                const a = document.getElementById('agent-outputs');
                if (a) a.scrollTop = a.scrollHeight;
            """)
            await page.wait_for_timeout(500)
            await snap(snap_interval)

            # Check if demo finished
            try:
                status = await page.evaluate(
                    "fetch('/api/status').then(r => r.json())"
                )
                running = status.get("running", False)
            except Exception:
                pass
            if running:
                await page.wait_for_timeout(int(snap_interval * 1000))

        # Final settle after completion
        await page.wait_for_timeout(2000)
        print(f"  [video] {'Completed' if not running else 'Timed out'}: {title}")

        # --- Full completed dashboard overview ---
        await page.evaluate("""
            const s = document.getElementById('stream-messages');
            if (s) s.scrollTop = s.scrollHeight;
            const a = document.getElementById('agent-outputs');
            if (a) a.scrollTop = a.scrollHeight;
        """)
        await page.wait_for_timeout(500)
        await snap(4)  # overview hold

        # --- Zoom stream panel: scroll through all content ---
        print(f"  [video] Zooming stream: {title}")
        await _zoom_panel(page, "stream-panel")
        await page.evaluate(
            "document.getElementById('stream-messages').scrollTop = 0;"
        )
        await page.wait_for_timeout(400)
        await _scroll_panel_frames(page, "stream-messages", snap, hold=3)
        await _restore_layout(page)

        # --- Zoom agent-output panel: scroll through all content ---
        print(f"  [video] Zooming agent outputs: {title}")
        await _zoom_panel(page, "agent-output-panel")
        await page.evaluate(
            "document.getElementById('agent-outputs').scrollTop = 0;"
        )
        await page.wait_for_timeout(400)
        await _scroll_panel_frames(page, "agent-outputs", snap, hold=3)
        await _restore_layout(page)

        # --- Zoom timeline panel: scroll through all content ---
        print(f"  [video] Zooming timeline: {title}")
        await _zoom_panel(page, "timeline-panel")
        await page.evaluate(
            "document.getElementById('timeline-container').scrollTop = 0;"
        )
        await page.wait_for_timeout(400)
        await _scroll_panel_frames(page, "timeline-container", snap, hold=2)
        await _restore_layout(page)

        # Hold on the final dashboard one more time
        await snap(3)

    # --- Back to launcher ---
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    await snap(4)

    # --- Build video via ffmpeg concat (native resolution, no downscale) ---
    concat_file = temp / "concat.txt"
    with open(concat_file, "w") as f:
        for fp, dur in frames:
            safe = str(fp).replace("\\", "/")
            f.write(f"file '{safe}'\n")
            f.write(f"duration {dur}\n")
        safe = str(frames[-1][0]).replace("\\", "/")
        f.write(f"file '{safe}'\n")

    mp4_path = video_dir / "demo_walkthrough.mp4"
    print(f"[*] Building video from {len(frames)} captured frames...")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-vf", "fps=25",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-pix_fmt", "yuv420p",
            str(mp4_path),
        ],
        capture_output=True,
        text=True,
    )

    shutil.rmtree(temp, ignore_errors=True)
    return mp4_path


async def main(with_video: bool = False, video_only: bool = False, short_demo: bool = False):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # Start the app server
    print("[*] Starting app server...")
    env = os.environ.copy()
    env["HOST"] = "127.0.0.1"
    env["PYTHONIOENCODING"] = "utf-8"
    server_proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    try:
        await wait_for_server(BASE_URL)
        print(f"[*] Server running at {BASE_URL}")

        async with async_playwright() as p:
            # Screenshots (skip when --video-only)
            if not video_only:
                print("\n[*] Capturing screenshots...")
                browser = await p.chromium.launch(headless=False, channel="msedge")
                context = await browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    device_scale_factor=2,
                )
                page = await context.new_page()
                page.set_default_timeout(60000)
                await capture_screenshots(page, SCREENSHOT_DIR)
                await context.close()
                await browser.close()
                print(f"[*] Screenshots saved to: {SCREENSHOT_DIR}")

            # Video
            if with_video:
                print("\n[*] Recording video...")
                VIDEO_DIR.mkdir(parents=True, exist_ok=True)

                if short_demo:
                    # Short demo: Playwright video recorder with JSONL replay
                    browser = await p.chromium.launch(headless=False, channel="msedge")
                    context = await browser.new_context(
                        viewport={"width": 1440, "height": 900},
                        record_video_dir=str(VIDEO_DIR),
                        record_video_size={"width": 1440, "height": 900},
                    )
                    page = await context.new_page()
                    await record_short_demo(page, VIDEO_DIR)
                    await context.close()
                    await browser.close()

                    video_files = list(VIDEO_DIR.glob("*.webm"))
                    if video_files:
                        latest = max(video_files, key=lambda f: f.stat().st_mtime)
                        webm_path = VIDEO_DIR / "short_demo.webm"
                        if webm_path.exists():
                            webm_path.unlink()
                        latest.rename(webm_path)
                        mp4_path = VIDEO_DIR / "short_demo.mp4"
                        print("[*] Converting to mp4...")
                        conv = subprocess.run(
                            ["ffmpeg", "-y", "-i", str(webm_path),
                             "-c:v", "libx264", "-preset", "fast",
                             "-crf", "23", "-pix_fmt", "yuv420p",
                             str(mp4_path)],
                            capture_output=True, text=True,
                        )
                        if conv.returncode == 0 and mp4_path.exists():
                            size_mb = mp4_path.stat().st_size / 1_048_576
                            print(f"[*] Video saved to: {mp4_path} ({size_mb:.1f} MB)")
                        else:
                            print("[!] ffmpeg conversion failed (is ffmpeg installed?)")
                            print(f"[*] Raw video at: {webm_path}")
                else:
                    # Full walkthrough: screenshot-based video (avoids
                    # headless rendering issues with Playwright video recorder)
                    browser = await p.chromium.launch(headless=False, channel="msedge")
                    context = await browser.new_context(
                        viewport={"width": 1440, "height": 900},
                        device_scale_factor=2,
                    )
                    page = await context.new_page()
                    page.set_default_timeout(60000)
                    mp4_path = await _capture_video_frames(page, VIDEO_DIR)
                    await context.close()
                    await browser.close()
                    if mp4_path.exists():
                        size_mb = mp4_path.stat().st_size / 1_048_576
                        print(f"[*] Video saved to: {mp4_path} ({size_mb:.1f} MB)")
                    else:
                        print("[!] Failed to create video")

    finally:
        print("\n[*] Shutting down server...")
        server_proc.terminate()
        server_proc.wait(timeout=5)
        print("[*] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture screenshots and video of the demo pack")
    parser.add_argument("--video", action="store_true", help="Also record a full walkthrough video")
    parser.add_argument("--video-only", action="store_true", help="Record full video only (skip screenshots)")
    parser.add_argument("--short-demo", action="store_true", help="Record a ~60s video using instant JSONL replay (outputs short_demo.mp4)")
    args = parser.parse_args()
    short = args.short_demo
    do_video = args.video or args.video_only or short
    do_video_only = args.video_only or (short and not args.video)
    asyncio.run(main(with_video=do_video, video_only=do_video_only, short_demo=short))
