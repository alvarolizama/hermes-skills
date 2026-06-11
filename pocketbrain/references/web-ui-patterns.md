# UI Patterns — web_ui.html

Patrones arquitectónicos y diseño de la interfaz web de PocketBrain.

## Vista de proyecto: tabs principales

El proyecto tiene tabs principales: `Contenido` (por defecto) → `Goals` → `Kanban` → `Recordatorios` → `Journal` → `Archivos` → `Entregables` → `Graph`.

- El **tab por defecto es Contenido**, renderizando el `body` markdown del proyecto (`mdToHtml(p.body)`).
- **No se inserta un resumen o meta pills arriba del tab nav**, solo el título + breadcrumb (icono flecha + "Proyectos"), luego los tabs, luego el contenido.
- Cada tab `<a>` tiene `href="\\#\"` y `onclick="...; return false;"` — sin `href` o `return false` se recarga la SPA (blank page).

```js
h += '<div class="project-tabs">' +
     '<a class="active" href="\\#" onclick="switchProjectTab(\\'content\\',\\''+slug+'\\'); return false;">Contenido</a>' +
     '<a href="\\#" onclick="switchProjectTab(\\'goals\\',\\''+slug+'\\'); return false;">Goals</a>' +
     ... +
     '</div>';
```

## Sub-tabs de filtrado en Goals (general y por proyecto)

Tanto la vista general de Goals (sidebar → Goals) como el tab Goals dentro de un proyecto deben tener sub-tabs para filtrar por status: **Todos | Activos | Terminados | Cancelados**.

```js
// En renderGoalsView (general)
var h = '<div class="project-tabs" style="margin-bottom:12px">' +
        '<a href="#" onclick="event.preventDefault(); _goalStatusFilter=\\'all\\'; renderGoalsView(); return false;" ' + 
          (_goalStatusFilter === 'all' ? 'class=\"active\"' : '') + '>Todos</a>' + ...;

// En tab goals de proyecto (dentro switchProjectTab)
if (tab === 'goals') {
  var gsf = window._projGoalStatus || 'all';
  h += '<div class="project-tabs">' ...; // mismo patrón, variable window._projGoalStatus
  var pGoals = d.goals;
  if (gsf === 'active') pGoals = pGoals.filter(g => g.status === 'active' || g.status === 'planned');
  ...
}
```

**Variable**: `_goalStatusFilter` (global) → `renderGoalsView()`. `window._projGoalStatus` (por proyecto en tab) → `switchProjectTab('goals', slug)`.

**Filtro de status**: `active` agrupa `active` + `planned`; `completed` = `completed`; `cancelled` = `cancelled`.

## Patrón general: filtros de tabs en project detail

Cada tab de proyecto que muestra una lista filtrable (Goals, Reminders, Kanban) usa el **mismo patrón arquitectónico**:

1. **Variable global** `window._proj*Filter` para persistir el filtro entre renders.
2. **Setter** `setProj*Filter(s)` que muta la variable y re-renderiza el tab.
3. **Tabs dinámicos** con conteo por filtro y `active` class en el filtro actual.
4. **Render condicional** dentro de `switchProjectTab()` según `window._proj*Filter`.

### Ejemplos concretos:

| Tab | Variable global | Setter | Filtros |
|-----|----------------|--------|---------|
| Goals | `window._projGoalStatus` | `setProjGoalStatus(s)` | all / active / completed / cancelled |
| Reminders | `window._projReminderStatusTab` | `setProjReminderStatus(s)` | today / week / future / overdue / done / all |
| Kanban | `window._projKanbanFilter` | `setProjKanbanFilter(s)` | all / no-goal / by-goal |

### Goals: filtrado por status

```js
function setProjGoalStatus(s) {
  window._projGoalStatus = s;
  switchProjectTab('goals', window._projectData.slug);
}
// En switchProjectTab('goals'):
var gsf = window._projGoalStatus || 'all';
var pGoalsAll = d.goals;
var cAll = pGoalsAll.length, cActive = pGoalsAll.filter(g => g.status === 'active' || g.status === 'planned').length;
// ... tabs con conteos ...
var pGoals = d.goals;
if (gsf === 'active') pGoals = pGoals.filter(g => g.status === 'active' || g.status === 'planned');
```

### Reminders: filtrado por fecha

```js
function setProjReminderStatus(s) {
  window._projReminderStatusTab = s;
  switchProjectTab('reminders', window._projectData.slug);
}
```

### Kanban: filtrado por goal association

El kanban tiene tres modos de visualización que cambian completamente la estructura de columnas:

- **Todas** (default): todas las tareas del proyecto, agrupadas por status en columnas fijas (backlog → cancelled).
- **Sin Goal**: tareas donde `!t.goal_id`, mismas columnas de status.
- **Por Goal**: columnas = goals del proyecto (más "Sin Goal" como última columna). Cada columna contiene las tareas de ese goal, con status+domain en la meta.

```js
function setProjKanbanFilter(s) {
  window._projKanbanFilter = s;
  switchProjectTab('kanban', window._projectData.slug);
}
// En switchProjectTab('kanban'):
var kf = window._projKanbanFilter || 'all';
var cAll = d.todos.length;
var cNoGoal = d.todos.filter(function(t) { return !t.goal_id; }).length;
var cByGoal = d.todos.filter(function(t) { return !!t.goal_id; }).length;
// Tabs: Todas (N) | Sin Goal (N) | Por Goal (N)

if (kf === 'by-goal') {
  // Columnas por goal
  var gcols = [];
  d.goals.forEach(function(g) { gcols.push({id: g.id, title: g.title, type: g.type, todos: []}); });
  gcols.push({id: null, title: 'Sin Goal', type: 'none', todos: []});
  d.todos.forEach(function(t) {
    var found = false;
    for (var i = 0; i < gcols.length - 1; i++) {
      if (gcols[i].id === t.goal_id) { gcols[i].todos.push(t); found = true; break; }
    }
    if (!found) gcols[gcols.length - 1].todos.push(t);
  });
  // Render kanban con gcols como columnas (solo si tienen todos)
} else {
  // Kanban por status: ss = ['backlog','this week','today','in progress','done','cancelled']
  var filtered = (kf === 'no-goal') ? d.todos.filter(function(t) { return !t.goal_id; }) : d.todos;
  // distribuir en bs[status]
}
```

**Regla:** cuando se agrega un nuevo filtro de tab de proyecto, seguir este patrón exacto. No inventar nombres nuevos para variables o funciones; usar `_proj` + `NombreTab` + `Filter/Status` y `setProj` + `NombreTab` + `Filter/Status`.

## Tab active state: nunca hardcodear `class="active"`

**Regla de oro:** ninguna tab `<a>` debe nacer con `class="active"` hardcodeada en el HTML generado por JS. El estado activo debe manejarse **dinámicamente** mediante la función switch de cada vista.

### ❌ Incorrecto (causa el bug de tab fantasma)

```javascript
// En renderProjectView() o showPage():
var h = '<div class="project-tabs">' +
     '<a class="active" href="#" onclick="switchProjectTab(\\'content\\',\\''+slug+'\\')">Contenido</a>' +
     '<a href="#" onclick="switchProjectTab(\\'goals\\',\\''+slug+'\\')">Goals</a>' +
     '</div>';
```

**Síntoma del bug:** al cambiar de proyecto, el primer tab del proyecto anterior sigue apareciendo como "activo" visualmente, aunque el contenido sea del nuevo proyecto o de otro tab. Esto pasa porque el HTML viejo se reemplaza pero el `class="active"` hardcodeado en el nuevo HTML no refleja el estado real.

### ✅ Correcto — estado dinámico vía switch

```javascript
// En renderProjectView():
var h = '<div class="project-tabs">' +
     '<a href="#" onclick="switchProjectTab(\\'content\\',\\''+slug+'\\')">Contenido</a>' +
     '<a href="#" onclick="switchProjectTab(\\'goals\\',\\''+slug+'\\')">Goals</a>' +
     '</div>';

// Llamar switch para mostrar contenido y marcar el tab correcto:
switchProjectTab('content', slug);
```

```javascript
// En switchProjectTab(): SIEMPRE resetear active y marcar el correcto
function switchProjectTab(tab, slug, el) {
  // Siempre quitar active de todos los tabs
  document.querySelectorAll('.project-tabs a').forEach(function(a) {
    a.classList.remove('active');
  });
  // Marcar el clickeado si hay el, o buscar por indice si no
  if (el) {
    el.classList.add('active');
  } else {
    var links = document.querySelectorAll('#view-todos .project-tabs a');
    var map = {content:0, goals:1, kanban:2, reminders:3, journal:4, files:5, deliverables:6, graph:7};
    if (links.length && map[tab] !== undefined) links[map[tab]].classList.add('active');
  }
  // ... renderizar contenido del tab
}
```

**Patrón:** la función switch SIEMPRE limpia todos los `active` y luego marca el correspondiente, sin depender de si fue llamada por click (`el`) o programáticamente. Así al abrir un nuevo proyecto, se renderiza sin tabs fantasma.

**Verificación después del fix:**
1. Abrir proyecto A → se ve "Contenido" activo ✅
2. Click en "Goals" → Goals activo ✅
3. Volver a proyectos y abrir proyecto B → "Contenido" activo (no Goals) ✅
4. Click en "Kanban" en proyecto B → Kanban activo, volver a proyecto A → "Goals" (el estado anterior se perdio, correcto) ✅

Lo mismo aplica a `showPage()` y `switchPageTab()`.

## Kanban: full-width + full-height dentro del proyecto

Dentro del tab `Kanban` del proyecto, el board debe ocupar todo el espacio disponible (100% ancho, 100% alto de su contenedor):

```css
/* CSS: project-tab-content es contenedor flex */
#project-tab-content { display: flex; flex-direction: column; flex: 1; min-height: 0; }

/* JS: kanban con flex:1 */
h += '<div class="kanban" style="flex:1; min-height:0">';
```

**Columnas**: `.kanban-col` usa `flex: 0 0 260px; min-width: 260px; max-height: 100%;` para que sean scrolleables horizontalmente si hay muchas.

## Markdown renderer: mdToHtml()

Función inline en el HTML. Mejoras aplicadas:
1. **Escapar HTML** en `code` blocks y texto plano: `& → &amp;`, `< → &lt;`, etc.
2. **Bold**: `"**text**"` o `"**text**"` (double asterisk).
3. **Italic**: `*text*` (single asterisk) — con regex negativa para evitar conflictos con `**`.
4. **Listas**: unordered `ul`/`li` con `- ` o `* `; ordered `ol`/`li` con `1. `.
5. **Links**: `[text](url)` se abren como `<a target="_blank" class="wl">text</a>`.
6. **Wikilinks**: `[[Slug]]` o `[[Page|Alias]]` → `showPage()` o `<span class="bl">` (si no existe).
7. **Blockquotes**: `> texto` → `<blockquote>`.
8. **Cierre de listas**: `closeList()` al final de cada bloque o línea vacía.

```js
function mdToHtml(text) {
  if (!text) return '';
  var lines = text.split('\\n'), out = [], ic = false, ul = false, ol = false;
  function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\\\"/g,'&quot;'); }
  function rl(tx) {
    tx = tx.replace(/\\*\\*\\*(.+?)\\*\\*\\*/g, '<strong><em>$1</em></strong>');
    tx = tx.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
    tx = tx.replace(/\\*(?!\\*)(.+?)\\*/g, '<em>$1</em>');
    return tx;
  }
  function closeList() { ... }
  // ... parseo por línea
  return out.join('\\n');
}
```

## Iconos: Heroicons SVG inline (no emojis, no font icons)

No usar emojis Unicode (☘, ↙, ↑) — en algunos sistemas no renderizan o se ven distintos. No usar font-icon libraries (requieren CDN).

**Solución**: helper `icon()` que inserta SVG `<path>` inline con los `d` de Heroicons 24 outline (descargados vía curl).

```js
var _ICONS = {
  'squares-2x2': 'M3.75 6A2.25...',
  'flag': 'M3 3v1.5...',
  // ...
};
function icon(name, size) {
  size = size || 20;
  return '<svg xmlns="http://www.w3.org/2000/svg" width="'+size+'" height="'+size+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="'+_ICONS[name]+'"/></svg>';
}
```

Usar `icon('arrow-left', 16) + ' Proyectos'` en el breadcrumb de la vista de proyecto, y en los headers de cada sección (Reminders: icon('exclamation-triangle') + ' Atrasados').

## Tab positioning: tabs always above the header/title

**Regla de diseño:** En todas las vistas con tabs, los tabs deben estar **arriba** del breadcrumb, título `<h1>`, dropdown de filtro, y contenido. Nunca entre el título y el contenido, ni entre breadcrumb y título.

### Vistas afectadas (todas cumplen el patrón `tabs → header → content`):

- **Goals (general)**: tabs de status (Todos/Activos/Terminados/Cancelados) → h1 "Goals" → dropdown de filtro por proyecto → lista
- **Reminders**: tabs (Hoy/Esta semana/Próximos/Atrasados/Completados/Todos) → h1 "Reminders" → dropdown de filtro por proyecto → lista
- **Project detail**: tabs (Contenido/Goals/Kanban/Recordatorios/Journal/Archivos/Entregables/Graph) → breadcrumb "Proyectos" → h1 título del proyecto → contenido
- **Wiki page detail**: tabs (Contenido/Backlinks/Relacionado) → breadcrumb "Wiki" → h1 título de la página → layout dos columnas

### Antipatrón: tabs entre título y contenido

```html
<!-- NO — tabs enterrados entre h1 y contenido -->
<h1>Goals</h1>
<div class="project-tabs">...</div>  <!-- mal -->
<p>17 goals</p>
```

```html
<!-- SÍ — tabs arriba de TODO -->
<div class="project-tabs">...</div>
<h1>Goals</h1>
<p>17 goals</p>
```

En el project detail, el título va DEBAJO del breadcrumb, y el breadcrumb DEBAJO de los tabs:
```html
<div class="project-tabs">...Contenido...Goals...</div>
<div style="font-size:12px">← Proyectos</div>
<h1>Viaje a Japón 2026</h1>
<div id="project-tab-content"></div>
```

## Sidebar: orden de navegación

El sidebar debe listar **Proyectos** como primer ítem, ya que es el entry point principal:
1. Proyectos (icon squares-2x2)
2. Todo (icon clipboard-document-list)
3. Goals (icon flag)
4. Reminders (icon bell)
5. Journal (icon book-open)
6. Files (icon paper-clip)
7. Deliverables (icon cube)
8. Wiki (icon document-text)
9. Graph (◉ Graph)
10. **Lint (icon shield-check)** — al final, abajo de todo

```js
h += icon('squares-2x2',16) + ' Proyectos';
h += ...; // Todo, Goals, etc.
h += '◉ Graph';
h += icon('shield-check',16) + ' Lint';  // último
```

## Mobile: cerrar sidebar automáticamente

```js
function closeSidebar() {
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('open');
  }
}
```

Llamar `closeSidebar()` en `showTab()`, `showProject()`, `showPage()` — cualquier navegación que el usuario inicie desde el menú.

## Sidebar nav badges / counts

Mostrar el número de elementos a la derecha de cada link de navegación en el sidebar (Proyectos 5, Todo 21, etc.).

**Patrón CSS** — flexbox con `justify-content:space-between`:
```css
#nav a.nav-link {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px; color: var(--body); text-decoration: none;
  border-radius: 6px; cursor: pointer; font-size: 13px;
}
#nav a.nav-link:hover, #nav a.nav-link.active { color: var(--ink); background: var(--soft); }
#nav a.nav-link .nav-count {
  font-size: 10px; color: var(--body); background: var(--hairline);
  padding: 1px 6px; border-radius: 9999px; min-width: 20px; text-align: center;
}
#nav a.nav-link.active .nav-count { color: var(--ink); background: var(--canvas); }
```

**Patrón HTML/JS** — cada link envuelve texto + icono en spans, el count en otro span:
```js
// Inside buildSidebar() — compute counts from global arrays first:
var pc = PAGES.filter(function(p) { return p.page_type === 'project'; }).length;
var wc = PAGES.filter(function(p) { return p.page_type !== 'project'; }).length;
var gc = GOALS.length, tc = TODOS.length, rc = REMINDERS.length;
var fc = FILES.length, dc = DEPS.length, jc = JOURNAL.length;
var nc = (GRAPH.nodes || []).length;

// Then render each link with spans:
h += '<a href="#" class="nav-link" onclick="showTab(\\'projects\\')" data-search="projects">' +
     icon('squares-2x2', 16) + '<span>Proyectos</span>' +
     '<span class="nav-count">' + pc + '</span></a>';
h += '<a href="#" class="nav-link" onclick="showTab(\\'todos\\')" data-search="todo">' +
     icon('clipboard-document-list', 16) + '<span>Todo</span>' +
     '<span class="nav-count">' + tc + '</span></a>';
// ... repeat for goals, reminders, journal, files, deliverables, wiki, graph, lint
```

**Pitfall: invisible count badge** — using `background: var(--soft)` (almost white) on a white sidebar makes the badge invisible. Always use `var(--hairline)` for the badge background so it has visible contrast.
**Pitfall: active badge disappears** — when the link is active/hovered, its background changes to `var(--soft)`. The `.nav-count` background must switch to `var(--canvas)` (white) so it pops against the grey active state, not blend in.


**Patrón: icon + label agrupados a la izquierda, badge a la derecha.**

Con flex `space-between`, si el link tiene 3 items (icon, text, badge), el texto queda centrado entre icono y badge. Para anclar el icono + texto juntos a la izquierda, envolverlos en un `<span>` con `.nav-label`:

```css
#nav a.nav-link .nav-label {
  display: flex; align-items: center; gap: 6px; flex: 1;
}
#nav a.nav-link .nav-count {
  font-size: 10px; color: var(--body); background: var(--hairline);
  padding: 1px 6px; border-radius: 9999px; min-width: 20px; text-align: center;
  flex-shrink: 0;
}
```

```js
h += '<a href="#" class="nav-link" onclick="showTab(\\'projects\\')" data-search="projects">' +
     '<span class="nav-label">' + icon('squares-2x2', 16) + '<span>Proyectos</span></span>' +
     '<span class="nav-count">' + pc + '</span></a>';
```

Resultado: `[Icon] [Text]          [Badge]` — el badge se empuja a la derecha por `space-between`, mientras el texto permanece pegado al icono. Si falta `.nav-label`, el texto se distribuye en el espacio medio y no se ve a la izquierda.

## Tab counts: todas las vistas con filtros o tabs

Cualquier vista que tenga tabs de filtrado o categorías debe mostrar el conteo de elementos en cada tab. No solo el sidebar: también los tabs de contenido principal.

### Ejemplos de vistas que necesitan conteos:

- **Goals (general)**: `Todos (N) | Activos (N) | Terminados (N) | Cancelados (N)`
- **Project detail**: `Contenido (N) | Goals (N) | Kanban (N) | Recordatorios (N) | Journal (N) | Archivos (N) | Entregables (N) | Graph (N)`
- **Wiki index**: `Todos (N) | Proyectos (N) | Conceptos (N) | Entidades (N) | ...`
- **Wiki page detail**: `Contenido (1) | Backlinks (N) | Relacionado (N)` — solo si hay contenido/backlinks/relacionados
- **Project goals sub-tabs**: `Todos (N) | Activos (N) | Terminados (N) | Cancelados (N)` — dentro del tab Goals de un proyecto

### Patrón: pre-computar counts antes de renderizar el HTML de tabs

```js
// GOALS view: contar ANTES de generar el HTML de los tabs
var cAll = filtered.filter(function(g) { return !g.parent; }).length;
var cActive = filtered.filter(function(g) { return !g.parent && (g.status === 'active' || g.status === 'planned'); }).length;
var cCompleted = filtered.filter(function(g) { return !g.parent && g.status === 'completed'; }).length;
var cCancelled = filtered.filter(function(g) { return !g.parent && g.status === 'cancelled'; }).length;
// ... luego renderizar:
h += '<a href="#" ...>Todos (' + cAll + ')</a>' + ...;
```

### Pitfall: key mismatch en dict de counts

Cuando se genera un diccionario de counts para tabs, las keys deben coincidir EXACTAMENTE con las keys del array de tabs:

```js
// BUG: keys en español no coinciden con tab.k (en inglés)
var counts = { todos: PAGES.length, proyectos: byType['project'], conceptos: byType['concept'], ... };
// tabs.forEach: t.k = 'all', 'project', 'concept' ...  → counts[t.k] = undefined
// Resultado: "Todos (undefined)"

// FIX: keys del dict deben coincidir exactamente con t.k
var counts = { all: PAGES.length, project: byType['project'], concept: byType['concept'], ... };
```
**Regla:** siempre usar `counts[t.k]` para verificar, no `counts[t.l]` (label). Los keys del dict deben ser el identificador del tab, no el texto mostrado.

## Graph rendering (vis.js): legend debe ser sibling, no child

vis.js Network **reemplaza el innerHTML del contenedor** cuando se inicializa. Cualquier elemento hijo dentro del `div` contenedor (ej. una leyenda de pills) será destruido al crear la red.

### ❌ Incorrecto — leyenda dentro del contenedor (se borra)

```html
<div id="project-graph-view">
  <div id="project-graph-legend">...</div>  <!-- se pierde cuando vis.js init -->
</div>
```

### ✅ Correcto — leyenda como sibling, no child

```html
<div style="position:relative">
  <div id="project-graph-view"></div>
  <div id="project-graph-legend" style="position:absolute;bottom:0;right:0;"></div>
</div>
```

### Mostrar la leyenda después de renderizar el grafo

```js
var lgc = document.getElementById('project-graph-legend');
if (lgc) {
  lgc.innerHTML = plh;
  lgc.style.display = 'block';  // arranca con display:none
}
```

### Page types en leyenda de ambos graphs

La leyenda del grafo global y del project graph deben mostrar **todos los page_types individuales**, no un genérico:

```js
var GTYPE_NAMES = {
  entity: 'Entidades', concept: 'Conceptos', comparison: 'Comparaciones',
  query: 'Consultas', raw: 'Raw', project: 'Proyectos',
  goal: 'Goals', milestone: 'Hitos', okr: 'OKRs',
  todo: 'Todo', deliverable: 'Entregables', reminder: 'Reminders'
};
```

Para el project graph, las page_types se cuentan extrayendo `[[wikilinks]]` del body del proyecto:

```js
var ptCounts = {};
if (d.p && d.p.body) {
  var links = (d.p.body.match(/\\[\\[([^\\]]+)\\]\\]/g) || [])
    .map(function(l) { return l.replace(/[\\[\\]]/g, '').split('|')[0].trim(); });
  links.forEach(function(slug) {
    var pp = pmap[slug];
    if (pp) { var t = pp.page_type || 'concept'; ptCounts[t] = (ptCounts[t] || 0) + 1; }
  });
}
```

Para el backend (brain_web.py), las páginas deben usar su `page_type` como `group` en vez de "page":

```python
nodes.append({
    "id": slug,
    "label": pg.get("title", slug),
    "color": COLORS.get(pg.get("page_type", "concept"), "#607D8B"),
    "group": pg.get("page_type", "concept")  # antes era "page"
})
```

## ShowPage() navigation: deactivate other views

**Regla:** `showPage()` (manejador de wikilinks y clicks en cards) debe desactivar todas las vistas previas antes de activar `view-wiki`. Si no, el div viejo queda con `display:block` y el contenido se renderiza debajo.

```javascript
function showPage(slug) {
  window._wikiSlug = slug;
  setHashParams({tab:'wiki', page:slug});
  var p = pmap[slug];
  if (!p) { ... return; }
  // ✅ SIEMPRE desactivar vistas previas
  document.querySelectorAll('#main>div').forEach(function(d){
    d.classList.remove('active');
  });
  closeSidebar();
  document.getElementById('view-wiki').classList.add('active');
  // ...render content...
}
```

**Pitfall:** si el viewport tiene dos divs con `active`, el CSS `#main>div.active { display: block }` los apila verticalmente. El usuario ve el contenido de la página wikilinkeada "abajo" de la vista anterior. El browser_vision puede reportar falsamente que "solo se ve una vista" cuando en realidad hay stacking — siempre verificar con `document.querySelectorAll('#main > div.active').length`.

## Empty state: toda sección sin items debe mostrar un mensaje

**Regla:** cualquier tab o sección que pueda estar vacía debe mostrar `"No hay ..."` cuando no hay items. No dejar el `#project-tab-content` vacío sin feedback visual.

### Sections with empty state in project tabs

| Tab en switchProjectTab | Mensaje | Código |
|------------------------|---------|--------|
| goals | `"No hay goals."` | `if(!pGoals.length)h+='<p>No hay goals.</p>'` |
| milestones | `"No hay milestones."` | `if(!projMS.length)h+='<p>No hay milestones.</p>'` |
| ideas | `"No hay ideas relacionadas."` | `if(!ideas.length)h+='<p>No hay ideas relacionadas.</p>'` |
| plans | `"No hay planes relacionados."` | `if(!plans.length)h+='<p>No hay planes relacionados.</p>'` |
| notes | `"No hay notas relacionadas."` | `if(!notes.length)h+='<p>No hay notas relacionadas.</p>'` |
| reminders | `"No hay recordatorios en esta sección."` | `if(!activeSet.length)h+='<p>No hay recordatorios...</p>'` |
| journal | `"No hay entradas."` | `if(!d.jour.length)h+='<p>No hay entradas.</p>'` |
| files | `"No hay archivos adjuntos."` | `if(!fls.length)h+='<p>No hay archivos adjuntos.</p>'` |
| deliverables | `"No hay entregables."` | `if(!dlv.length)h+='<p>No hay entregables.</p>'` |

### Data sources for project tab sections

Cada sección obtiene sus datos de `window._projectData`:

| Tab | Property | Tipo |
|-----|----------|------|
| content | `d.p.body` | string (markdown) |
| goals | `d.goals` | array (filtrable por status y type) |
| milestones | `d.goals.filter(g.type==='milestone')` | array |
| ideas | `d.pideas` | array de slugs |
| plans | `d.pplans` | array de slugs |
| todo/kanban | `d.todos` | array |
| reminders | `d.rems` | array |
| notes | `d.pnotes` | array de slugs |
| journal | `d.jour` | array |
| files | `d.files` | array |
| deliverables | `d.deps` | array |
| graph | `d.p` + graph data | render vis.js |

**Pitfall:** milestones, ideas, plans, notes NO tienen handler en `switchProjectTab()` originalmente. Si agregas el tab en `renderProjectView()`, debes agregar el handler correspondiente en `switchProjectTab()`. Siempre verificar que handler exista para cada tab agregado.

## Journal: filter dual (proyecto + mes/año)

Journal es la única vista que combina dos filtros en el header: proyecto y mes/año. Ambos selectores aparecen en la misma fila del `view-header`.

```javascript
var h='<div class="view-header">'
+ '<h1>Journal</h1>'
+ '<select onchange="setJournalFilter(this.value)">...Todos/Con proyecto/Sin proyecto</select>'
+ '<div class="journal-nav">'
+ '  <select onchange="...month/year...">...</select>'
+ '</div>'
+ '</div>';
```

### Orden de filtrado

1. Primero se aplica el filtro de proyecto (`_journalFilter`) sobre el array `JOURNAL`
2. Luego se aplica el filtro de mes/año (`_journalYear`, `_journalMonth`) sobre el resultado

```javascript
var journalEntries = JOURNAL;
if(_journalFilter==='project') journalEntries = JOURNAL.filter(function(j){return !!j.page_slug;});
else if(_journalFilter==='noproject') journalEntries = JOURNAL.filter(function(j){return !j.page_slug;});
var filtered = journalEntries.filter(function(j){
  var d = new Date(j.date);
  return d.getFullYear() === _journalYear && (d.getMonth()+1) === _journalMonth;
});
```

### Variable y setter

```javascript
var _journalFilter = '';  // junto a las otras filter variables globales
function setJournalFilter(v) { _journalFilter = v; renderJournalView(); }
```

**Patrón:** el filtro de proyecto es el primero en aplicarse (más amplio), el mes/año es el segundo (más específico). Esto evita tener que refetch datos al cambiar el filtro de proyecto.

## Pitfall: carácter Unicode U+2019 (') en archivos de código

El `patch` tool con `replace_all=true` o copiar-pegar desde el chat pueden introducir el caracter Unicode U+2019 (Right Single Quotation Mark, `'`) en lugar de la comilla simple ASCII U+0027 (`'`). 
El HTML no distingue, pero el JS sí: `var h = '...';` → SyntaxError en el browser.

**Síntoma:** `node --check` falla con `SyntaxError: Invalid or unexpected token` en una línea con comillas aparentemente normales. El caracter U+2019 es visualmente idéntico a U+0027 en la mayoría de las fonts.

**Fix:** Si `node --check` falla en una línea con comillas, verificar con `hexdump` o `python3`:
```python
with open('web_ui.html','rb') as f:
    data = f.read()
    # buscar el caracter U+2019 (UTF-8: 0xE2 0x80 0x99)
    if b'\\xe2\\x80\\x99' in data:
        print('Encontrado U+2019 at position', data.index(b'\\xe2\\x80\\x99'))
```
**Prevention:** Nunca copiar código JS con comillas simples desde el editor de chat (puede re-encodificar apóstrofes). Siempre escribir el código directamente en el archivo. O usar `replace_all=true` con `old_string` y `new_string` que no contengan apóstrofos.
