import Store from '../store.js';

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

  let html = `<div class="view-header"><h1>Archivos</h1>`
    + `<select data-pb-filter="file" style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)">`
    + `<option value="" ${filter === '' ? 'selected' : ''}>Todos</option>`
    + `<option value="project" ${filter === 'project' ? 'selected' : ''}>Con proyecto</option>`
    + `<option value="noproject" ${filter === 'noproject' ? 'selected' : ''}>Sin proyecto</option>`
    + `</select></div>`;

  html += `<p style="color:var(--mute);margin-bottom:20px">${files.length} archivos</p>`;

  if (!files.length) {
    html += '<p style="color:var(--mute)">No hay archivos.</p>';
  } else {
    files.forEach(f => {
      html += `<div class="card" style="padding:12px;margin-bottom:8px"><h3>${esc(f.name)}</h3><div style="font-size:12px;color:var(--mute)">${esc(f.file_type || 'otro')}</div></div>`;
    });
  }

  container.innerHTML = html;

  const select = container.querySelector('select[data-pb-filter="file"]');
  if (select) {
    select.addEventListener('change', e => {
      Store.setFilter('file', e.target.value);
      renderFilesView();
    });
  }
}

export { renderFilesView as renderFiles };
export default renderFilesView;
