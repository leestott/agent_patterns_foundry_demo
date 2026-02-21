/**
 * Live stream panel: real-time message display with agent coloring.
 */

function appendStream(event) {
    const panel = document.getElementById('stream-messages');

    const div = document.createElement('div');
    div.className = `stream-event ${event.type}`;

    const agentName = event.data?.agent || 'System';
    const message = event.data?.message || event.data?.output || event.data?.error || event.data?.input || '';

    let content = `<span class="stream-agent">${escapeHtml(agentName)}</span>`;
    content += `<span class="stream-type">${escapeHtml(event.type)}</span>`;
    if (message) {
        content += `<div class="stream-text">${escapeHtml(message)}</div>`;
    }

    // Show pattern info for orchestrator events
    if (event.data?.pattern) {
        content += `<div class="stream-text" style="color:#8b949e">Orchestration: ${escapeHtml(event.data.pattern)}</div>`;
    }
    if (event.data?.participants) {
        content += `<div class="stream-text" style="color:#8b949e">Agents: ${escapeHtml(event.data.participants.join(' → '))}</div>`;
    }

    div.innerHTML = content;
    
    const isAtBottom = panel.scrollHeight - panel.scrollTop <= panel.clientHeight + 50;
    panel.appendChild(div);
    if (isAtBottom) {
        panel.scrollTop = panel.scrollHeight;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
