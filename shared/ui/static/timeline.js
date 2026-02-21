/**
 * Timeline view: chronological event list with detail inspector.
 */

let startTime = null;

function appendTimeline(event) {
    if (!startTime) startTime = event.timestamp;
    const container = document.getElementById('timeline-container');

    const entry = document.createElement('div');
    entry.className = 'timeline-entry';
    entry.onclick = () => showDetail(event, entry);

    const elapsed = ((event.timestamp - startTime) * 1000).toFixed(0);

    entry.innerHTML = `
        <span class="timeline-dot ${escapeAttr(event.type)}"></span>
        <span class="timeline-time">+${elapsed}ms</span>
        <span class="timeline-label">
            <strong>${escapeHtml(event.data?.agent || '—')}</strong>
            ${escapeHtml(event.type)}
            ${event.data?.message ? ': ' + escapeHtml(truncate(event.data.message, 60)) : ''}
        </span>
    `;

    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;
    container.appendChild(entry);
    if (isAtBottom) {
        container.scrollTop = container.scrollHeight;
    }
}

function showDetail(event, entry) {
    // Highlight selected
    document.querySelectorAll('.timeline-entry').forEach(e => e.classList.remove('selected'));
    entry.classList.add('selected');

    const detail = document.getElementById('detail-content');
    detail.textContent = JSON.stringify(event, null, 2);
}

function truncate(str, len) {
    return str.length > len ? str.substring(0, len) + '…' : str;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    return escapeHtml(text).replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}
