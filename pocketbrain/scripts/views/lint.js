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

const SUMMARY_KEYS = [
  { k: 'orphans', label: 'Huérfanos' },
  { k: 'broken_links', label: 'Links rotos' },
  { k: 'low_confidence', label: 'Confianza baja' },
  { k: 'kb_contested', label: 'Contested' },
  { k: 'invalid_tags', label: 'Tags inválidos' },
  { k: 'oversized', label: 'Páginas grandes' },
  { k: 'drift', label: 'Source drift' },
  { k: 'frontmatter_issues', label: 'Frontmatter inválido' }
];

export function renderLintView() {
  const container = document.getElementById('view-lint');
  if (!container) return;
  setActiveView('view-lint');

  container.innerHTML = `
    <div class="view-header">
      <div class="project-breadcrumb" style="margin-bottom:8px">
        <a href="javascript:void(0)" data-pb-back-projects>${icon('arrow-left', 12)}<span>Proyectos</span></a>
        <span class="project-breadcrumb-sep">/</span><span>Lint</span>
      </div>
      <div class="view-title-row">
        <h1>${icon('shield-check', 20)}<span>Lint</span></h1>
        <button data-pb-refresh-lint class="filter-select" style="display:flex;align-items:center;gap:6px;cursor:pointer;">${icon('arrow-path', 14)} Refrescar</button>
      </div>
      <p class="view-subtitle">Resultados de brain.lint()</p>
    </div>
    <div id="lint-results"><p style="color:var(--mute)">Cargando...</p></div>
  `;

  refreshLint();

  const btn = container.querySelector('[data-pb-refresh-lint]');
  if (btn) {
    btn.addEventListener('click', refreshLint);
  }

  const back = container.querySelector('[data-pb-back-projects]');
  if (back) {
    back.addEventListener('click', e => {
      e.preventDefault();
      if (typeof window.showTab === 'function') window.showTab('projects');
    });
  }
}

async function refreshLint() {
  const results = document.getElementById('lint-results');
  if (!results) return;
  results.innerHTML = '<p style="color:var(--mute)">Cargando...</p>';

  try {
    const res = await fetch('/api/lint?context=' + encodeURIComponent(Store.state.context || 'personal'));
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();

    if (!data || !data.summary) {
      results.innerHTML = '<p style="color:var(--mute)">Sin datos.</p>';
      return;
    }

    let h = '<div class="metrics-row" style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px">';
    h += `<div class="metric-card"><div class="metric-value">${data.total_pages || 0}</div><div class="metric-label">Páginas</div></div>`;
    SUMMARY_KEYS.forEach(({ k, label }) => {
      const c = data.summary[k] || 0;
      h += `<div class="metric-card" style="${c > 0 ? 'border-color:#E53935' : ''}"><div class="metric-value" style="${c > 0 ? 'color:#E53935' : ''}">${c}</div><div class="metric-label">${esc(label)}</div></div>`;
    });
    h += '</div>';

    h += '<div class="cards-grid">';

    const renderList = (items, title) => {
      if (!items || !items.length) return '';
      let out = `<h3 style="margin-top:16px;font-size:14px;font-weight:600">${esc(title)} (${items.length})</h3>`;
      items.forEach(s => {
        let val, page, link;
        if (typeof s === 'string') {
          val = s;
          page = s;
        } else if (s.link) {
          val = `${s.link} ← ${s.page}`;
          page = s.page;
          link = s.link;
        } else {
          val = s.page || s.slug || JSON.stringify(s);
          page = s.page || s.slug;
        }
        out += `<div class="card" style="cursor:pointer;padding:8px 12px;margin-bottom:6px" data-pb-page="${esc(page)}" data-pb-link="${esc(link || '')}">${esc(val)}</div>`;
      });
      return out;
    };

    h += renderList(data.orphans, 'Huérfanas');
    h += renderList(data.broken_links, 'Links rotos');
    h += renderList(data.low_confidence, 'Confianza baja');
    h += renderList(data.contested_pages, 'Contested');
    h += renderList(data.invalid_tags, 'Tags inválidos');
    h += renderList(data.oversized_pages, 'Páginas grandes');
    h += renderList(data.drift, 'Source drift');
    h += '</div>';

    results.innerHTML = h || '<p style="color:var(--mute)">No hay issues.</p>';

    results.querySelectorAll('[data-pb-page]').forEach(el => {
      el.addEventListener('click', () => {
        const slug = el.dataset.pbPage;
        const link = el.dataset.pbLink;
        if (link && typeof window.showPage === 'function') window.showPage(link);
        else if (slug && typeof window.showPage === 'function') window.showPage(slug);
      });
    });
  } catch (e) {
    results.innerHTML = `<p style="color:#E53935">Error: ${esc(e.message)}</p>`;
  }
}

export default renderLintView;
