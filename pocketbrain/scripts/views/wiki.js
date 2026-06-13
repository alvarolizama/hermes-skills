import Store from '../store.js';
import { Tabs, bindTabs } from '../components/Tabs.js';
import { icon } from '../components/Icon.js';
import { getHashParams, setHashParams } from '../router.js';
import { bindMarkdownLinks } from '../markdown.js';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

let wikiIndexTab = 'all';
let pageTab = 'content';

const INDEX_TABS = [
  { id: 'all', label: 'Todos', icon: 'squares-2x2' },
  { id: 'project', label: 'Proyectos', icon: 'squares-2x2' },
  { id: 'concept', label: 'Conceptos', icon: 'light-bulb' },
  { id: 'entity', label: 'Entidades', icon: 'users' },
  { id: 'comparison', label: 'Comparaciones', icon: 'chart-pie' },
  { id: 'query', label: 'Consultas', icon: 'magnifying-glass' },
  { id: 'raw', label: 'Raw', icon: 'paper-clip' }
];

const TYPE_NAMES = {
  project: 'Proyectos',
  concept: 'Conceptos',
  entity: 'Entidades',
  comparison: 'Comparaciones',
  query: 'Consultas',
  raw: 'Raw'
};

export function renderWikiView(slug) {
  const params = getHashParams();
  if (slug) {
    pageTab = params.wtab || 'content';
    renderWikiPage(slug);
  } else {
    wikiIndexTab = params.wtab || 'all';
    renderWikiIndex();
  }
}

function pageMetadataRows(p) {
  const rows = [];
  if (p.page_type) rows.push(['Tipo', p.page_type]);
  if (p.confidence) rows.push(['Confianza', p.confidence]);
  if (p.status) rows.push(['Estado', p.status]);
  if (p.tags && p.tags.length) rows.push(['Tags', p.tags.join(', ')]);
  if (p.source_url) rows.push(['Source URL', `<a href="${esc(p.source_url)}" target="_blank" rel="noopener">${esc(p.source_url.substring(0, 40))}</a>`]);
  if (p.source_sha256) rows.push(['SHA256', `<span style="font-family:monospace;font-size:11px">${esc(p.source_sha256.substring(0, 16))}...</span>`]);
  if (p.contested) rows.push(['Contested', `<span style="color:#E53935;display:flex;align-items:center;gap:4px">${icon('exclamation-triangle', 12)}<span>Sí</span></span>`]);
  if (p.contradictions) rows.push(['Contradicciones', p.contradictions]);
  if (p.created) rows.push(['Creado', p.created]);
  if (p.updated) rows.push(['Actualizado', p.updated]);
  if (p.started_date) rows.push(['Iniciado', p.started_date]);
  if (p.completed_date) rows.push(['Completado', p.completed_date]);
  if (p.cancelled_date) rows.push(['Cancelado', p.cancelled_date]);
  if (p.comment) rows.push(['Nota', p.comment]);
  return rows;
}

function renderWikiPage(slug) {
  const container = document.getElementById('view-wiki');
  if (!container) return;

  const pages = Store.mapPages();
  const p = pages[slug];
  if (!p) {
    container.innerHTML = '<p style="color:var(--mute)">Página no encontrada.</p>';
    return;
  }

  setActiveView('view-wiki');
  setHashParams({ tab: 'wiki', page: slug, wtab: pageTab });

  const goals = Store.state.goals.filter(g => g.page === slug);
  const todos = Store.state.todos.filter(t => t.page_slug === slug);
  const reminders = Store.state.reminders.filter(r => r.page_slug === slug);
  const journal = Store.state.journal.filter(j => j.page_slug === slug);
  const backlinks = p.backlinks || [];
  const relCount = goals.length + todos.length + reminders.length + journal.length;

  const tabs = [{ id: 'content', label: 'Contenido', icon: 'document-text', count: p.body ? 1 : 0 }];
  if (backlinks.length) tabs.push({ id: 'backlinks', label: 'Backlinks', icon: 'arrow-left', count: backlinks.length });
  if (relCount) tabs.push({ id: 'related', label: 'Relacionado', icon: 'share', count: relCount });

  let html = `<div style="font-size:12px;color:var(--mute);margin-bottom:8px">`
    + `<a href="javascript:void(0)" data-pb-index style="color:var(--ink)">${icon('arrow-left', 12)}<span>Wiki</span></a> · `
    + `<a href="javascript:void(0)" data-pb-type="${esc(p.page_type)}" style="color:var(--ink)">${esc(TYPE_NAMES[p.page_type] || p.page_type)}</a> · ${esc(p.title)}`
    + `</div>`;
  html += `<div class="view-title-row" style="margin-bottom:20px"><h1>${icon('document-text', 24)}<span>${esc(p.title)}</span></h1></div>`;

  html += Tabs({ items: tabs, active: pageTab });

  html += `<div class="wiki-layout-page"><div class="wiki-left">`;
  html += `<div id="page-tab-content" class="card md-content" style="margin-top:12px"></div>`;

  const logs = (Store.state.logs || []).filter(l => l.page === p.id).slice(0, 10);
  html += `<div class="wiki-log" style="margin-top:24px"><h2>Actividad reciente</h2>`;
  if (logs.length) {
    logs.forEach(l => {
      html += `<div style="font-size:13px;color:var(--body);margin-bottom:6px"><strong>${esc(l.created)}</strong> · ${esc(l.operation)}${l.details ? ': ' + esc(l.details) : ''}</div>`;
    });
  } else {
    html += '<p style="color:var(--mute);font-size:13px">Sin actividad reciente.</p>';
  }
  html += '</div></div>';

  html += `<div class="wiki-right">`;
  html += renderRelationsCard(goals, todos, reminders, journal, backlinks);
  html += renderMetadataCard(p);
  html += '</div></div>';

  container.innerHTML = html;
  renderPageTabContent(p, goals, todos, reminders, journal, backlinks);

  const tabsRoot = container.querySelector('.project-tabs');
  if (tabsRoot) {
    bindTabs(tabsRoot, id => {
      pageTab = id;
      setHashParams({ tab: 'wiki', page: slug, wtab: id });
      renderPageTabContent(p, goals, todos, reminders, journal, backlinks);
    });
  }

  const indexLink = container.querySelector('[data-pb-index]');
  if (indexLink) {
    indexLink.addEventListener('click', e => {
      e.preventDefault();
      if (typeof window.showTab === 'function') window.showTab('wiki');
    });
  }

  const typeLink = container.querySelector('[data-pb-type]');
  if (typeLink) {
    typeLink.addEventListener('click', e => {
      e.preventDefault();
      const type = typeLink.dataset.pbType;
      if (typeof window.showTab === 'function') {
        window.showTab('type_' + type);
      } else if (typeof window.showIndex === 'function') {
        window.showIndex();
      }
    });
  }
}

function renderPageTabContent(p, goals, todos, reminders, journal, backlinks) {
  const content = document.getElementById('page-tab-content');
  if (!content) return;

  let html = '';
  if (pageTab === 'content') {
    html += window.mdToHtml ? window.mdToHtml(p.body || '') : esc(p.body || '');
    bindMarkdownLinks(content);
  } else if (pageTab === 'backlinks') {
    if (!backlinks.length) {
      html += '<p style="color:var(--mute)">Sin backlinks.</p>';
    } else {
      backlinks.forEach(b => {
        html += `<div class="card" style="cursor:pointer;padding:12px;margin-bottom:8px" data-pb-page="${esc(b.slug)}" role="link" tabindex="0"><h3>${esc(b.title)}</h3></div>`;
      });
    }
  } else if (pageTab === 'related') {
    if (goals.length) {
      html += `<h2>Goals (${goals.length})</h2>`;
      goals.forEach(g => {
        html += `<div class="card" style="padding:12px;margin-bottom:8px"><h3>${esc(g.title)}</h3><div style="font-size:12px;color:var(--mute)">${esc(g.status)}</div></div>`;
      });
    }
    if (todos.length) {
      html += `<h2>Tareas (${todos.length})</h2>`;
      todos.forEach(t => {
        html += `<div class="card" style="padding:12px;margin-bottom:8px"><h3>${esc(t.title)}</h3><div style="font-size:12px;color:var(--mute)">${esc(t.status)}</div></div>`;
      });
    }
    if (reminders.length) {
      html += `<h2>Recordatorios (${reminders.length})</h2>`;
      reminders.forEach(r => {
        html += `<div class="card" style="padding:12px;margin-bottom:8px"><h3>${esc(r.title)}</h3><div style="font-size:12px;color:var(--mute)">${esc(r.date)}</div></div>`;
      });
    }
    if (journal.length) {
      html += `<h2>Journal (${journal.length})</h2>`;
      journal.slice(0, 5).forEach(j => {
        html += `<div class="card" style="padding:12px;margin-bottom:8px"><h3>${esc(j.title)}</h3><div style="font-size:12px;color:var(--mute)">${esc(j.date)}</div></div>`;
      });
    }
  }

  content.innerHTML = html || '<p style="color:var(--mute)">Sin contenido.</p>';

  content.querySelectorAll('[data-pb-page]').forEach(el => {
    el.addEventListener('click', () => {
      const slug = el.dataset.pbPage;
      if (slug && typeof window.showPage === 'function') window.showPage(slug);
    });
  });
}

function renderRelationsCard(goals, todos, reminders, journal, backlinks) {
  const items = [];
  if (goals.length) items.push({ icon: 'G', color: '#4CAF50', bg: '#E8F5E9', label: `${goals.length} goals` });
  if (todos.length) items.push({ icon: 'T', color: '#9C27B0', bg: '#F3E8F5', label: `${todos.length} tareas` });
  if (reminders.length) items.push({ icon: 'R', color: '#FFC107', bg: '#FFF8E1', label: `${reminders.length} reminders` });
  if (journal.length) items.push({ icon: 'J', color: '#2196F3', bg: '#E3F0FF', label: `${journal.length} journal` });
  if (backlinks.length) items.push({ icon: 'B', color: '#737373', bg: '#F5F5F0', label: `${backlinks.length} backlinks` });

  let html = '<div class="wiki-relations-card"><div class="wiki-relations-title">Relaciones</div><div class="wiki-relation-row">';
  items.forEach(it => {
    html += `<div class="wiki-relation-item">`
      + `<span class="wiki-rel-icon" style="background:${it.bg};color:${it.color}">${it.icon}</span>`
      + `<span class="wiki-rel-label">${it.label}</span></div>`;
  });
  html += '</div></div>';
  return html;
}

function renderMetadataCard(p) {
  const rows = pageMetadataRows(p);
  if (!rows.length) return '';
  let html = '<div class="wiki-relations-card"><div class="wiki-relations-title">Metadata</div><div class="wiki-relation-row">';
  rows.forEach(([k, v]) => {
    html += `<div class="wiki-relation-item"><span class="wiki-rel-label">${esc(k)}</span><span class="wiki-rel-value">${v}</span></div>`;
  });
  html += '</div></div>';
  return html;
}

export function renderWikiIndex() {
  const container = document.getElementById('view-wiki');
  if (!container) return;

  setActiveView('view-wiki');
  setHashParams({ tab: 'wiki' });
  const pages = Store.state.pages;
  const byType = {};
  pages.forEach(p => {
    const pt = p.page_type || 'concept';
    byType[pt] = byType[pt] || [];
    byType[pt].push(p);
  });

  const counts = {
    all: pages.length,
    project: (byType.project || []).length,
    concept: (byType.concept || []).length,
    entity: (byType.entity || []).length,
    comparison: (byType.comparison || []).length,
    query: (byType.query || []).length,
    raw: (byType.raw || []).length
  };

  const tabCounts = {};
  INDEX_TABS.forEach(t => {
    tabCounts[t.id] = t.id === 'all' ? counts.all : counts[t.id] || 0;
  });

  let html = `<div class="view-header">`
    + `<div class="project-breadcrumb" style="margin-bottom:8px">`
    + `<a href="javascript:void(0)" data-pb-back-projects>${icon('arrow-left', 12)}<span>Proyectos</span></a>`
    + `<span class="project-breadcrumb-sep">/</span><span>Wiki</span>`
    + `</div>`
    + `<div class="view-title-row"><h1>${icon('bars-3', 20)}<span>Wiki</span></h1></div>`
    + `<p class="view-subtitle">${pages.length} páginas</p></div>`;
  html += Tabs({ items: INDEX_TABS, active: wikiIndexTab, counts: tabCounts });

  const types = wikiIndexTab === 'all' ? ['project', 'concept', 'entity', 'comparison', 'query', 'raw'] : [wikiIndexTab];
  const total = types.reduce((sum, t) => sum + (byType[t] || []).length, 0);
  html += `<div class="cards-grid">`;

  types.forEach(pt => {
    const items = byType[pt] || [];
    if (!items.length) return;
    items.sort((a, b) => a.title.localeCompare(b.title));
    const typeIcon = INDEX_TABS.find(t => t.id === pt)?.icon || 'document-text';
    items.forEach(p => {
      html += `<div class="card" style="cursor:pointer;padding:12px;margin-bottom:8px" data-pb-page="${esc(p.slug)}">`
        + `<div style="display:flex;align-items:center;gap:8px">${icon(typeIcon, 16)}<h3>${esc(p.title)}</h3></div>`
        + (p.page_type ? `<div style="font-size:12px;color:var(--mute);margin-top:4px">${esc(p.page_type)}</div>` : '')
        + `</div>`;
    });
  });

  html += '</div>';

  container.innerHTML = html;

  const tabsRoot = container.querySelector('.project-tabs');
  if (tabsRoot) {
    bindTabs(tabsRoot, id => {
      wikiIndexTab = id;
      setHashParams({ tab: 'wiki', wtab: id });
      renderWikiIndex();
    });
  }

  const back = container.querySelector('[data-pb-back-projects]');
  if (back) {
    back.addEventListener('click', e => {
      e.preventDefault();
      if (typeof window.showTab === 'function') window.showTab('projects');
    });
  }

  container.querySelectorAll('[data-pb-page]').forEach(el => {
    el.addEventListener('click', () => {
      const slug = el.dataset.pbPage;
      if (slug && typeof window.showPage === 'function') window.showPage(slug);
    });
  });
}

export default renderWikiView;
