import Store from '../store.js';
import API from '../api.js';
import { icon } from '../components/Icon.js';

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
const COLUMN_ICONS = {
  backlog: 'archive-box',
  'this week': 'calendar',
  today: 'sun',
  'in progress': 'arrow-path',
  done: 'check-circle',
  cancelled: 'x-circle'
};

export function renderTodosView() {
  const container = document.getElementById('view-todos');
  if (!container) return;

  const filter = Store.state.filters.todo || '';
  let todos = Store.state.todos;

  if (filter === 'project') {
    todos = todos.filter(t => !!t.project);
  } else if (filter === 'noproject') {
    todos = todos.filter(t => !t.project);
  }

  const byCol = {};
  COLUMNS.forEach(c => byCol[c] = []);
  todos.forEach(t => {
    const c = t.status || 'backlog';
    if (byCol[c]) byCol[c].push(t);
  });

  let html = `<div class="view-header">`
    + `<div class="project-breadcrumb" style="margin-bottom:8px">`
    + `<a href="javascript:void(0)" data-pb-back-projects>${icon('arrow-left', 12)}<span>Proyectos</span></a>`
    + `<span class="project-breadcrumb-sep">/</span><span>Todo</span>`
    + `</div>`
    + `<div class="view-title-row"><h1>${icon('clipboard-document-list', 20)}<span>Todo</span></h1>`
    + `<select data-pb-filter="todo" class="filter-select">`
    + `<option value="" ${filter === '' ? 'selected' : ''}>Todos</option>`
    + `<option value="project" ${filter === 'project' ? 'selected' : ''}>Con proyecto</option>`
    + `<option value="noproject" ${filter === 'noproject' ? 'selected' : ''}>Sin proyecto</option>`
    + `</select></div>`
    + `<p class="view-subtitle">${todos.length} tareas · ${byCol['done'].length} done · ${byCol['in progress'].length} in progress</p></div>`;

  html += `<div class="kanban-board">`;
  COLUMNS.forEach(c => {
    const items = byCol[c];
    html += `<div class="kanban-column">`
      + `<div class="kanban-column-header">${icon(COLUMN_ICONS[c], 14)}<span>${COLUMN_LABELS[c]}</span><span class="kanban-count">${items.length}</span></div>`
      + `<div class="kanban-column-body">`;
    items.forEach(t => {
      html += `<div class="kanban-card" data-pb-todo="${esc(t.id)}" style="cursor:pointer">`
        + `<div class="kanban-card-title">${esc(t.title)}</div>`
        + (t.goal_title ? `<div class="kanban-card-meta">${esc(t.goal_title)}</div>` : '')
        + `<div class="kanban-current-status">${esc(COLUMN_LABELS[c])}</div>`
        + `<div class="kanban-actions">`;
      COLUMNS.forEach(target => {
        if (target === c) return;
        html += `<button class="kanban-move" data-pb-move-todo="${esc(t.id)}:${esc(target)}" title="Mover a ${esc(COLUMN_LABELS[target])}">${esc(COLUMN_LABELS[target])}</button>`;
      });
      html += `</div></div>`;
    });
    html += `</div></div>`;
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

  const back = container.querySelector('[data-pb-back-projects]');
  if (back) {
    back.addEventListener('click', e => {
      e.preventDefault();
      if (typeof window.showTab === 'function') window.showTab('projects');
    });
  }

  container.querySelectorAll('[data-pb-todo]').forEach(el => {
    el.addEventListener('click', e => {
      const moveBtn = e.target.closest('[data-pb-move-todo]');
      if (moveBtn) {
        e.preventDefault();
        e.stopPropagation();
        const [id, status] = moveBtn.dataset.pbMoveTodo.split(':');
        moveTodo(id, status);
        return;
      }
      const id = el.dataset.pbTodo;
      const todo = Store.state.todos.find(t => String(t.id) === id);
      let slug = todo && (todo.project || todo.goal_id);
      if (todo && todo.goal_id && !slug) {
        const goal = Store.state.goals.find(g => String(g.id) === String(todo.goal_id));
        slug = goal && (goal.project || goal.slug);
      }
      if (slug && typeof window.showPage === 'function') {
        window.showPage(slug);
      } else if (todo && todo.title && typeof window.showTab === 'function') {
        window.showTab('wiki');
      }
    });
  });
}

async function moveTodo(id, status) {
  try {
    await API.patch(`/todos/${id}/status/${status}`);
    const idx = Store.state.todos.findIndex(t => String(t.id) === String(id));
    if (idx >= 0) {
      Store.state.todos[idx] = { ...Store.state.todos[idx], status };
    }
    renderTodosView();
  } catch (err) {
    console.error('moveTodo error', err);
    alert('No se pudo mover la tarea: ' + err.message);
  }
}

export default renderTodosView;
