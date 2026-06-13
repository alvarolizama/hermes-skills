# Frontend modular con ES modules

Guía concreta para refactorizar el frontend monolítico de PocketBrain (`web_ui.html`) a módulos ES con un SPA shell.

## Cuándo aplicar

- `web_ui.html` supera las 600 líneas de JS inline.
- Hay variables globales inmanejables (`PAGES`, `GOALS`, `TODOS`, ...).
- Se repiten patrones de filtrado, tabs y cards en múltiples vistas.
- Necesitas tests de sintaxis con `node --check` para cada vista.

## Estructura de archivos

```
~/.hermes/skills/productivity/pocketbrain/scripts/
├── web_ui.html          # solo estructura HTML + <script type="module" src="/app.js">
├── web_ui.css           # estilos extraídos del inline <style>
├── app.js               # entry point
├── api.js               # fetch wrapper con context
├── store.js             # estado centralizado
├── router.js            # hash routing
├── markdown.js          # renderer MD con wikilinks
├── components/
│   ├── Tabs.js          # tabs reutilizable
│   └── Icon.js          # Heroicons SVG helper
└── views/
    ├── projects.js
    ├── todos.js
    ├── reminders.js
    ├── journal.js
    ├── type.js
    ├── files.js
    ├── deliverables.js
    ├── goals.js
    ├── milestones.js
    ├── wiki.js
    ├── graph.js
    └── lint.js
```

## Reglas de diseño para todas las vistas

1. **Layout unificado**: H1 + select de filtro en `.view-header` (select a la derecha). Status tabs debajo con `margin:12px 0`.
2. **Cards minimalistas**: solo título, cursor pointer, sin chips ni metadata.
3. **Event delegation**: no inline `onclick`. Usar `data-*` attributes y agregar listeners después de renderizar.
4. **Filtros estándar**: `Todos` / `Con proyecto` / `Sin proyecto`.
5. **Hash routing**: cada navegación llama `setHashParams()` y usa `href="javascript:void(0)"`.
6. **Iconos**: Heroicons SVG via `components/Icon.js`.

## api.js

```javascript
const API = {
  ctx: 'personal',
  setContext(name) { this.ctx = name || 'personal'; },
  async request(method, path, body = null) {
    const sep = path.includes('?') ? '&' : '?';
    const url = `/api${path}${sep}context=${encodeURIComponent(this.ctx)}`;
    const opts = { method, headers: {} };
    if (body !== null) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(`${method} ${path} -> ${res.status}`);
    const text = await res.text();
    return text ? JSON.parse(text) : null;
  },
  get(path) { return this.request('GET', path); },
  post(path, body) { return this.request('POST', path, body); },
  patch(path, body) { return this.request('PATCH', path, body); },
  del(path) { return this.request('DELETE', path); },
  loadAll() {
    return Promise.all([
      this.get('/pages'), this.get('/goals'), this.get('/todos'),
      this.get('/deps'), this.get('/files'), this.get('/reminders'),
      this.get('/journal'), this.get('/graph'), this.get('/logs')
    ]);
  }
};
export default API;
```

## store.js

```javascript
const initialState = {
  context: 'personal',
  pages: [], goals: [], todos: [], deps: [], files: [],
  reminders: [], journal: [], graph: { nodes: [], edges: [] }, logs: [],
  loading: false, offline: false, error: null,
  filters: { page: '', goal: '', todo: '', reminder: '', journal: '', file: '', dep: '' }
};

const Store = {
  state: { ...initialState },
  listeners: [],
  subscribe(fn) { this.listeners.push(fn); return () => { this.listeners = this.listeners.filter(l => l !== fn); }; },
  notify() { this.listeners.slice().forEach(fn => fn(this.state)); },
  set(key, value) {
    if (key && typeof key === 'object') Object.assign(this.state, key);
    else this.state[key] = value;
    this.notify();
  },
  get(key) { return key === undefined ? this.state : this.state[key]; },
  mapPages() { const m = {}; this.state.pages.forEach(p => { if (p.slug) m[p.slug] = p; }); return m; },
  setFilter(view, value) {
    if (!Object.prototype.hasOwnProperty.call(this.state.filters, view)) throw new Error(`Unknown filter: ${view}`);
    this.state.filters = { ...this.state.filters, [view]: String(value ?? '') };
    this.notify();
  }
};
export default Store;
```

## router.js

```javascript
export function getHashParams() {
  const hash = location.hash || '';
  if (!hash || hash === '#') return {};
  const params = {};
  hash.slice(1).split('&').forEach(part => {
    const [k, v] = part.split('=');
    if (k) params[k] = v !== undefined ? decodeURIComponent(v) : '';
  });
  return params;
}

export function setHashParams(params) {
  const parts = [];
  for (const key in params) {
    const value = params[key];
    if (value !== null && value !== undefined && value !== '') parts.push(`${key}=${encodeURIComponent(value)}`);
  }
  history.replaceState(null, '', '#' + parts.join('&'));
}

export const Router = {
  routes: {},
  register(name, handler) { this.routes[name] = handler; },
  go(name, params = {}) {
    const current = getHashParams();
    setHashParams({ ...current, ...params });
    this.resolve();
  },
  resolve() {
    const params = getHashParams();
    if (params.project && this.routes.project) this.routes.project(params.project);
    else if (params.page && this.routes.page) this.routes.page(params.page);
    else if (params.tab && this.routes.tab) this.routes.tab(params.tab);
    else if (this.routes.default) this.routes.default();
  }
};
export default Router;
```

## components/Tabs.js

```javascript
export function Tabs({ items, active, counts = {} }) {
  const tabs = items.map(it => {
    const id = String(it.id ?? '');
    const label = String(it.label ?? '');
    const count = counts[id];
    const display = count !== undefined ? `${label} (${count})` : label;
    const cls = id === active ? 'active' : '';
    return `<a href="javascript:void(0)" class="${cls}" data-tab-id="${id}" onclick="event.preventDefault(); this.closest('.project-tabs').dispatchEvent(new CustomEvent('tab-change',{detail:'${id}',bubbles:true})); return false;">${display}</a>`;
  }).join('');
  return `<div class="project-tabs">${tabs}</div>`;
}
export default Tabs;
```

## Ejemplo mínimo de vista: views/projects.js

```javascript
import Store from '../store.js';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function renderProjectsView() {
  const container = document.getElementById('view-projects');
  if (!container) return;

  const filter = Store.state.filters.page || '';
  let projects = Store.state.pages.filter(p => p.page_type === 'project');
  const projectSlugs = new Set(projects.map(p => p.slug));

  if (filter === 'project') {
    projects = projects.filter(p => p.body && Array.from(projectSlugs).some(slug =>
      p.body.includes('[[' + slug + ']]') || p.body.includes('[[' + slug + '|')
    ));
  } else if (filter === 'noproject') {
    projects = projects.filter(p => !p.body || !Array.from(projectSlugs).some(slug =>
      p.body.includes('[[' + slug + ']]') || p.body.includes('[[' + slug + '|')
    ));
  }

  let html = `<div class="view-header"><h1>Proyectos</h1>
    <select data-pb-filter="page" style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)">
      <option value="" ${filter === '' ? 'selected' : ''}>Todos</option>
      <option value="project" ${filter === 'project' ? 'selected' : ''}>Con proyecto</option>
      <option value="noproject" ${filter === 'noproject' ? 'selected' : ''}>Sin proyecto</option>
    </select></div>`;

  html += `<p style="color:var(--mute);margin-bottom:20px">${projects.length} proyectos</p>`;

  if (!projects.length) {
    html += '<p style="color:var(--mute)">No hay proyectos en este contexto.</p>';
  } else {
    projects.forEach(p => {
      html += `<div class="card" style="cursor:pointer" data-pb-project="${esc(p.slug)}">
        <h3>${esc(p.title)}</h3>
      </div>`;
    });
  }

  container.innerHTML = html;

  container.querySelector('select[data-pb-filter="page"]').addEventListener('change', e => {
    Store.setFilter('page', e.target.value);
    renderProjectsView();
  });

  container.querySelectorAll('[data-pb-project]').forEach(el => {
    el.addEventListener('click', () => {
      const slug = el.dataset.pbProject;
      if (slug && typeof window.showProject === 'function') window.showProject(slug);
    });
  });
}

export default renderProjectsView;
```

## brain_web.py: servir módulos estáticos

```python
elif path == "/app.js":
    self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
    self.wfile.write((Path(__file__).parent / "app.js").read_bytes())
elif path == "/web_ui.css":
    self.send_response(200); self.send_header("Content-Type","text/css; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
    self.wfile.write((Path(__file__).parent / "web_ui.css").read_bytes())
elif path.startswith("/views/") or path.startswith("/components/"):
    js_path = Path(__file__).parent / path.lstrip('/')
    if js_path.exists() and js_path.is_file():
        self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
        self.wfile.write(js_path.read_bytes())
    else:
        self.send_response(404); self.end_headers()
```

**Pitfall:** en Python 3.9, `str.startswith()` no acepta tupla. Usa múltiples `elif` o verifica typo `startsWith`.

## Verificación

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 -m py_compile brain_web.py
node --check app.js router.js api.js store.js markdown.js
node --check components/*.js
for f in views/*.js; do node --check "$f"; done
```

Levantar servidor y verificar con `browser_navigate` + `browser_vision`:

```bash
python3 brain_web.py --context personal --port 8899
# en otra terminal
curl -s http://localhost:8899/views/projects.js | head -1
```

## Checklist antes de declarar "listo"

- [ ] `node --check` pasa para todos los `.js`.
- [ ] `python3 -m py_compile brain_web.py` pasa.
- [ ] Todos los módulos devuelven HTTP 200.
- [ ] Verificar imports/exports: `app.js` debe importar nombres que cada `views/*.js` exporte (node --check no detecta este error).
- [ ] Sidebar renderiza con conteos y sin errores JS.
- [ ] Proyectos, Todo, Goals, Reminders, Wiki, Journal cargan datos.
- [ ] Click en proyecto/card navega correctamente.
- [ ] No queda `href="#"` en el HTML generado.
- [ ] Hard refresh del browser después de cambios en módulos ES.

## Pitfalls descubiertos en refactor real

### Names de exports deben coincidir exactamente

Si `views/files.js` exporta `renderFilesView` pero `app.js` importa `{ renderFiles }`, el módulo falla en runtime del browser con:

```
The requested module './views/files.js' does not provide an export named 'renderFiles'
```

`node --check` NO detecta esto porque valida sintaxis individual, no resolución de imports. **Regla**: estandarizar nombres o usar aliases consistentes en `app.js`:

```javascript
import { renderFilesView as renderFiles } from './views/files.js';
import { renderDeliverablesView as renderDeliverables } from './views/deliverables.js';
```

Verificar la matriz completa de imports con un grep:

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
node --check app.js
grep -E "^export|^import" views/*.js components/*.js app.js | sort
```

### Stubs dejan de funcionar silenciosamente

Cuando delegas la creación de vistas a subagentes, algunos pueden generar stubs tipo "Vista en construcción". Si no verificas cada vista con `browser_navigate` + `browser_vision`, la UI parece cargar pero no muestra datos. **Regla**: ninguna vista declara "listo" sin screenshot de datos reales.

### Cache del browser tras edits

Después de cambiar `app.js` o módulos, el browser puede seguir sirviendo la versión vieja. Si la UI se queda en "Cargando...":
1. Verificar en console el error exacto de import.
2. Confirmar con `curl` que el archivo servido contiene el fix.
3. Forzar hard refresh del browser o abrir en pestaña nueva con querystring único.
4. Matar proceso Python y liberar puerto si es necesario (`lsof -ti:PORT | xargs kill -9`).

### Case-insensitive wikilinks y backlinks

PocketBrain almacena slugs en minúsculas (`pocketbrain`) pero el usuario escribe `[[PocketBrain]]`. Tanto el backend como el frontend deben resolver case-insensitive:

- Backend (`brain_web.py`): usar `slug_by_lower` en `get_pages()` y `get_graph()`.
- Frontend (`markdown.js`): `resolveSlug(target) || resolveSlug(target.toLowerCase())`.

### `brain.py:list_pages()` debe expandir `related_pages`

Sin `expand=related_pages`, `get_pages()` no puede computar `page_slug` para goals/todos/reminders ni backlinks cruzados. Asegurar:

```python
params = {
    'filter': "&&".join(filters),
    'perPage': per_page,
    'expand': 'domain,tags,related_pages',
}
```

### Project detail condicional por datos

Si un proyecto no tiene tareas/reminders/entregables asociados vía `page_slug`, los tabs correspondientes no aparecen. Esto es correcto según diseño minimalista, pero el backend debe devolver `page_slug` correctamente (requiere `expand=related_pages`).

### Onclick en sidebar necesita `;return false`

El hamburguesa y los nav links con `href="javascript:void(0)"` deben terminar el onclick con `;return false;` para evitar que el hash se modifique o el sidebar se comporte raro en móvil.

### Project tabs deben coincidir con handlers

Por cada tab que agregues en el detalle de proyecto, agrega un `else if (tab === 'X')` correspondiente. Si no, el tab se clickea y el contenido queda vacío sin mensaje.