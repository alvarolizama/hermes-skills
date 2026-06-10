# UI Patterns — web_ui.html

Patrones arquitectónicos y diseño de la interfaz web de PocketBrain.

## Vista de proyecto: tabs principales

El proyecto tiene tabs principales: `Contenido` (por defecto) → `Goals` → `Kanban` → `Recordatorios` → `Journal` → `Archivos` → `Entregables` → `Graph`.

- El **tab por defecto es Contenido**, renderizando el `body` markdown del proyecto (`mdToHtml(p.body)`).
- **No se inserta un resumen o meta pills arriba del tab nav**, solo el título + breadcrumb (icono flecha + "Proyectos"), luego los tabs, luego el contenido.
- Cada tab `<a>` tiene `href="\#"` y `onclick="...; return false;"` — sin `href` o `return false` se recarga la SPA (blank page).

```js
h += '<div class="project-tabs">' +
     '<a class="active" href="\#" onclick="switchProjectTab(\'content\',\''+slug+'\'); return false;">Contenido</a>' +
     '<a href="\#" onclick="switchProjectTab(\'goals\',\''+slug+'\'); return false;">Goals</a>' +
     ... +
     '</div>';
```

## Sub-tabs de filtrado en Goals (general y por proyecto)

Tanto la vista general de Goals (sidebar → Goals) como el tab Goals dentro de un proyecto deben tener sub-tabs para filtrar por status: **Todos | Activos | Terminados | Cancelados**.

```js
// En renderGoalsView (general)
var h = '<div class="project-tabs" style="margin-bottom:12px">' +
        '<a href="#" onclick="event.preventDefault(); _goalStatusFilter=\'all\'; renderGoalsView(); return false;" ' + 
          (_goalStatusFilter === 'all' ? 'class="active"' : '') + '>Todos</a>' + ...;

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
  var lines = text.split('\n'), out = [], ic = false, ul = false, ol = false;
  function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;'); }
  function rl(tx) {
    tx = tx.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    tx = tx.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    tx = tx.replace(/\*(?!\*)(.+?)\*/g, '<em>$1</em>');
    return tx;
  }
  function closeList() { ... }
  // ... parseo por línea
  return out.join('\n');
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
9. Graph (icon chart-pie)

```js
h += icon('squares-2x2',16) + ' Proyectos';
h += ...; // Todo, Goals, etc.
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
h += '<a href="#" class="nav-link" onclick="showTab(\'projects\')" data-search="projects">' +
     icon('squares-2x2', 16) + '<span>Proyectos</span>' +
     '<span class="nav-count">' + pc + '</span></a>';
h += '<a href="#" class="nav-link" onclick="showTab(\'todos\')" data-search="todo">' +
     icon('clipboard-document-list', 16) + '<span>Todo</span>' +
     '<span class="nav-count">' + tc + '</span></a>';
// ... repeat for goals, reminders, journal, files, deliverables, wiki, graph
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
h += '<a href="#" class="nav-link" onclick="showTab(\'projects\')" data-search="projects">' +
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

## Pitfall: carácter Unicode U+2019 (’) en archivos de código

El `patch` tool con `replace_all=true` o copiar-pegar desde el chat pueden introducir el caracter Unicode U+2019 (Right Single Quotation Mark, `’`) en lugar de la comilla simple ASCII U+0027 (`'`). 
El HTML no distingue, pero el JS sí: `var h = '...’;` → SyntaxError en el browser.

**Síntoma:** `node --check` falla con `SyntaxError: Invalid or unexpected token` en una línea con comillas aparentemente normales. El caracter U+2019 es visualmente idéntico a U+0027 en la mayoría de las fonts.

**Fix:** Si `node --check` falla en una línea con comillas, verificar con `hexdump` o `python3`:
```python
with open('web_ui.html','rb') as f:
    data = f.read()
    # buscar el caracter U+2019 (UTF-8: 0xE2 0x80 0x99)
    if b'\xe2\x80\x99' in data:
        print('Encontrado U+2019 at position', data.index(b'\xe2\x80\x99'))
```
**Prevention:** Nunca copiar código JS con comillas simples desde el editor de chat (puede re-encodificar apóstrofes). Siempre escribir el código directamente en el archivo. O usar `replace_all=true` con `old_string` y `new_string` que no contengan apóstrofos.

