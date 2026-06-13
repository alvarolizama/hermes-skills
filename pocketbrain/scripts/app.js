/**
 * PocketBrain SPA entry point.
 *
 * Wires the API, store, router, and view stubs together, then boots the app.
 */

import API from './api.js';
import Store from './store.js';
import { Router, getHashParams, setHashParams } from './router.js';
import { icon } from './components/Icon.js';
import { mdToHtml as markdownToHtml, bindMarkdownLinks } from './markdown.js';
import { renderProjectsView } from './views/projects.js';
import { renderTodosView } from './views/todos.js';
import { renderRemindersView } from './views/reminders.js';
import { renderJournalView } from './views/journal.js';
import { renderFilesView as renderFiles } from './views/files.js';
import { renderTypeView } from './views/type.js';
import { renderGoalsView } from './views/goals.js';
import { renderMilestonesView } from './views/milestones.js';
import { renderWikiView } from './views/wiki.js';
import { renderGraph, renderProjectGraph } from './views/graph.js';
import { renderLintView } from './views/lint.js';
import { renderProjectPlaceholder } from './views/project-detail.js';

const TAB_VIEW_IDS = {
  projects: 'view-projects',
  todos: 'view-todos',
  goals: 'view-goals',
  milestones: 'view-milestones',
  journal: 'view-journal',
  reminders: 'view-reminders',
  files: 'view-files',
  wiki: 'view-wiki',
  graph: 'view-graph',
  lint: 'view-lint'
};

function closeSidebar() {
  const sb = document.getElementById('sidebar');
  if (sb) sb.classList.remove('open');
}

function updateStatus(state) {
  const el = document.getElementById('status');
  if (!el) return;
  el.className = state;
  const label = state === 'live' ? 'live' : state === 'offline' ? 'offline' : 'cargando...';
  el.innerHTML = `<span class="dot"></span>${label}`;
}

function setActiveView(viewId) {
  document.querySelectorAll('#main > div').forEach(d => d.classList.remove('active'));
  const el = document.getElementById(viewId);
  if (el) el.classList.add('active');
}

function setActiveNav(tab) {
  document.querySelectorAll('#nav a.nav-link').forEach(a => a.classList.remove('active'));
  try {
    const sel = `a.nav-link[onclick*="showTab('${tab}')"]`;
    const link = document.querySelector(sel);
    if (link) link.classList.add('active');
  } catch (e) {
    // ignore malformed selectors
  }
}

function renderTab(tab) {
  if (getHashParams().project) {
    Router.resolve();
    return;
  }
  let viewId = TAB_VIEW_IDS[tab];
  if (!viewId && tab && tab.startsWith('type_')) {
    viewId = `view-type-${tab.replace('type_', '')}`;
  }
  setActiveView(viewId || 'view-projects');
  setActiveNav(tab);

  switch (tab) {
    case 'projects': renderProjectsView(); break;
    case 'todos': renderTodosView(); break;
    case 'goals': renderGoalsView('goal'); break;
    case 'milestones': renderMilestonesView(); break;
    case 'journal': renderJournalView(); break;
    case 'reminders': renderRemindersView(); break;
    case 'files': renderFiles(); break;
    case 'wiki': renderWikiView(); break;
    case 'graph': renderGraph(); break;
    case 'lint': renderLintView(); break;
    default:
      if (tab && tab.startsWith('type_')) {
        setHashParams({ tab });
        renderTypeView(tab.replace('type_', ''));
      } else {
        renderProjectsView();
      }
  }
}

function buildSidebar() {
  const state = Store.get();
  const nav = document.getElementById('nav');
  if (!nav) return;

  const pages = state.pages || [];
  const countType = t => pages.filter(p => p.page_type === t).length;
  const tc = (state.todos || []).length;
  const rc = (state.reminders || []).length;
  const jc = (state.journal || []).length;
  const nc = (state.graph?.nodes || []).length;

  const item = (id, label, count, search, iconName) => {
    const countAttr = count !== '' ? `<span class="nav-count">${count}</span>` : '';
    const svg = iconName ? icon(iconName, 16) : '';
    return `<a href="javascript:void(0)" class="nav-link" onclick="showTab('${id}');return false;" data-search="${search || label.toLowerCase()}">`
      + `<span class="nav-label" style="display:flex;align-items:center;gap:8px">${svg}<span>${label}</span></span>`
      + `${countAttr}</a>`;
  };

  let h = '';
  h += item('projects', 'Proyectos', countType('project'), 'projects', 'squares-2x2');
  h += item('goals', 'Goals', countType('goal'), 'goals', 'flag');
  h += item('milestones', 'Milestones', countType('milestone'), 'milestones', 'check-circle');
  h += item('type_idea', 'Ideas', countType('idea'), 'idea', 'light-bulb');
  h += item('type_plan', 'Planes', countType('plan'), 'plan', 'calendar-days');
  h += item('todos', 'Todo', tc, 'todo', 'clipboard-document-list');
  h += item('reminders', 'Reminders', rc, 'reminders', 'bell');
  h += item('type_note', 'Notas', countType('note'), 'note', 'clock');
  h += item('journal', 'Journal', jc, 'journal', 'book-open');
  h += item('type_file', 'Archivos', countType('file'), 'file', 'document-text');
  h += item('type_concept', 'Conceptos', countType('concept'), 'concept', 'document-text');
  h += item('type_entity', 'Entidades', countType('entity'), 'entity', 'users');
  h += item('type_comparison', 'Comparaciones', countType('comparison'), 'comparison', 'chart-pie');
  h += item('type_query', 'Consultas', countType('query'), 'query', 'magnifying-glass');
  h += item('type_raw', 'Raw', countType('raw'), 'raw', 'paper-clip');
  h += item('wiki', 'Wiki', pages.length, 'wiki all', 'bars-3');
  h += `<a href="javascript:void(0)" class="nav-link" onclick="showTab('graph');return false;" data-search="graph"><span class="nav-label" style="display:flex;align-items:center;gap:8px">${icon('circle', 16)}<span>Graph</span></span><span class="nav-count">${nc}</span></a>`;
  h += item('lint', 'Lint', '', 'lint', 'shield-check');
  nav.innerHTML = h;
}

function filterSidebar() {
  const input = document.getElementById('search');
  const q = input ? input.value.toLowerCase() : '';
  document.querySelectorAll('#nav a[data-search]').forEach(a => {
    const search = (a.getAttribute('data-search') || '').toLowerCase();
    a.style.display = q && !search.includes(q) ? 'none' : 'block';
  });
}

async function loadAll() {
  updateStatus('syncing');
  try {
    const [pages, goals, todos, deps, files, reminders, journal, graph, logs] = await API.loadAll();
    Store.set({
      pages: pages || [],
      goals: goals || [],
      todos: todos || [],
      deps: deps || [],
      files: files || [],
      reminders: reminders || [],
      journal: journal || [],
      graph: graph || { nodes: [], edges: [] },
      logs: logs || [],
      offline: false,
      error: null
    });
    buildSidebar();
    Router.resolve();
    updateStatus('live');
  } catch (err) {
    console.error('loadAll error', err);
    Store.setOffline(true);
    updateStatus('offline');
  }
}

async function switchBrain(name) {
  const sel = document.getElementById('brain-selector');
  if (sel) sel.value = name;
  API.setContext(name);
  Store.set('context', name);
  await loadAll();
}

function showTab(tab) {
  setHashParams({ tab });
  Router.resolve();
  closeSidebar();
}

function showProject(slug, ptab = 'content') {
  setHashParams({ project: slug, ptab });
  Router.resolve();
  closeSidebar();
}

function showPage(slug) {
  setHashParams({ tab: 'wiki', page: slug });
  Router.resolve();
  closeSidebar();
}

// Project detail view is implemented in ./views/project-detail.js.

function renderProjectDetail(slug, ptab) {
renderProjectPlaceholder(slug, ptab || 'content');
}

function renderPagePlaceholder(slug) {
  renderWikiView(slug);
}

// Register router handlers.
Router.register('tab', renderTab);
Router.register('project', renderProjectDetail);
Router.register('page', renderPagePlaceholder);
Router.register('default', () => renderTab('projects'));

// Expose global helpers expected by inline HTML handlers.
window.showTab = showTab;
window.showProject = showProject;
window.showPage = showPage;
window.showIndex = () => showTab('wiki');
window.mdToHtml = text => markdownToHtml(text, Store.mapPages());
window.switchBrain = switchBrain;
window.filterSidebar = filterSidebar;
window.setActiveView = setActiveView;
window.setActiveNav = setActiveNav;

async function init() {
  const sel = document.getElementById('brain-selector');
  try {
    const brains = await API.get('/contexts');
    if (sel) {
      sel.innerHTML = brains.map(b => `<option value="${b.name}">${b.name}</option>`).join('');
    }
    const initial = brains[0]?.name || 'personal';
    if (sel) sel.value = initial;
    API.setContext(initial);
    Store.set('context', initial);
    await loadAll();
  } catch (err) {
    console.error('init error', err);
    updateStatus('offline');
  }
}

window.addEventListener('DOMContentLoaded', init);
window.addEventListener('popstate', () => Router.resolve());
window.addEventListener('hashchange', () => Router.resolve());
