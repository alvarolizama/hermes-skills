import Store from '../store.js';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const COLUMNS = ['backlog', 'this week', 'today', 'in progress', 'done', 'cancelled'];
const COLUMN_LABELS = {
  backlog: 'BACKLOG',
  'this week': 'THIS WEEK',
  today: 'TODAY',
  'in progress': 'IN PROGRESS',
  done: 'DONE',
  cancelled: 'CANCELLED'
};

export function renderTodosView() {
  const container = document.getElementById('view-todos');
  if (!container) return;

  const filter = Store.state.filters.todo || '';
  let todos = Store.state.todos;

  if (filter === 'project') {
    todos = todos.filter(t => !!t.page_slug);
  } else if (filter === 'noproject') {
    todos = todos.filter(t => !t.page_slug);
  }

  const byCol = {};
  COLUMNS.forEach(c => byCol[c] = []);
  todos.forEach(t => {
    const c = t.status || 'backlog';
    if (byCol[c]) byCol[c].push(t);
  });

  let html = `<div class="view-header"><h1>Todo</h1>`
    + `<select data-pb-filter="todo" style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)">`
    + `<option value="" ${filter === '' ? 'selected' : ''}>Todos</option>`
    + `<option value="project" ${filter === 'project' ? 'selected' : ''}>Con proyecto</option>`
    + `<option value="noproject" ${filter === 'noproject' ? 'selected' : ''}>Sin proyecto</option>`
    + `</select></div>`;

  html += `<div class="kanban">`;
  COLUMNS.forEach(c => {
    const items = byCol[c];
    html += `<div class="kanban-col"><h3>${COLUMN_LABELS[c]} (${items.length})</h3>`;
    items.forEach(t => {
      html += `<div class="kanban-card" data-pb-todo="${esc(t.id)}" style="cursor:pointer">`
        + esc(t.title)
        + (t.domain ? `<div class="meta2">${esc(t.domain)}</div>` : '')
        + `</div>`;
    });
    html += `</div>`;
  });
  html += `</div>`;

  container.innerHTML = html;

  const select = container.querySelector('select[data-pb-filter="todo"]');
  if (select) {
    select.addEventListener('change', e => {
      Store.setFilter('todo', e.target.value);
      renderTodosView();
    });
  }

  container.querySelectorAll('[data-pb-todo]').forEach(el => {
    el.addEventListener('click', () => {
      const id = el.dataset.pbTodo;
      const todo = Store.state.todos.find(t => String(t.id) === id);
      let slug = todo && (todo.page_slug || todo.goal_id);
      if (todo && todo.goal_id && !slug) {
        const goal = Store.state.goals.find(g => String(g.id) === String(todo.goal_id));
        slug = goal && (goal.page_slug || goal.slug);
      }
      if (slug && typeof window.showPage === 'function') {
        window.showPage(slug);
      } else if (todo && todo.title && typeof window.showTab === 'function') {
        window.showTab('wiki');
      }
    });
  });
}

export default renderTodosView;
