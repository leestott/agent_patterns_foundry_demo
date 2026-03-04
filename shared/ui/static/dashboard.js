const demoId = window.location.pathname.split('/').pop();
// Track per-agent outputs: { agentName: [messages] }
const agentOutputs = {};

// Model provider state
let modelCfg = null;
let activeTab = 'foundry_local';

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

    // Load model provider info and populate the badge
    loadModelConfig();

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

// ── Model provider settings ────────────────────────────────────────────────

async function loadModelConfig() {
    try {
        const res = await fetch('/api/model-config');
        modelCfg = await res.json();
        updateProviderBadge(modelCfg.provider);
        applyConfigToPanel();
    } catch (e) {}
}

function updateProviderBadge(provider) {
    const btn = document.getElementById('btn-provider');
    if (!btn) return;
    if (provider === 'azure_foundry') {
        btn.textContent = '☁ Microsoft Foundry';
        btn.className = 'provider-pill cloud';
    } else {
        const model = modelCfg?.foundry_local?.model || 'Foundry Local';
        btn.textContent = `🖥 ${model}`;
        btn.className = 'provider-pill local';
    }
}

function openSettings() {
    document.getElementById('settings-overlay').classList.add('open');
    document.getElementById('tab-' + (activeTab === 'foundry_local' ? 'local' : 'cloud')).focus();
}

function closeSettings() {
    document.getElementById('settings-overlay').classList.remove('open');
}

function overlayClick(e) {
    if (e.target === document.getElementById('settings-overlay')) closeSettings();
}

function switchTab(tab) {
    activeTab = tab;
    document.getElementById('tab-local').classList.toggle('active', tab === 'foundry_local');
    document.getElementById('tab-cloud').classList.toggle('active', tab === 'azure_foundry');
    document.getElementById('tab-local').setAttribute('aria-selected', tab === 'foundry_local');
    document.getElementById('tab-cloud').setAttribute('aria-selected', tab === 'azure_foundry');
    document.getElementById('section-local').style.display = tab === 'foundry_local' ? '' : 'none';
    document.getElementById('section-cloud').style.display = tab === 'azure_foundry' ? '' : 'none';
}

function applyConfigToPanel() {
    if (!modelCfg) return;
    switchTab(modelCfg.provider || 'foundry_local');

    const sel = document.getElementById('local-model');
    const available = modelCfg.foundry_local?.available_models || [];
    const current = modelCfg.foundry_local?.model || '';
    sel.innerHTML = '';
    const models = available.includes(current) ? available : [current, ...available];
    models.filter(Boolean).forEach(m => {
        const opt = document.createElement('option');
        opt.value = m; opt.textContent = m;
        if (m === current) opt.selected = true;
        sel.appendChild(opt);
    });

    document.getElementById('local-endpoint').value = modelCfg.foundry_local?.endpoint_override || '';
    document.getElementById('azure-endpoint').value = modelCfg.azure_foundry?.endpoint || '';
    document.getElementById('azure-key').value = modelCfg.azure_foundry?.api_key === '***' ? '' : (modelCfg.azure_foundry?.api_key || '');
    document.getElementById('azure-model').value = modelCfg.azure_foundry?.model || '';
    document.getElementById('azure-deployment').value = modelCfg.azure_foundry?.deployment || '';

    updateProviderIndicator(modelCfg.provider);
}

function updateProviderIndicator(provider) {
    const ind = document.getElementById('active-provider-indicator');
    const txt = document.getElementById('active-provider-text');
    if (provider === 'azure_foundry') {
        ind.className = 'provider-indicator cloud';
        txt.textContent = 'Using: Microsoft Foundry';
    } else {
        ind.className = 'provider-indicator local';
        const model = modelCfg?.foundry_local?.model || 'Foundry Local';
        txt.textContent = `Using: Foundry Local (${model})`;
    }
    updateProviderBadge(provider);
}

async function saveSettings() {
    const msg = document.getElementById('save-msg');
    msg.textContent = '';
    msg.className = 'save-msg';

    const payload = {
        provider: activeTab,
        foundry_local: {
            model: document.getElementById('local-model').value,
            endpoint_override: document.getElementById('local-endpoint').value.trim(),
        },
        azure_foundry: {
            endpoint: document.getElementById('azure-endpoint').value.trim(),
            model: document.getElementById('azure-model').value.trim(),
            deployment: document.getElementById('azure-deployment').value.trim(),
        },
    };
    const keyVal = document.getElementById('azure-key').value;
    if (keyVal) payload.azure_foundry.api_key = keyVal;

    try {
        const res = await fetch('/api/model-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        modelCfg = await res.json();
        if (!res.ok) {
            msg.textContent = modelCfg.error || 'Save failed';
            msg.className = 'save-msg error';
            return;
        }
        applyConfigToPanel();
        msg.textContent = '✓ Settings saved';
        setTimeout(() => { msg.textContent = ''; }, 3000);
    } catch (e) {
        msg.textContent = 'Network error — could not save';
        msg.className = 'save-msg error';
    }
}

// Close settings on Escape
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSettings(); });
