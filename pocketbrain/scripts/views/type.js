import Store from '../store.js';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const TYPE_NAMES = {
  concept: 'Conceptos', entity: 'Entidades', comparison: 'Comparaciones',
  query: 'Consultas', raw: 'Raw', plan: 'Planes', note: 'Notas', idea: 'Ideas',
  file: 'Archivos', deliverable: 'Entregables'
};

export function renderTypeView(typeName) {
  const containerId = `view-type-${typeName}`;
  const container = document.getElementById(containerId);
  if (!container) return;

  const filter = Store.state.filters[typeName] || '';
  const all = Store.state.pages.filter(p => p.page_type === typeName);
  let items = all;

  if (filter === 'project') {
    items = all.filter(p => {
      if (!p.body) return false;
      const projectSlugs = Store.state.pages.filter(pg => pg.page_type === 'project').map(pg => pg.slug);
      return projectSlugs.some(slug => p.body.toLowerCase().includes(`[[${slug.toLowerCase()}]]`) || p.body.toLowerCase().includes(`[[${slug.toLowerCase()}|`));
    });
  } else if (filter === 'noproject') {
    items = all.filter(p => {
      if (!p.body) return true;
      const projectSlugs = Store.state.pages.filter(pg => pg.page_type === 'project').map(pg => pg.slug);
      return !projectSlugs.some(slug => p.body.toLowerCase().includes(`[[${slug.toLowerCase()}]]`) || p.body.toLowerCase().includes(`[[${slug.toLowerCase()}|`));
    });
  }

  items.sort((a, b) => a.title.localeCompare(b.title));

  let html = `<div class="view-header"><h1>${esc(TYPE_NAMES[typeName] || typeName)}</h1>`
    + `<select data-pb-filter="${esc(typeName)}" style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)">`
    + `<option value="" ${filter === '' ? 'selected' : ''}>Todos</option>`
    + `<option value="project" ${filter === 'project' ? 'selected' : ''}>Con proyecto</option>`
    + `<option value="noproject" ${filter === 'noproject' ? 'selected' : ''}>Sin proyecto</option>`
    + `</select></div>`;

  html += `<p style="color:var(--mute);margin-bottom:20px">${items.length} ${esc((TYPE_NAMES[typeName] || typeName).toLowerCase())}</p>`;

  if (!items.length) {
    html += '<p style="color:var(--mute)">No hay items.</p>';
  } else {
    items.forEach(p => {
      html += `<div class="card" style="cursor:pointer;padding:12px;margin-bottom:8px" data-pb-page="${esc(p.slug)}"><h3>${esc(p.title)}</h3></div>`;
    });
  }

  container.innerHTML = html;

  const select = container.querySelector(`select[data-pb-filter="${esc(typeName)}"]`);
  if (select) {
    select.addEventListener('change', e => {
      Store.setFilter(typeName, e.target.value);
      renderTypeView(typeName);
    });
  }

  container.querySelectorAll('[data-pb-page]').forEach(el => {
    el.addEventListener('click', () => {
      const slug = el.dataset.pbPage;
      if (slug && typeof window.showPage === 'function') window.showPage(slug);
    });
  });
}

export default renderTypeView;
