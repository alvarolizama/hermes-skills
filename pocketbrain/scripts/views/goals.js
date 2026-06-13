import Store from '../store.js';
import { Tabs, bindTabs } from '../components/Tabs.js';
import { setHashParams } from '../router.js';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const TAB_IDS = ['all', 'active', 'backlog', 'completed', 'cancelled'];
const TAB_LABELS = {
  all: 'Todos',
  active: 'Activos',
  backlog: 'Backlog',
  completed: 'Terminados',
  cancelled: 'Cancelados'
};

export function renderGoalsView(typeFilter = 'goal') {
  const containerId = typeFilter === 'milestone' ? 'view-milestones' : 'view-goals';
  const container = document.getElementById(containerId);
  if (!container) return;

  const gf = Store.get('filters').goal || '';
  let filtered = Store.get('goals').filter(g => g.type === typeFilter);

  if (gf === 'project') {
    filtered = filtered.filter(g => !!g.page_slug);
  } else if (gf === 'noproject') {
    filtered = filtered.filter(g => !g.page_slug);
  }

  const counts = {
    all: filtered.length,
    active: filtered.filter(g => g.status === 'active' || g.status === 'planned').length,
    backlog: filtered.filter(g => g.status === 'backlog').length,
    completed: filtered.filter(g => g.status === 'completed').length,
    cancelled: filtered.filter(g => g.status === 'cancelled').length
  };

  const status = Store.get('goalStatus') || 'all';
  if (status === 'active') {
    filtered = filtered.filter(g => g.status === 'active' || g.status === 'planned');
  } else if (status === 'backlog') {
    filtered = filtered.filter(g => g.status === 'backlog');
  } else if (status === 'completed') {
    filtered = filtered.filter(g => g.status === 'completed');
  } else if (status === 'cancelled') {
    filtered = filtered.filter(g => g.status === 'cancelled');
  }

  const label = typeFilter === 'milestone' ? 'Milestones' : 'Goals';

  let html = `<div class="view-header"><h1>${esc(label)}</h1>`
    + `<select data-pb-filter="goal" style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)">`
    + `<option value="" ${gf === '' ? 'selected' : ''}>Todos</option>`
    + `<option value="project" ${gf === 'project' ? 'selected' : ''}>Con proyecto</option>`
    + `<option value="noproject" ${gf === 'noproject' ? 'selected' : ''}>Sin proyecto</option>`
    + `</select></div>`;

  html += Tabs({
    items: TAB_IDS.map(id => ({ id, label: TAB_LABELS[id] })),
    active: status,
    counts
  });

  html += `<p style="color:var(--mute);margin-bottom:20px">${filtered.length} ${esc(label.toLowerCase())}</p>`;

  if (!filtered.length) {
    html += '<p style="color:var(--mute)">No hay items.</p>';
  } else {
    filtered.forEach(g => {
      html += `<div class="card" style="cursor:pointer;margin-bottom:8px;padding:12px" data-pb-goal="${esc(g.slug)}">`
        + `<h3>${esc(g.title)}</h3>`
        + `</div>`;
    });
  }

  container.innerHTML = html;

  const select = container.querySelector('select[data-pb-filter="goal"]');
  if (select) {
    select.addEventListener('change', e => {
      Store.setFilter('goal', e.target.value);
      renderGoalsView(typeFilter);
    });
  }

  const tabsRoot = container.querySelector('.project-tabs');
  if (tabsRoot) {
    bindTabs(tabsRoot, id => {
      Store.set('goalStatus', id);
      const tab = typeFilter === 'milestone' ? 'milestones' : 'goals';
      setHashParams({ tab, gstatus: id });
      renderGoalsView(typeFilter);
    });
  }

  container.querySelectorAll('[data-pb-goal]').forEach(el => {
    el.addEventListener('click', () => {
      const slug = el.dataset.pbGoal;
      const g = Store.state.goals.find(x => x.slug === slug);
      if (g && g.page_slug && typeof window.showPage === 'function') {
        window.showPage(g.page_slug);
      } else if (slug && typeof window.showPage === 'function') {
        window.showPage(slug);
      }
    });
  });
}

export default renderGoalsView;
