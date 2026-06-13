/**
 * Project detail view for PocketBrain.
 *
 * Renders a full project dashboard with metric cards and 12 tabs:
 * Contenido, Goals, Milestones, Ideas, Plans, Todo (kanban), Notes,
 * Reminders, Journal, Files, Pages, Graph.
 */

import Store from '../store.js';
import API from '../api.js';
import { icon } from '../components/Icon.js';
import { mdToHtml, bindMarkdownLinks } from '../markdown.js';
import { setHashParams } from '../router.js';
import { renderProjectGraph } from './graph.js';

const TAB_SPECS = [
  { id: 'content', label: 'Contenido', icon: 'document-text' },
  { id: 'goals', label: 'Goals', icon: 'flag' },
  { id: 'milestones', label: 'Milestones', icon: 'check-circle' },
  { id: 'ideas', label: 'Ideas', icon: 'light-bulb' },
  { id: 'plans', label: 'Planes', icon: 'calendar-days' },
  { id: 'todo', label: 'Todo', icon: 'clipboard-document-list' },
  { id: 'notes', label: 'Notas', icon: 'clock' },
  { id: 'reminders', label: 'Reminders', icon: 'bell' },
  { id: 'journal', label: 'Journal', icon: 'book-open' },
  { id: 'files', label: 'Archivos', icon: 'paper-clip' },
  { id: 'pages', label: 'Pages', icon: 'bars-3' },
  { id: 'graph', label: 'Graph', icon: 'circle' }
];

const KANBAN_COLUMNS = ['backlog', 'this week', 'today', 'in progress', 'done', 'cancelled'];
const COLUMN_LABELS = {
  backlog: 'BACKLOG',
  'this week': 'THIS WEEK',
  today: 'TODAY',
  'in progress': 'IN PROGRESS',
  done: 'DONE',
  cancelled: 'CANCELLED'
};

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeRegExp(string) {
  return String(string).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d)) return '';
  return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
}

function pageLinksTo(page, slug) {
  if (!page || !page.body) return false;
  const re = new RegExp('\\[\\[' + escapeRegExp(slug) + '\\]\\]|\\[\\[' + escapeRegExp(slug) + '\\|', 'gi');
  return re.test(page.body);
}

function isProjectRelated(page, slug) {
  if (!page || page.slug === slug) return false;
  return page.page_slug === slug || pageLinksTo(page, slug);
}

function collectProjectData(slug) {
  const pages = Store.state.pages || [];
  const p = Store.mapPages()[slug];

  const goals = (Store.state.goals || []).filter(g => g.page === slug || g.page_slug === slug);
  const todos = (Store.state.todos || []).filter(t => t.page_slug === slug);
  const reminders = (Store.state.reminders || []).filter(r => r.page_slug === slug);
  const journal = (Store.state.journal || []).filter(j => j.page_slug === slug);
  const files = (Store.state.files || []).filter(f => f.page_slug === slug);

  const relatedPages = pages.filter(pg => isProjectRelated(pg, slug));
  const ideas = relatedPages.filter(pg => pg.page_type === 'idea');
  const plans = relatedPages.filter(pg => pg.page_type === 'plan');
  const notes = relatedPages.filter(pg => pg.page_type === 'note');

  return {
    slug,
    p,
    goals,
    milestones: goals.filter(g => g.type === 'milestone'),
    goalItems: goals.filter(g => g.type !== 'milestone'),
    todos,
    reminders,
    journal,
    files,
    ideas,
    plans,
    notes,
    relatedPages
  };
}

function metricCard(label, value, sub, iconName) {
  const subHtml = sub ? `<div class="metric-sub">${esc(sub)}</div>` : '';
  const svg = iconName ? icon(iconName, 18) : '';
  return `<div class="metric-card">`
    + `<div class="metric-icon">${svg}</div>`
    + `<div class="metric-body">`
    + `<div class="metric-value">${esc(value)}</div>`
    + `<div class="metric-label">${esc(label)}</div>`
    + subHtml
    + `</div></div>`;
}

function renderMetrics(data) {
  const todoDone = data.todos.filter(t => t.status === 'done').length;
  const todoInProgress = data.todos.filter(t => t.status === 'in progress').length;
  const todoBacklog = data.todos.filter(t => t.status === 'backlog').length;

  let html = `<div class="project-metrics">`;
  html += metricCard('Goals', data.goalItems.length, null, 'flag');
  html += metricCard('Milestones', data.milestones.length, null, 'check-circle');
  html += metricCard('Todo', data.todos.length, `${todoDone} done · ${todoInProgress} in progress · ${todoBacklog} backlog`, 'clipboard-document-list');
  html += metricCard('Reminders', data.reminders.length, null, 'bell');
  html += metricCard('Journal', data.journal.length, null, 'book-open');
  html += metricCard('Files', data.files.length, null, 'paper-clip');
  html += metricCard('Notas', data.notes.length, null, 'clock');
  html += metricCard('Ideas', data.ideas.length, null, 'light-bulb');
  html += metricCard('Planes', data.plans.length, null, 'calendar-days');
  html += metricCard('Pages', data.relatedPages.length, null, 'bars-3');
  html += `</div>`;
  return html;
}

function tabCount(data, tabId) {
  switch (tabId) {
    case 'content': return 0;
    case 'goals': return data.goalItems.length;
    case 'milestones': return data.milestones.length;
    case 'ideas': return data.ideas.length;
    case 'plans': return data.plans.length;
    case 'todo': return data.todos.length;
    case 'notes': return data.notes.length;
    case 'reminders': return data.reminders.length;
    case 'journal': return data.journal.length;
    case 'files': return data.files.length;
    case 'pages': return data.relatedPages.length;
    case 'graph': return 0;
    default: return 0;
  }
}

function renderTabs(data, activeTab) {
  let html = `<div class="project-tabs">`;
  TAB_SPECS.forEach(spec => {
    const count = tabCount(data, spec.id);
    const countHtml = count ? ` <span class="nav-count">${count}</span>` : '';
    const activeClass = spec.id === activeTab ? 'active' : '';
    const svg = icon(spec.icon, 16);
    html += `<a href="javascript:void(0)" class="${activeClass}" data-pb-ptab="${esc(spec.id)}">`
      + `<span class="tab-label">${svg}<span>${esc(spec.label)}</span></span>${countHtml}`
      + `</a>`;
  });
  html += `</div>`;
  return html;
}

function renderContentTab(data) {
  const p = data.p;
  if (!p) return '<p style="color:var(--mute)">Proyecto no encontrado.</p>';

  let html = '';

  const meta = [];
  if (p.status) meta.push(['Estado', p.status]);
  if (p.tags && p.tags.length) meta.push(['Tags', Array.isArray(p.tags) ? p.tags.join(', ') : p.tags]);
  if (p.created) meta.push(['Creado', formatDate(p.created)]);
  if (p.updated) meta.push(['Actualizado', formatDate(p.updated)]);

  if (meta.length) {
    html += `<div class="meta" style="margin-bottom:16px">`;
    html += meta.map(([k, v]) => `<span>${esc(k)}: ${esc(v)}</span>`).join('');
    html += `</div>`;
  }

  html += `<div class="card md-content">${window.mdToHtml ? window.mdToHtml(p.body || '') : esc(p.body || '')}</div>`;

  const backlinks = p.backlinks || [];
  if (backlinks.length) {
    html += `<div class="backlink-section"><h3>Backlinks</h3>`;
    backlinks.forEach(b => {
      html += `<a href="javascript:void(0)" data-pb-page="${esc(b.slug)}">${esc(b.title)}</a>`;
    });
    html += `</div>`;
  }

  return html;
}

function renderGoalCard(g) {
  const chipClass = g.type === 'milestone' ? 'chip-milestone' : g.type === 'okr' ? 'chip-okr' : 'chip-goal';
  const chipLabel = g.type === 'milestone' ? 'Milestone' : g.type === 'okr' ? 'OKR' : 'Goal';
  const deadline = g.deadline ? ` · ${esc(g.deadline)}` : '';
  return `<div class="card project-item-card" data-pb-page="${esc(g.slug || g.id)}">`
    + `<div class="project-item-header">`
    + `<h3>${esc(g.title)}</h3>`
    + `<span class="chip ${chipClass}">${chipLabel}</span>`
    + `</div>`
    + `<div class="project-item-meta">${esc(g.status || 'planned')}${deadline}</div>`
    + `</div>`;
}

function renderTodoCard(t, showMove = true) {
  const goalMeta = t.goal_title ? ` · ${esc(t.goal_title)}` : '';
  let html = `<div class="card project-item-card" data-pb-page="${esc(t.slug || t.id)}">`
    + `<h3>${esc(t.title)}</h3>`
    + `<div class="project-item-meta">${esc(t.status || 'backlog')}${goalMeta}</div>`;

  if (showMove) {
    html += `<div class="kanban-actions">`;
    KANBAN_COLUMNS.forEach(col => {
      if (col === (t.status || 'backlog')) return;
      html += `<button class="kanban-move" data-pb-move-todo="${esc(t.id)}:${esc(col)}" title="Mover a ${esc(COLUMN_LABELS[col])}">${esc(COLUMN_LABELS[col])}</button>`;
    });
    html += `</div>`;
  }

  html += `</div>`;
  return html;
}

function renderReminderCard(r) {
  const dateTime = [r.date, r.time].filter(Boolean).map(esc).join(' · ');
  const done = r.done ? ' · Completado' : '';
  return `<div class="card project-item-card" data-pb-page="${esc(r.slug || r.id)}">`
    + `<h3>${esc(r.title)}</h3>`
    + `<div class="project-item-meta">${dateTime || 'Sin fecha'}${done}</div>`
    + `</div>`;
}

function renderJournalCard(j) {
  const meta = [j.date, j.mood].filter(Boolean).map(esc).join(' · ');
  return `<div class="card project-item-card" data-pb-page="${esc(j.slug || j.id)}">`
    + `<h3>${esc(j.title)}</h3>`
    + (meta ? `<div class="project-item-meta">${meta}</div>` : '')
    + `</div>`;
}

function renderFileCard(f) {
  return `<div class="card project-item-card" data-pb-page="${esc(f.slug || f.id)}">`
    + `<h3>${esc(f.name)}</h3>`
    + `<div class="project-item-meta">${esc(f.file_type || 'otro')}</div>`
    + `</div>`;
}

function renderPageCard(p) {
  return `<div class="card project-item-card" data-pb-page="${esc(p.slug)}">`
    + `<div class="project-item-header">`
    + `<h3>${esc(p.title)}</h3>`
    + `<span class="chip">${esc(p.page_type || 'concept')}</span>`
    + `</div>`
    + (p.summary ? `<div class="project-item-summary">${esc(p.summary)}</div>` : '')
    + `</div>`;
}

function renderGoalsTab(data) {
  if (!data.goalItems.length) return '<p style="color:var(--mute)">No hay goals.</p>';
  return data.goalItems.map(renderGoalCard).join('');
}

function renderMilestonesTab(data) {
  if (!data.milestones.length) return '<p style="color:var(--mute)">No hay milestones.</p>';
  return data.milestones.map(renderGoalCard).join('');
}

function renderTypedPagesTab(items, emptyLabel) {
  if (!items.length) return `<p style="color:var(--mute)">No hay ${emptyLabel}.</p>`;
  return items.map(renderPageCard).join('');
}

function renderTodoKanban(data) {
  if (!data.todos.length) return '<p style="color:var(--mute)">No hay tareas.</p>';

  const byCol = {};
  KANBAN_COLUMNS.forEach(c => byCol[c] = []);
  data.todos.forEach(t => {
    const c = t.status || 'backlog';
    if (byCol[c]) byCol[c].push(t);
  });

  let html = `<div class="kanban-board">`;
  KANBAN_COLUMNS.forEach(col => {
    const items = byCol[col];
    html += `<div class="kanban-column">`
      + `<div class="kanban-column-header">${esc(COLUMN_LABELS[col])} <span class="kanban-count">${items.length}</span></div>`
      + `<div class="kanban-column-body">`;
    items.forEach(t => {
      html += `<div class="kanban-card" data-pb-page="${esc(t.slug || t.id)}">`
        + `<div class="kanban-card-title">${esc(t.title)}</div>`
        + (t.goal_title ? `<div class="kanban-card-meta">${esc(t.goal_title)}</div>` : '')
        + `<div class="kanban-current-status">${esc(COLUMN_LABELS[col])}</div>`
        + `<div class="kanban-actions">`;
      KANBAN_COLUMNS.forEach(target => {
        if (target === col) return;
        html += `<button class="kanban-move" data-pb-move-todo="${esc(t.id)}:${esc(target)}" title="Mover a ${esc(COLUMN_LABELS[target])}">${esc(COLUMN_LABELS[target])}</button>`;
      });
      html += `</div></div>`;
    });
    html += `</div></div>`;
  });
  html += `</div>`;
  return html;
}

function renderRemindersTab(data) {
  if (!data.reminders.length) return '<p style="color:var(--mute)">No hay reminders.</p>';
  return data.reminders.map(renderReminderCard).join('');
}

function renderJournalTab(data) {
  if (!data.journal.length) return '<p style="color:var(--mute)">No hay entradas de journal.</p>';
  return data.journal.map(renderJournalCard).join('');
}

function renderFilesTab(data) {
  if (!data.files.length) return '<p style="color:var(--mute)">No hay archivos.</p>';
  return data.files.map(renderFileCard).join('');
}

function renderPagesTab(data) {
  if (!data.relatedPages.length) return '<p style="color:var(--mute)">No hay páginas relacionadas.</p>';
  return data.relatedPages.map(renderPageCard).join('');
}

function renderGraphTab(data) {
  let html = `<div id="project-graph-view" class="project-graph-view"></div>`;
  html += `<div id="project-graph-legend"></div>`;
  return html;
}

function renderTabContent(data, tab) {
  switch (tab) {
    case 'content': return renderContentTab(data);
    case 'goals': return renderGoalsTab(data);
    case 'milestones': return renderMilestonesTab(data);
    case 'ideas': return renderTypedPagesTab(data.ideas, 'ideas');
    case 'plans': return renderTypedPagesTab(data.plans, 'planes');
    case 'todo': return renderTodoKanban(data);
    case 'notes': return renderTypedPagesTab(data.notes, 'notas');
    case 'reminders': return renderRemindersTab(data);
    case 'journal': return renderJournalTab(data);
    case 'files': return renderFilesTab(data);
    case 'pages': return renderPagesTab(data);
    case 'graph': return renderGraphTab(data);
    default: return '<p style="color:var(--mute)">Tab no implementada.</p>';
  }
}

async function moveTodo(id, status, slug) {
  try {
    // The backend exposes PATCH /api/todos/{id}/status/{status}.
    await API.patch(`/todos/${id}/status/${status}`);
    const idx = Store.state.todos.findIndex(t => String(t.id) === String(id));
    if (idx >= 0) {
      Store.state.todos[idx] = { ...Store.state.todos[idx], status };
    }
    renderProjectPlaceholder(slug, 'todo');
  } catch (err) {
    console.error('moveTodo error', err);
    alert('No se pudo mover la tarea: ' + err.message);
  }
}

function navigateToPage(slug) {
  if (slug && typeof window.showPage === 'function') {
    window.showPage(slug);
  }
}

export function renderProjectPlaceholder(slug, ptab = 'content') {
  const viewId = 'view-projects';
  if (typeof window.setActiveView === 'function') {
    window.setActiveView(viewId);
  }

  if (typeof window.setActiveNav === 'function') {
    window.setActiveNav('projects');
  }

  setHashParams({ project: slug, ptab });

  const container = document.getElementById(viewId);
  if (!container) return;

  const data = collectProjectData(slug);

  if (!data.p) {
    container.innerHTML = `<div class="view-header"><h1>Proyecto no encontrado</h1></div>`;
    return;
  }

  let html = '';

  // Breadcrumb
  html += `<div class="project-breadcrumb">`
    + `<a href="javascript:void(0)" data-pb-back-projects>${icon('arrow-left', 14)}<span>Proyectos</span></a>`
    + `<span class="project-breadcrumb-sep">/</span>`
    + `<span>${esc(data.p.title)}</span>`
    + `</div>`;

  // Header
  html += `<div class="view-header"><div class="view-title-row"><h1>${icon('squares-2x2', 22)}<span>${esc(data.p.title)}</span></h1></div></div>`;

  // Dashboard metrics
  html += renderMetrics(data);

  // Tabs
  html += renderTabs(data, ptab);

  // Tab content
  html += `<div id="project-tab-content">${renderTabContent(data, ptab)}</div>`;

  container.innerHTML = html;
  container.scrollTop = 0;

  // Bind markdown links after rendering content tab.
  if (ptab === 'content') {
    const content = document.getElementById('project-tab-content');
    if (content) bindMarkdownLinks(content);
  }

  // Render graph only when tab is visible and container exists.
  if (ptab === 'graph') {
    if (typeof renderProjectGraph === 'function') {
      renderProjectGraph(data);
    }
  }

  // Remove any previously delegated handler before adding a new one.
  if (container._projectClickHandler) {
    container.removeEventListener('click', container._projectClickHandler);
  }
  container._projectClickHandler = onProjectClick;
  container.addEventListener('click', container._projectClickHandler);

  function onProjectClick(e) {
    const back = e.target.closest('[data-pb-back-projects]');
    const tabLink = e.target.closest('[data-pb-ptab]');
    const card = e.target.closest('[data-pb-page]');
    const moveBtn = e.target.closest('[data-pb-move-todo]');

    if (back) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof window.showTab === 'function') window.showTab('projects');
      return;
    }

    if (tabLink) {
      e.preventDefault();
      e.stopPropagation();
      const tab = tabLink.dataset.pbPtab;
      if (tab) renderProjectPlaceholder(slug, tab);
      return;
    }

    if (moveBtn) {
      e.preventDefault();
      e.stopPropagation();
      const [id, status] = moveBtn.dataset.pbMoveTodo.split(':');
      if (id && status) moveTodo(id, status, slug);
      return;
    }

    if (card) {
      e.preventDefault();
      e.stopPropagation();
      const pageSlug = card.dataset.pbPage;
      if (pageSlug) navigateToPage(pageSlug);
    }
  }
}

export default renderProjectPlaceholder;
