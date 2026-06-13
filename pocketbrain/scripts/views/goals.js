import Store from '../store.js';
import { Tabs, bindTabs } from '../components/Tabs.js';
import { icon } from '../components/Icon.js';
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
const TAB_ICONS = {
  all: 'squares-2x2',
  active: 'bolt',
  backlog: 'archive-box',
  completed: 'check-circle',
  cancelled: 'x-circle'
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
  const headerIcon = typeFilter === 'milestone' ? 'check-circle' : 'flag';

  let html = `<div class="view-header">`
    + `<div class="project-breadcrumb" style="margin-bottom:8px">`
    + `<a href="javascript:void(0)" data-pb-back-projects>${icon('arrow-left', 12)}<span>Proyectos</span></a>`
    + `<span class="project-breadcrumb-sep">/</span><span>${esc(label)}</span>`
    + `</div>`
    + `<div class="view-title-row"><h1>${icon(headerIcon, 20)}<span>${esc(label)}</span></h1>`
    + `<select data-pb-filter="goal" class="filter-select">`
    + `<option value="" ${gf === '' ? 'selected' : ''}>Todos</option>`
    + `<option value="project" ${gf === 'project' ? 'selected' : ''}>Con proyecto</option>`
    + `<option value="noproject" ${gf === 'noproject' ? 'selected' : ''}>Sin proyecto</option>`
    + `</select></div>`
    + `<p class="view-subtitle">${filtered.length} ${esc(label.toLowerCase())}</p></div>`;

  html += Tabs({
    items: TAB_IDS.map(id => ({ id, label: TAB_LABELS[id], icon: TAB_ICONS[id] })),
    active: status,
    counts
  });

  html += `<div class="cards-grid">`;

  if (!filtered.length) {
    html += '<p style="color:var(--mute)">No hay items.</p>';
  } else {
    filtered.forEach(g => {
      const chipClass = g.type === 'milestone' ? 'chip-milestone' : g.type === 'okr' ? 'chip-okr' : 'chip-goal';
      const chipLabel = g.type === 'milestone' ? 'Milestone' : g.type === 'okr' ? 'OKR' : 'Goal';
      const deadline = g.deadline ? ` · ${esc(g.deadline)}` : '';
      html += `<div class="card" style="cursor:pointer;margin-bottom:8px;padding:12px" data-pb-goal="${esc(g.slug)}">`
        + `<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">`
        + `<h3>${esc(g.title)}</h3>`
        + `<span class="chip ${chipClass}">${chipLabel}</span>`
        + `</div>`
        + `<div style="font-size:12px;color:var(--mute);margin-top:4px">${esc(g.status || 'planned')}${deadline}${g.page_slug ? ' · ' + esc(g.page_slug) : ''}</div>`
        + `</div>`;
    });
  }

  html += '</div>';

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

  const back = container.querySelector('[data-pb-back-projects]');
  if (back) {
    back.addEventListener('click', e => {
      e.preventDefault();
      if (typeof window.showTab === 'function') window.showTab('projects');
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
