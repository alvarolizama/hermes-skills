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

export function renderFilesView() {
  const container = document.getElementById('view-files');
  if (!container) return;

  const filter = Store.state.filters.file || '';
  let files = Store.state.files;

  if (filter === 'project') {
    files = files.filter(f => !!f.page_slug);
  } else if (filter === 'noproject') {
    files = files.filter(f => !f.page_slug);
  }

  let html = `<div class="view-header">`
    + `<div class="project-breadcrumb" style="margin-bottom:8px">`
    + `<a href="javascript:void(0)" data-pb-back-projects>${icon('arrow-left', 12)}<span>Proyectos</span></a>`
    + `<span class="project-breadcrumb-sep">/</span><span>Archivos</span>`
    + `</div>`
    + `<div class="view-title-row"><h1>${icon('paper-clip', 20)}<span>Archivos</span></h1>`
    + `<select data-pb-filter="file" class="filter-select">`
    + `<option value="" ${filter === '' ? 'selected' : ''}>Todos</option>`
    + `<option value="project" ${filter === 'project' ? 'selected' : ''}>Con proyecto</option>`
    + `<option value="noproject" ${filter === 'noproject' ? 'selected' : ''}>Sin proyecto</option>`
    + `</select></div>`
    + `<p class="view-subtitle">${files.length} archivos</p></div>`;

  html += `<div class="cards-grid">`;

  if (!files.length) {
    html += '<p style="color:var(--mute)">No hay archivos.</p>';
  } else {
    files.forEach(f => {
      html += `<div class="card" style="cursor:pointer;padding:12px;margin-bottom:8px" data-pb-page="${esc(f.slug || f.id)}">`
        + `<div style="display:flex;align-items:center;gap:8px">${icon('document-text', 18)}<h3>${esc(f.name)}</h3></div>`
        + `<div style="font-size:12px;color:var(--mute);margin-top:4px">${esc(f.file_type || 'otro')}${f.page_slug ? ' · ' + esc(f.page_slug) : ''}</div>`
        + `</div>`;
    });
  }

  html += '</div>';

  container.innerHTML = html;

  const select = container.querySelector('select[data-pb-filter="file"]');
  if (select) {
    select.addEventListener('change', e => {
      Store.setFilter('file', e.target.value);
      renderFilesView();
    });
  }

  const back = container.querySelector('[data-pb-back-projects]');
  if (back) {
    back.addEventListener('click', e => {
      e.preventDefault();
      if (typeof window.showTab === 'function') window.showTab('projects');
    });
  }
}

export { renderFilesView as renderFiles };
export default renderFilesView;
