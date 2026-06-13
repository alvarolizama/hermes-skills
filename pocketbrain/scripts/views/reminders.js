import Store from '../store.js';
import { Tabs, bindTabs } from '../components/Tabs.js';
import { icon } from '../components/Icon.js';
import { setHashParams } from '../router.js';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const TAB_IDS = ['all', 'today', 'week', 'upcoming', 'overdue', 'done'];
const TAB_LABELS = {
  all: 'Todos',
  today: 'Hoy',
  week: 'Esta semana',
  upcoming: 'Próximos',
  overdue: 'Atrasados',
  done: 'Completados'
};
const TAB_ICONS = {
  all: 'squares-2x2',
  today: 'sun',
  week: 'calendar-days',
  upcoming: 'arrow-right-circle',
  overdue: 'exclamation-circle',
  done: 'check-circle'
};

let reminderStatus = 'all';

export function renderRemindersView() {
  const container = document.getElementById('view-reminders');
  if (!container) return;

  const filter = Store.state.filters.reminder || '';
  let reminders = Store.state.reminders;

  if (filter === 'project') {
    reminders = reminders.filter(r => !!r.page_slug);
  } else if (filter === 'noproject') {
    reminders = reminders.filter(r => !r.page_slug);
  }

  const today = new Date().toISOString().slice(0, 10);
  const counts = {
    all: reminders.length,
    today: reminders.filter(r => r.date === today).length,
    week: 0,
    upcoming: 0,
    overdue: 0,
    done: reminders.filter(r => r.done).length
  };

  reminders.forEach(r => {
    if (r.done) return;
    const d = r.date || '';
    if (d < today) counts.overdue++;
    else if (d > today) counts.upcoming++;
  });

  let filtered = reminders;
  if (reminderStatus === 'today') filtered = reminders.filter(r => r.date === today);
  else if (reminderStatus === 'week') filtered = reminders.filter(r => false);
  else if (reminderStatus === 'upcoming') filtered = reminders.filter(r => !r.done && r.date >= today);
  else if (reminderStatus === 'overdue') filtered = reminders.filter(r => !r.done && r.date < today);
  else if (reminderStatus === 'done') filtered = reminders.filter(r => r.done);

  let html = `<div class="view-header">`
    + `<div class="project-breadcrumb" style="margin-bottom:8px">`
    + `<a href="javascript:void(0)" data-pb-back-projects>${icon('arrow-left', 12)}<span>Proyectos</span></a>`
    + `<span class="project-breadcrumb-sep">/</span><span>Reminders</span>`
    + `</div>`
    + `<div class="view-title-row"><h1>${icon('bell', 20)}<span>Reminders</span></h1>`
    + `<select data-pb-filter="reminder" class="filter-select">`
    + `<option value="" ${filter === '' ? 'selected' : ''}>Todos</option>`
    + `<option value="project" ${filter === 'project' ? 'selected' : ''}>Con proyecto</option>`
    + `<option value="noproject" ${filter === 'noproject' ? 'selected' : ''}>Sin proyecto</option>`
    + `</select></div>`
    + `<p class="view-subtitle">${filtered.length} reminders</p></div>`;

  html += Tabs({
    items: TAB_IDS.map(id => ({ id, label: TAB_LABELS[id], icon: TAB_ICONS[id] })),
    active: reminderStatus,
    counts
  });

  html += `<div class="cards-grid">`;

  if (!filtered.length) {
    html += '<p style="color:var(--mute)">No hay reminders.</p>';
  } else {
    filtered.forEach(r => {
      const cls = !r.done && r.date < today ? 'reminder-overdue' : '';
      html += `<div class="card ${cls}" style="cursor:pointer;padding:12px;margin-bottom:8px" data-pb-reminder="${esc(r.id || r.slug || '')}">`
        + `<h3>${esc(r.title)}</h3>`
        + `<div style="font-size:12px;color:var(--mute);display:flex;align-items:center;gap:6px;margin-top:4px">`
        + `${icon('calendar', 12)}${esc(r.date)}${r.time ? ' · ' + esc(r.time) : ''}${r.done ? icon('check-circle', 12) : ''}`
        + `</div>`
        + `</div>`;
    });
  }

  html += '</div>';

  container.innerHTML = html;

  const select = container.querySelector('select[data-pb-filter="reminder"]');
  if (select) {
    select.addEventListener('change', e => {
      Store.setFilter('reminder', e.target.value);
      renderRemindersView();
    });
  }

  const back = container.querySelector('[data-pb-back-projects]');
  if (back) {
    back.addEventListener('click', e => {
      e.preventDefault();
      if (typeof window.showTab === 'function') window.showTab('projects');
    });
  }

  const tabsRoot = container.querySelector('.project-tabs');
  if (tabsRoot) {
    bindTabs(tabsRoot, id => {
      reminderStatus = id;
      setHashParams({ tab: 'reminders', rstatus: id });
      renderRemindersView();
    });
  }

  container.querySelectorAll('[data-pb-reminder]').forEach(el => {
    el.addEventListener('click', () => {
      const key = el.dataset.pbReminder;
      const r = Store.state.reminders.find(x => String(x.id) === key || String(x.slug) === key);
      if (r && r.page_slug && typeof window.showPage === 'function') {
        window.showPage(r.page_slug);
      } else if (r && typeof window.showTab === 'function') {
        window.showTab('wiki');
      }
    });
  });
}

export default renderRemindersView;
