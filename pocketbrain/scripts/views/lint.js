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
  { k: 'contested', label: 'Contested' },
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
    <div class="view-header"><h1>${icon('shield-check', 18)} Lint</h1></div>
    <p style="color:var(--mute);margin-bottom:16px">Resultados de brain.lint().</p>
    <button data-pb-refresh-lint style="margin-bottom:16px;padding:8px 16px;border:1px solid var(--hairline);border-radius:6px;cursor:pointer;background:var(--canvas);color:var(--body)">
      Refrescar
    </button>
    <div id="lint-results"><p style="color:var(--mute)">Cargando...</p></div>
  `;

  refreshLint();

  const btn = container.querySelector('[data-pb-refresh-lint]');
  if (btn) {
    btn.addEventListener('click', refreshLint);
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

    let h = `<div style="margin-bottom:16px"><strong>Total páginas:</strong> ${data.total_pages || 0}</div>`;
    h += '<table style="width:100%;border-collapse:collapse;border:1px solid var(--hairline);margin-bottom:16px"><thead><tr style="background:var(--hairline)">';
    h += '<th style="padding:6px 12px;text-align:left;font-weight:500">Issue</th><th style="padding:6px 12px;text-align:right;font-weight:500">Cantidad</th></tr></thead><tbody>';

    SUMMARY_KEYS.forEach(({ k, label }) => {
      const c = data.summary[k] || 0;
      h += `<tr><td style="padding:4px 12px;border-bottom:1px solid var(--hairline)">${esc(label)}</td>`;
      h += `<td style="padding:4px 12px;text-align:right;border-bottom:1px solid var(--hairline);font-weight:${c > 0 ? '700' : '400'}">${c}</td></tr>`;
    });
    h += '</tbody></table>';

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
