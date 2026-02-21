/**
 * D3.js force-directed graph renderer for agent topology.
 * Nodes = agents, edges = interaction routes.
 * Active agent highlighted with glow effect.
 */

let graphSim, graphNodes, graphLinks, nodeElements, linkElements, graphGroup, graphZoom;
const nodeColorMap = {};
const COLORS = ['#58a6ff','#3fb950','#d29922','#a371f7','#f78181','#79c0ff','#56d364','#e3b341'];

function initGraph(topology) {
    const svg = d3.select('#graph-svg');
    const rect = svg.node().getBoundingClientRect();
    const w = rect.width || 500, h = rect.height || 400;

    svg.selectAll('*').remove();

    // Zoom behaviour — scroll wheel + pinch + buttons
    graphZoom = d3.zoom()
        .scaleExtent([0.2, 4])
        .on('zoom', event => graphGroup && graphGroup.attr('transform', event.transform));
    svg.call(graphZoom).on('dblclick.zoom', null);

    // Arrow marker
    svg.append('defs').append('marker')
        .attr('id', 'arrow').attr('viewBox', '0 0 10 10')
        .attr('refX', 20).attr('refY', 5)
        .attr('markerWidth', 6).attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path').attr('d', 'M 0 0 L 10 5 L 0 10 Z').attr('fill', '#30363d');

    // Build nodes/links from topology
    const nodes = (topology.nodes || []).map((n, i) => {
        nodeColorMap[n.id || n.name] = COLORS[i % COLORS.length];
        return { id: n.id || n.name, label: n.label || n.name, role: n.role || '', ...n };
    });

    const links = (topology.edges || []).map(e => ({
        source: e.from || e.source,
        target: e.to || e.target,
        label: e.label || ''
    }));

    graphNodes = nodes;
    graphLinks = links;

    // Inner group — zoom transform is applied here
    graphGroup = svg.append('g');
    linkElements = graphGroup.selectAll('.link').data(links).join('line')
        .attr('class', 'link');

    // Nodes
    nodeElements = graphGroup.selectAll('.node').data(nodes, d => d.id).join('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragStart)
            .on('drag', dragged)
            .on('end', dragEnd));

    nodeElements.append('circle')
        .attr('r', 20)
        .attr('fill', d => nodeColorMap[d.id] + '33')
        .attr('stroke', d => nodeColorMap[d.id]);

    nodeElements.append('text')
        .attr('dy', 32)
        .text(d => d.label);

    // Role subtitle
    nodeElements.append('text')
        .attr('dy', 44).attr('class', 'role-text')
        .style('font-size', '9px').style('fill', '#8b949e')
        .text(d => d.role);

    // Simulation
    graphSim = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(120))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(w / 2, h / 2))
        .on('tick', () => {
            linkElements.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
            nodeElements.attr('transform', d => `translate(${d.x},${d.y})`);
        });

    // Legend
    const legend = document.getElementById('graph-legend');
    legend.innerHTML = '';
    nodes.forEach(n => {
        const span = document.createElement('span');
        span.style.color = nodeColorMap[n.id];
        span.textContent = `● ${n.label}`;
        legend.appendChild(span);
    });
}

function updateGraph(event) {
    if (!nodeElements) return;
    const agent = event.data?.agent;
    if (!agent) return;

    // Highlight active node
    nodeElements.classed('active', d => d.id === agent || d.label === agent);
    nodeElements.select('circle')
        .attr('stroke-width', d => (d.id === agent || d.label === agent) ? 3 : 2)
        .style('color', d => nodeColorMap[d.id]);

    // Highlight active edges
    if (event.type === 'handoff' && event.data?.from_agent) {
        linkElements.classed('active', d =>
            (d.source.id === event.data.from_agent && d.target.id === agent) ||
            (d.source.id === agent)
        );
    } else if (event.type === 'agent_message') {
        linkElements.classed('active', d => d.source.id === agent || d.source.label === agent);
        setTimeout(() => linkElements.classed('active', false), 1500);
    }
}

function resetGraphHighlights() {
    if (nodeElements) nodeElements.classed('active', false);
    if (linkElements) linkElements.classed('active', false);
}

function dragStart(event, d) {
    if (!event.active) graphSim.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
}
function dragged(event, d) { d.fx = event.x; d.fy = event.y; }
function dragEnd(event, d) {
    if (!event.active) graphSim.alphaTarget(0);
    d.fx = null; d.fy = null;
}

// Zoom controls (called by toolbar buttons)
// Scales around the centre of the SVG viewport so nodes stay in view
function _svgCenter() {
    const node = document.getElementById('graph-svg');
    if (!node) return [250, 200];
    const r = node.getBoundingClientRect();
    return [r.width / 2, r.height / 2];
}
function zoomIn()    { if (!graphZoom) return; const c = _svgCenter(); d3.select('#graph-svg').transition().duration(300).call(graphZoom.scaleBy, 1.4, c); }
function zoomOut()   { if (!graphZoom) return; const c = _svgCenter(); d3.select('#graph-svg').transition().duration(300).call(graphZoom.scaleBy, 1 / 1.4, c); }
function zoomReset() { if (!graphZoom) return; d3.select('#graph-svg').transition().duration(400).call(graphZoom.transform, d3.zoomIdentity); }

// Wire up buttons — DOM is ready since this script is at the end of <body>
document.getElementById('btn-zoom-in')   ?.addEventListener('click', zoomIn);
document.getElementById('btn-zoom-out')  ?.addEventListener('click', zoomOut);
document.getElementById('btn-zoom-reset')?.addEventListener('click', zoomReset);
