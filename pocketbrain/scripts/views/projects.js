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

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d)) return '';
  return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
}

function excerpt(body, max = 120) {
  const text = (body || '').replace(/\[\[([^\]|]+)\|?([^\]]*)\]\]/g, '$2$1').replace(/[#*_`]/g, '').replace(/\n+/g, ' ').trim();
  return text.length > max ? text.slice(0, max).trim() + '…' : text;
}

export function renderProjectsView() {
  const container = document.getElementById('view-projects');
  if (!container) return;

  const filter = Store.state.filters.page || '';
  const allProjects = Store.state.pages.filter(p => p.page_type === 'project');
  const projectSlugs = new Set(allProjects.map(p => p.slug));
  let projects = allProjects;

  if (filter === 'project') {
    projects = allProjects.filter(p => {
      if (!p.body) return false;
      return Array.from(projectSlugs).some(slug => slug !== p.slug && (
        p.body.indexOf('[[' + slug + ']]') >= 0 || p.body.indexOf('[[' + slug + '|') >= 0
      ));
    });
  } else if (filter === 'noproject') {
    projects = allProjects.filter(p => {
      if (!p.body) return true;
      return !Array.from(projectSlugs).some(slug => slug !== p.slug && (
        p.body.indexOf('[[' + slug + ']]') >= 0 || p.body.indexOf('[[' + slug + '|') >= 0
      ));
    });
  }

  const counts = {};
  projects.forEach(p => {
    counts[p.slug] = { goals: 0, todos: 0, reminders: 0, journal: 0, notes: 0, ideas: 0, plans: 0 };
  });
  const addCount = (slug, key) => { if (counts[slug]) counts[slug][key]++; };

  Store.state.goals.forEach(g => { if (g.page_slug) addCount(g.page_slug, 'goals'); });
  Store.state.todos.forEach(t => { if (t.page_slug) addCount(t.page_slug, 'todos'); });
  Store.state.reminders.forEach(r => { if (r.page_slug) addCount(r.page_slug, 'reminders'); });
  Store.state.journal.forEach(j => { if (j.page_slug) addCount(j.page_slug, 'journal'); });
  Store.state.pages.forEach(p => {
    if (p.page_type === 'note' && p.page_slug) addCount(p.page_slug, 'notes');
    if (p.page_type === 'idea' && p.page_slug) addCount(p.page_slug, 'ideas');
    if (p.page_type === 'plan' && p.page_slug) addCount(p.page_slug, 'plans');
  });

  const map = Store.mapPages();

  let html = `
    <div class="view-header">
      <div class="view-title-row">
        <h1>${icon('squares-2x2', 20)}<span>Proyectos</span></h1>
        <select data-pb-filter="page" class="filter-select">
          <option value="" ${filter === '' ? 'selected' : ''}>Todos</option>
          <option value="project" ${filter === 'project' ? 'selected' : ''}>Con proyecto</option>
          <option value="noproject" ${filter === 'noproject' ? 'selected' : ''}>Sin proyecto</option>
        </select>
      </div>
      <p class="view-subtitle">${projects.length} proyectos</p>
    </div>
    <div class="cards-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;">`;

  if (!projects.length) {
    html += '</div><p style="color:var(--mute)">No hay proyectos en este contexto.</p>';
  } else {
    projects.forEach(p => {
      const c = counts[p.slug] || {};
      const chips = [];
      if (c.goals) chips.push(`Goals ${c.goals}`);
      if (c.todos) chips.push(`Todo ${c.todos}`);
      if (c.reminders) chips.push(`Reminders ${c.reminders}`);
      if (c.journal) chips.push(`Journal ${c.journal}`);
      if (c.notes) chips.push(`Notas ${c.notes}`);
      if (c.ideas) chips.push(`Ideas ${c.ideas}`);
      if (c.plans) chips.push(`Planes ${c.plans}`);

      const domain = p.expand?.domain?.name || p.domain || '';
      const tags = (p.expand?.tags || p.tags || []).slice(0, 3);
      const updated = formatDate(p.updated || p.created);

      html += `
        <div class="card project-card" data-pb-project="${esc(p.slug)}">
          <div class="project-card-header">
            <h3>${esc(p.title)}</h3>
            ${domain ? `<span class="chip-domain">${esc(domain)}</span>` : ''}
          </div>
          ${p.summary || p.body ? `<p class="project-excerpt">${esc(excerpt(p.summary || p.body))}</p>` : ''}
          <div class="project-meta">
            ${tags.map(t => typeof t === 'string' ? `<span class="chip-tag">${esc(t)}</span>` : `<span class="chip-tag">${esc(t.name || '')}</span>`).join('')}
          </div>
          <div class="project-chips">
            ${chips.map(label => `<span class="project-chip">${esc(label)}</span>`).join('')}
          </div>
          ${updated ? `<div class="project-footer">Actualizado ${esc(updated)}</div>` : ''}
        </div>`;
    });
    html += '</div>';
  }

  container.innerHTML = html;

  const select = container.querySelector('select[data-pb-filter="page"]');
  if (select) {
    select.addEventListener('change', e => {
      Store.setFilter('page', e.target.value);
      renderProjectsView();
    });
  }

  container.querySelectorAll('[data-pb-project]').forEach(el => {
    el.addEventListener('click', () => {
      const slug = el.dataset.pbProject;
      if (slug && typeof window.showProject === 'function') {
        window.showProject(slug);
      }
    });
  });
}

export default renderProjectsView;
