import Store from '../store.js';
import { icon } from '../components/Icon.js';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const GCOLORS = {
  entity: '#4CAF50', concept: '#2196F3', comparison: '#FF9800', query: '#9C27B0', raw: '#607D8B',
  project: '#E91E63', plan: '#795548', note: '#00BCD4', idea: '#FF5722',
  goal: '#4CAF50', milestone: '#FF9800', okr: '#E91E63', todo: '#9C27B0',
  deliverable: '#00BCD4', reminder: '#FFC107'
};
const GTYPE_NAMES = {
  entity: 'Entidades', concept: 'Conceptos', comparison: 'Comparaciones', query: 'Consultas', raw: 'Raw',
  project: 'Proyectos', plan: 'Planes', note: 'Notas', idea: 'Ideas',
  goal: 'Goals', milestone: 'Hitos', okr: 'OKRs', todo: 'Todo', deliverable: 'Entregables', reminder: 'Reminders'
};

export function renderGraph() {
  const container = document.getElementById('view-graph');
  if (!container) return;
  setActiveView('view-graph');

  const graph = Store.state.graph || { nodes: [], edges: [], counts: {} };
  const nodeCount = graph.nodes.length;
  const edgeCount = graph.edges.length;

  let html = `<div class="view-header"><div class="view-title-row"><h1>${icon('share', 20)}<span>Graph</span></h1></div>`
    + `<p class="view-subtitle">${nodeCount} nodos · ${edgeCount} aristas</p></div>`;

  if (!graph.nodes.length) {
    html += '<p style="padding:20px;color:var(--mute)">No hay datos para el grafo.</p>';
    container.innerHTML = html;
    return;
  }

  html += `<div class="graph-wrap"><div id="graph-view" style="height:65vh;"></div><div id="graph-legend" class="graph-legend"></div></div>`;
  container.innerHTML = html;

  const legend = document.getElementById('graph-legend');
  if (legend) {
    let lh = '';
    const counts = graph.counts || {};
    for (const group in counts) {
      const color = GCOLORS[group] || '#888';
      const label = GTYPE_NAMES[group] || group;
      lh += `<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color};margin-right:4px;"></span>${label} (${counts[group]})</div>`;
    }
    legend.innerHTML = lh;
  }

  const nodes = new vis.DataSet(graph.nodes.map(n => ({
    id: n.id,
    label: n.label,
    color: { background: n.color, border: '#333' },
    font: { color: '#333', size: 11 },
    shape: 'dot',
    size: 18
  })));

  const edges = new vis.DataSet(graph.edges.map(e => ({
    from: e.from,
    to: e.to,
    color: { color: '#ccc', opacity: 0.6 },
    arrows: { to: { enabled: true, scaleFactor: 0.5 } }
  })));

  window._net = new vis.Network(
    document.getElementById('graph-view'),
    { nodes, edges },
    {
      physics: {
        forceAtlas2Based: { gravitationalConstant: -50, centralGravity: 0.01, springLength: 150, springConstant: 0.08 },
        maxVelocity: 50,
        solver: 'forceAtlas2Based',
        timestep: 0.35,
        stabilization: { iterations: 150 }
      },
      interaction: { hover: true, zoomView: true, dragView: true },
      edges: { smooth: { type: 'continuous' } }
    }
  );

  window._net.once('afterDrawing', () => window._net.fit());
  window._net.fit();
}

export function renderProjectGraph(d) {
  if (!d || !d.p) return;

  const container = document.getElementById('project-graph-view');
  if (!container) return;

  const colors = {
    goal: '#4CAF50', milestone: '#FF9800', todo: '#9C27B0', concept: '#2196F3', entity: '#4CAF50',
    project: '#E91E63', reminder: '#FFC107', deliverable: '#00BCD4', file: '#607D8B', journal: '#795548'
  };

  const nodes = [{ id: 'project', label: d.p.title, color: { background: '#E91E63', border: '#333' }, font: { color: '#333', size: 14 }, shape: 'dot', size: 25 }];
  const edges = [];

  d.goals.forEach((g, i) => {
    const nid = 'goal_' + i;
    nodes.push({ id: nid, label: g.title, color: { background: colors[g.type] || '#4CAF50', border: '#333' }, font: { color: '#333', size: 11 }, shape: 'dot', size: 16 });
    edges.push({ from: 'project', to: nid, color: { color: '#ccc', opacity: 0.6 } });
  });

  d.todos.forEach((t, i) => {
    const nid = 'todo_' + i;
    nodes.push({ id: nid, label: t.title, color: { background: colors.todo, border: '#333' }, font: { color: '#333', size: 10 }, shape: 'dot', size: 14 });
    edges.push({ from: 'project', to: nid, color: { color: '#ddd', opacity: 0.4 } });
  });

  d.rems.forEach((r, i) => {
    const nid = 'rem_' + i;
    nodes.push({ id: nid, label: r.title, color: { background: colors.reminder, border: '#333' }, font: { color: '#333', size: 10 }, shape: 'dot', size: 14 });
    edges.push({ from: 'project', to: nid, color: { color: '#ddd', opacity: 0.4 } });
  });

  const nds = new vis.DataSet(nodes);
  const eds = new vis.DataSet(edges);
  const pnet = new vis.Network(container, { nodes: nds, edges: eds }, {
    physics: { barnesHut: { gravitationalConstant: -2000, centralGravity: 0.3, springLength: 120, springConstant: 0.04 }, maxVelocity: 50, solver: 'barnesHut', stabilization: { iterations: 100 } },
    interaction: { hover: true, zoomView: true, dragView: true },
    edges: { smooth: { type: 'continuous' } }
  });
  if (pnet) pnet.fit();

  const ptypes = [];
  if (d.goals.length) ptypes.push({ label: 'Goals', count: d.goals.length, color: '#4CAF50' });
  if (d.todos.length) ptypes.push({ label: 'Tareas', count: d.todos.length, color: '#9C27B0' });
  if (d.rems.length) ptypes.push({ label: 'Reminders', count: d.rems.length, color: '#FFC107' });
  ptypes.push({ label: 'Proyecto', count: 1, color: '#E91E63' });

  const ptCounts = {};
  if (d.p && d.p.body) {
    const links = (d.p.body.match(/\[\[([^\]]+)\]\]/g) || []).map(l => l.replace(/[\[\]]/g, '').split('|')[0].trim());
    links.forEach(slug => {
      const pp = Store.mapPages()[slug];
      if (pp) {
        const t = pp.page_type || 'concept';
        ptCounts[t] = (ptCounts[t] || 0) + 1;
      }
    });
  }
  const ptLabels = { entity: 'Entidades', concept: 'Conceptos', comparison: 'Comparaciones', query: 'Consultas', raw: 'Raw', plan: 'Planes', note: 'Notas', idea: 'Ideas' };
  const ptColors = { entity: '#4CAF50', concept: '#2196F3', comparison: '#FF9800', query: '#9C27B0', raw: '#607D8B', plan: '#795548', note: '#00BCD4', idea: '#FF5722' };
  Object.keys(ptLabels).forEach(t => {
    if (ptCounts[t]) ptypes.push({ label: ptLabels[t], count: ptCounts[t], color: ptColors[t] });
  });

  const lgc = document.getElementById('project-graph-legend');
  if (lgc) {
    let plh = '<div style="display:flex;gap:12px;flex-wrap:wrap;font-size:11px;margin-top:8px;">';
    ptypes.forEach(pt => {
      plh += `<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${pt.color};margin-right:4px;"></span>${pt.label} (${pt.count})</div>`;
    });
    plh += '</div>';
    lgc.innerHTML = plh;
    lgc.style.display = 'block';
  }
}

export default renderGraph;
