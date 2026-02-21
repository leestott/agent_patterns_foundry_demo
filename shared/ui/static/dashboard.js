const demoId = window.location.pathname.split('/').pop();
// Track per-agent outputs: { agentName: [messages] }
const agentOutputs = {};

async function sendPrompt() {
    const promptEl = document.getElementById('prompt-input');
    const prompt = promptEl.value.trim();
    clearAll();
    const res = await fetch(`/api/run/${demoId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt || null }),
    });
    const data = await res.json();
    if (data.status === 'started') {
        const status = document.getElementById('run-status');
        status.className = 'run-status';
        status.querySelector('span:last-child').textContent = 'Running';
        const tRes = await fetch('/api/topology');
        const topo = await tRes.json();
        if (topo.nodes && topo.nodes.length > 0) initGraph(topo);
    }
}

(async () => {
    // Fetch demo metadata
    const demosRes = await fetch('/api/demos');
    const demos = await demosRes.json();
    const demo = demos.find(d => d.id === demoId);
    if (demo) {
        document.getElementById('demo-title').textContent = demo.title;
        document.title = `Agent Patterns — ${demo.title}`;
    }

    // Pre-fill prompt with the demo's suggested prompt
    const promptEl = document.getElementById('prompt-input');
    if (demo && demo.suggested_prompt) {
        promptEl.value = demo.suggested_prompt;
    }

    // Fetch topology
    const topoRes = await fetch('/api/topology');
    const topology = await topoRes.json();

    // Show pattern badge
    const badge = document.getElementById('pattern-badge');
    if (topology.pattern) {
        badge.textContent = `Pattern: ${topology.pattern}`;
        badge.className = `badge badge-${topology.pattern.toLowerCase().replace(/[ /]+/g, '-')}`;
    }

    // Initialize graph
    if (topology.nodes && topology.nodes.length > 0) {
        initGraph(topology);
    }

    // Connect WebSocket
    const ws = new WebSocket(`ws://${location.host}/ws`);
    ws.onmessage = (e) => {
        const event = JSON.parse(e.data);
        handleEvent(event);
    };
    ws.onclose = () => {
        const status = document.getElementById('run-status');
        status.className = 'run-status stopped';
        status.querySelector('span:last-child').textContent = 'Completed';
    };

    // Load existing events
    const eventsRes = await fetch('/api/events');
    const events = await eventsRes.json();
    events.forEach(handleEvent);

    // Poll for status
    async function pollStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            const status = document.getElementById('run-status');
            if (data.running && data.demo_id === demoId) {
                status.className = 'run-status';
                status.querySelector('span:last-child').textContent = 'Running';
            } else if (data.demo_id === demoId) {
                status.className = 'run-status stopped';
                status.querySelector('span:last-child').textContent = 'Completed';
            } else {
                status.className = 'run-status stopped';
                status.querySelector('span:last-child').textContent = 'Idle';
            }
        } catch (e) {}
    }
    setInterval(pollStatus, 2000);

    // Re-run button — re-sends with current prompt
    document.getElementById('btn-rerun').onclick = () => sendPrompt();

    // Replay button
    document.getElementById('btn-replay').onclick = async () => {
        const path = prompt('Enter JSONL file path:');
        if (!path) return;
        const replayRes = await fetch('/api/replay', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path}),
        });
        if (!replayRes.ok) { alert('File not found'); return; }
        const replayEvents = await replayRes.json();
        clearAll();
        for (const ev of replayEvents) {
            handleEvent(ev);
            await new Promise(r => setTimeout(r, 300));
        }
    };

    // Clear button
    document.getElementById('btn-clear').onclick = clearAll;
})();

function handleEvent(event) {
    updateGraph(event);
    appendStream(event);
    appendTimeline(event);
    trackAgentOutput(event);
}

function trackAgentOutput(event) {
    const agentName = event.data?.agent;
    if (!agentName || agentName === 'System' || agentName === 'Orchestrator') return;

    const message = event.data?.message || event.data?.output || '';
    if (!message) return;

    // Only track meaningful message types
    const tracked = ['agent_message', 'agent_completed', 'agent_started'];
    if (!tracked.includes(event.type)) return;

    if (!agentOutputs[agentName]) agentOutputs[agentName] = [];
    agentOutputs[agentName].push({ type: event.type, message, timestamp: event.data?.timestamp });
    renderAgentOutputs();
}

function renderAgentOutputs() {
    const container = document.getElementById('agent-outputs');
    container.innerHTML = '';
    const agents = Object.keys(agentOutputs);
    if (agents.length === 0) {
        container.innerHTML = '<div style="color:#484f58;font-size:12px;">Waiting for agent outputs…</div>';
        return;
    }
    agents.forEach(name => {
        const card = document.createElement('div');
        card.className = 'agent-output-card';
        card.setAttribute('role', 'region');
        card.setAttribute('aria-label', `Output from ${name}`);

        const header = document.createElement('div');
        header.className = 'agent-output-header';
        header.textContent = name;
        card.appendChild(header);

        const msgs = agentOutputs[name];
        msgs.forEach(m => {
            const line = document.createElement('div');
            line.className = `agent-output-line ${m.type}`;
            line.textContent = m.message;
            card.appendChild(line);
        });

        container.appendChild(card);
    });
    container.scrollTop = container.scrollHeight;
}

function clearAll() {
    document.getElementById('stream-messages').innerHTML = '';
    document.getElementById('timeline-container').innerHTML = '';
    document.getElementById('detail-content').textContent = 'Click a timeline event to inspect';
    document.getElementById('agent-outputs').innerHTML = '';
    // Clear tracked outputs
    Object.keys(agentOutputs).forEach(k => delete agentOutputs[k]);
    resetGraphHighlights();
}
