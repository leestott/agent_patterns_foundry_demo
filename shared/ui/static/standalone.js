// Boot: fetch topology, connect WebSocket
(async () => {
    const res = await fetch('/api/topology');
    const topology = await res.json();

    // Show pattern badge
    const badge = document.getElementById('pattern-badge');
    if (topology.pattern) {
        badge.textContent = `Pattern: ${topology.pattern}`;
        badge.className = `badge badge-${topology.pattern.toLowerCase().replace(/[ /]+/g, '-')}`;
    }

    // Initialize graph
    initGraph(topology);

    // Connect WebSocket
    const ws = new WebSocket(`ws://${location.host}/ws`);
    ws.onmessage = (e) => {
        const event = JSON.parse(e.data);
        handleEvent(event);
    };
    ws.onclose = () => {
        console.log('WebSocket closed — events may have stopped');
    };

    // Load existing events
    const eventsRes = await fetch('/api/events');
    const events = await eventsRes.json();
    events.forEach(handleEvent);

    // Replay button
    document.getElementById('btn-replay').onclick = async () => {
        const path = prompt('Enter JSONL file path:');
        if (!path) return;
        const replayRes = await fetch('/api/replay', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({path}),
        });
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
}

function clearAll() {
    document.getElementById('stream-messages').innerHTML = '';
    document.getElementById('timeline-container').innerHTML = '';
    document.getElementById('detail-content').textContent = 'Click a timeline event to inspect';
    const agentOutputs = document.getElementById('agent-outputs');
    if (agentOutputs) agentOutputs.innerHTML = 'Waiting for agent outputs…';
    resetGraphHighlights();
}
