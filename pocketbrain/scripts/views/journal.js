import Store from '../store.js';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const MONTHS = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

function ymOptions() {
  const opts = [];
  const now = new Date();
  for (let y = now.getFullYear(); y >= 2024; y--) {
    const end = y === now.getFullYear() ? now.getMonth() : 11;
    for (let m = end; m >= 0; m--) {
      opts.push({ value: `${y}-${String(m+1).padStart(2,'0')}`, label: `${MONTHS[m]} ${y}` });
    }
  }
  return opts;
}

let journalFilter = 'all';
let journalMonth = '';

export function renderJournalView() {
  const container = document.getElementById('view-journal');
  if (!container) return;

  const filter = Store.state.filters.journal || '';
  let entries = Store.state.journal;

  if (filter === 'project') {
    entries = entries.filter(j => !!j.page_slug);
  } else if (filter === 'noproject') {
    entries = entries.filter(j => !j.page_slug);
  }

  if (!journalMonth) {
    const now = new Date();
    journalMonth = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
  }
  const [y, m] = journalMonth.split('-');
  const prefix = `${y}-${m}-`;
  const monthEntries = entries.filter(j => j.date && j.date.startsWith(prefix));

  const byDay = {};
  monthEntries.forEach(j => {
    const d = j.date;
    byDay[d] = byDay[d] || [];
    byDay[d].push(j);
  });
  const days = Object.keys(byDay).sort((a, b) => b.localeCompare(a));

  const opts = ymOptions();

  let html = `<div class="view-header"><h1>Journal</h1>`
    + `<div style="display:flex;gap:8px">`
    + `<select data-pb-filter="journal" style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)">`
    + `<option value="" ${filter === '' ? 'selected' : ''}>Todos</option>`
    + `<option value="project" ${filter === 'project' ? 'selected' : ''}>Con proyecto</option>`
    + `<option value="noproject" ${filter === 'noproject' ? 'selected' : ''}>Sin proyecto</option>`
    + `</select>`
    + `<select data-pb-month style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)">`
    + opts.map(o => `<option value="${o.value}" ${journalMonth === o.value ? 'selected' : ''}>${esc(o.label)}</option>`).join('')
    + `</select>`
    + `</div>`
    + `</div>`;

  html += `<p style="color:var(--mute);margin-bottom:20px">${monthEntries.length} entradas</p>`;

  if (!days.length) {
    html += '<p style="color:var(--mute)">No hay entradas este mes.</p>';
  } else {
    days.forEach(d => {
      html += `<div class="journal-day"><h2>${esc(d)}</h2>`;
      byDay[d].forEach(j => {
        html += `<div class="card" style="cursor:pointer" data-pb-journal="${esc(j.id || j.slug || '')}">`
          + `<h3>${esc(j.title)}</h3>`
          + (j.mood ? `<div style="font-size:11px;color:var(--mute)">${esc(j.mood)}</div>` : '')
          + `<div class="md-content" style="font-size:13px;color:var(--body);margin-top:4px">${window.mdToHtml ? window.mdToHtml(j.body || j.content || '') : esc(j.body || j.content || '')}</div>`
          + `</div>`;
      });
      html += `</div>`;
    });
  }

  container.innerHTML = html;

  const select = container.querySelector('select[data-pb-filter="journal"]');
  if (select) {
    select.addEventListener('change', e => {
      Store.setFilter('journal', e.target.value);
      renderJournalView();
    });
  }

  const monthSelect = container.querySelector('select[data-pb-month]');
  if (monthSelect) {
    monthSelect.addEventListener('change', e => {
      journalMonth = e.target.value;
      renderJournalView();
    });
  }

  container.querySelectorAll('[data-pb-journal]').forEach(el => {
    el.addEventListener('click', () => {
      const key = el.dataset.pbJournal;
      const j = Store.state.journal.find(x => String(x.id) === key || String(x.slug) === key);
      if (j && j.page_slug && typeof window.showPage === 'function') {
        window.showPage(j.page_slug);
      } else if (j && typeof window.showTab === 'function') {
        window.showTab('wiki');
      }
    });
  });
}

export default renderJournalView;
