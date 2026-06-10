# PocketBrain Web UI — Arquitectura

## Separación de archivos

v2.0.0+: el HTML/JS/CSS vive en `web_ui.html` (archivo separado), NO inline en `brain_web.py`.

```python
# brain_web.py — solo lógica Python (API endpoints + routing)
def _load_html():
    html_path = Path(__file__).parent / "web_ui.html"
    return html_path.read_text()
```

**Razón:** el HTML inline (~300 líneas) era ingobernable. Ahora se edita como archivo independiente.

## Server: ThreadingHTTPServer (OBLIGATORIO)

```python
from http.server import ThreadingHTTPServer
server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
```

El browser hace 8 `fetch()` en paralelo (`Promise.all`). Con `HTTPServer` simple (single-threaded), las requests colapsan y la UI muestra "● error". `ThreadingHTTPServer` las maneja concurrentemente.

## Sidebar

- **Sin sub-menús expandibles.** Navegación plana con `nav-link`.
- Solo secciones principales: Todo, Goals, Journal, Reminders, Proyectos, Wiki, Graph.
- Los proyectos se muestran en la vista "Proyectos" del contenido, NO en el sidebar.
- Cada vista tiene su propio dropdown de filtro por proyecto.

```
☐ Todo
◈ Goals
📓 Journal
⏰ Reminders
📁 Proyectos
📄 Wiki
◉ Graph
```

## Vistas

### TODO (Kanban)
- Dropdown de filtro: "Todos" | "Sin proyecto" | lista de proyectos activos del contexto.
- Columnas: Backlog, This Week, Today, In Progress, Done, Cancelled.

### GOALS
- Ídem dropdown de filtro por proyecto.
- Progress bars para goals tipo `goal`.
- Key Results anidados bajo el goal padre.

### REMINDERS (orden de urgencia)
- Secciones: ⚠ Atrasados → Hoy → Esta Semana → Próximos → Completados.
- Cada reminder muestra fecha, hora, proyecto asociado y contenido.
- Atrasados tienen borde rojo (`.reminder-overdue .card`).

### JOURNAL
- Dropdown año/mes a la derecha del título.
- Agrupado por día (`.journal-day`), orden descendente.
- Muestra mood, título y body de cada entrada.

### WIKI
- Índice agrupado por `page_type` (project, concept, entity, etc.).
- Click en una página → `showPage(slug)` con render markdown (`mdToHtml()`).
- `[[wikilinks]]` se convierten en links cliqueables (verdes si existen, rojos tachados si no).

### GRAPH
- Canvas vis.js con nodes (páginas, goals, todos, deliverables, reminders) y edges.
- Leyenda de colores por tipo de nodo.
- ForceAtlas2 physics.

### Proyectos
- Vista con cards de proyectos activos del contexto actual.
- Cada card muestra conteo de goals y tareas.
- Click en card → vista detalle del proyecto con **8 tabs**:

```
┌─ Resumen ─┬─ Goals ─┬─ Kanban ─┬─ Recordatorios ─┬─ Journal ─┬─ Archivos ─┬─ Entregables ─┬─ Graph ─┐
│ stats +   │ cards   │ columnas │ secciones por   │ entradas  │ lista de   │ cards con     │ vis.js  │
│ fechas    │ con     │ kanban   │ urgencia        │ recientes │ archivos   │ status y      │ centrado│
│           │ progress│          │                 │           │ adjuntos   │ versión       │ en proy.│
└───────────┴─────────┴──────────┴─────────────────┴───────────┴────────────┴───────────────┴─────────┘
```

- El tab **Graph** muestra un grafo centrado en el proyecto con nodos para goals, tareas y reminders conectados al nodo central del proyecto. Usa barnesHut physics para layout rápido.
- Los datos se cachean en `window._projectData` para evitar re-fetchear al cambiar de tab.
- La función `switchProjectTab(tab, slug)` renderiza cada tab bajo demanda en `#project-tab-content`.
- El índice de tabs (`idx`) mapea nombre → posición para activar/desactivar clases CSS.

### Wiki (páginas no-proyecto)
- Las páginas que NO son `page_type='project'` ahora también usan tabs:
  - **Contenido**: body renderizado con `mdToHtml()` ([[wikilinks]] cliqueables).
  - **Backlinks**: páginas que enlazan a esta.
  - **Relacionado**: goals, tareas, reminders y journal vinculados a esta página.
- Función `switchPageTab(tab, slug)` — misma arquitectura que project tabs.
- Solo se muestran los tabs que tienen contenido (si no hay backlinks, el tab no aparece).

## Mobile

```html
<button class="hamburger">☰</button>
<span class="mobile-title">PocketBrain</span>
```

- Hamburger + título fijos (`position:fixed`) solo visibles en `@media(max-width:768px)`.
- `.mobile-title` tiene `display:none` por defecto, `display:block` en mobile.
- Sidebar colapsado con `transform:translateX(-100%)`, se abre con toggle de clase `.open`.

## Brain Cache (optimización de API)

`get_brain()` en `brain_web.py` usa un cache por contexto (dict `BN → Brain`) para evitar re-autenticar en cada request:

```python
_brain_cache = {}  # BN -> Brain

def get_brain():
    global _brain_cache
    if BN in _brain_cache:
        return _brain_cache[BN]  # cache hit (~20ms)
    pb = quick_pb(host, email, password)
    brain = Brain(BN, pb=pb)
    brain.orient()  # solo la primera vez por contexto (~140ms)
    _brain_cache[BN] = brain
    return brain
```

**Por qué dict en vez de TTL:** con la versión anterior (cache global con timestamp de 30s), cambiar de contexto (`personal` → `bravo`) devolvía datos del contexto cacheado. El dict por `BN` asegura que cada contexto tenga su propia conexión, y el filtrado por contexto funciona correctamente en el selector.

**Por qué cache:** el browser hace 8 `fetch()` en paralelo al cargar. Sin cache, cada uno crea `PB()` nuevo + auth + `orient()`. Con cache, el primero autentica y los 7 siguientes comparten conexion en ~20ms.

## Kanban CSS: full-width, sin scroll forzado

```css
/* Desktop: columnas ocupan todo el ancho, wrap natural */
.kanban{display:flex;gap:8px;padding-bottom:20px}
.kanban-col{flex:1 1 0;min-width:140px;background:var(--soft);border-radius:12px;padding:12px}

/* Mobile: wrap automático */
@media(max-width:768px){
  .kanban{flex-wrap:wrap}
  .kanban-col{flex:1 1 140px;min-width:140px}
}
```

**Reglas:**
- `flex: 1 1 0` — todas las columnas ocupan el mismo ancho, adaptándose al espacio disponible.
- `min-width: 140px` — evita que se colapsen a 0.
- **NO usar `overflow-x:auto`** — genera scroll bars innecesarios aunque quepan.
- **NO usar `flex:none` o `flex-shrink:0`** — impide que se adapten al viewport.
- En mobile, `flex-wrap:wrap` permite que las columnas se apilen naturalmente.

## Debugging

- El browser tool de Hermes (Browserbase) NO puede hacer `fetch()` a localhost — las requests van al servidor remoto.
- Para testear la UI con datos reales, abrir en Chrome local.
- For verificar APIs: `curl http://localhost:8899/api/<endpoint>?brain=personal`.
- **JS syntax validation:** `node --check` sobre el JS extraído del HTML detecta syntax errors antes de abrir el browser:
  ```bash
  python3 -c "import re; html=open('web_ui.html').read(); m=re.search(r'<script>(.*?)</script>', html, re.DOTALL); open('/tmp/js.js','w').write(m.group(1))"
  node --check /tmp/js.js
  ```

## SPA Hash Routing (URL Deep-Linking)

La interfaz web es una SPA de un solo archivo. Para deep-linking sin framework:

```javascript
// Helpers
function getHashParams(){var hash=location.hash||'';if(!hash||hash==='#')return{};var p={},parts=hash.substring(1).split('&');parts.forEach(function(x){var kv=x.split('=');if(kv.length===2)p[kv[0]]=decodeURIComponent(kv[1]);});return p;}
function setHashParams(p){var parts=[];for(var k in p){if(p[k])parts.push(k+'='+encodeURIComponent(p[k]));}history.replaceState(null,'','#'+parts.join('&'));}
function restoreFromHash(){var hp=getHashParams();if(hp.project){_currentTab='project';_currentProject=hp.project;showCurrentView();}else if(hp.page){_currentTab='wiki';window._wikiSlug=hp.page;showCurrentView();}else if(hp.tab){_currentTab=hp.tab;_currentProject=null;showCurrentView();}}

// En cada función de navegación
function showTab(tab){_currentTab=tab;_currentProject=null;setHashParams({tab:tab});showCurrentView();}
function showProject(slug){_currentTab='project';_currentProject=slug;setHashParams({project:slug});showCurrentView();}
function showPage(slug){window._wikiSlug=slug;setHashParams({tab:'wiki',page:slug});/* ... render ... */}

// Init + popstate
loadBrains();
setTimeout(function(){
  function tryRestore(){if(!PAGES.length){setTimeout(tryRestore,200);return;}var hp=getHashParams();if(hp.project||hp.page||hp.tab)restoreFromHash();}
  tryRestore();
},500);
window.addEventListener('popstate',restoreFromHash);
```

**Por qué `replaceState` y no `pushState`:** en una SPA de un solo archivo con polling cada 30s, `pushState` crearía una entrada por cada navegación, saturando el historial. `replaceState` mantiene una sola entrada activa.

**Por qué retry loop:** `loadBrains()` dispara `loadAll()` que carga datos async. Si `restoreFromHash()` corre antes de que `PAGES` tenga elementos, las vistas detalle (wiki page, project) intentan acceder a `pmap[slug]` que aún no existe. El retry espera a que los datos carguen.

## Graph Legends with Node Counts

### Backend: `get_graph()` returns counts

```python
def get_graph():
    # ... existing node/edge building ...
    counts = {}
    for n in nodes:
        g = n.get("group", "unknown")
        counts[g] = counts.get(g, 0) + 1
    return {"nodes": nodes, "edges": edges, "counts": counts}
```

### Frontend: `renderGraph()` legend

```javascript
var GTYPE_NAMES = {page:'Paginas', goal:'Goals', todo:'Todo', deliverable:'Entregables', reminder:'Reminders'};
var lh = '';
var counts = GRAPH.counts || {};
for (var group in counts) {
    var color = GCOLORS[group] || '#888';
    var label = GTYPE_NAMES[group] || group;
    lh += '<div><span style="background:'+color+'"></span> '+label+' ('+counts[group]+')</div>';
}
document.getElementById('graph-legend').innerHTML = lh;
```

**Positioning:** `bottom:12px;right:12px` via `position:absolute` on `#graph-legend`. The parent `#view-graph.active` must have `position:relative`.

### Frontend: `renderProjectGraph()` legend

```javascript
var ptypes = [];
if (d.goals.length) ptypes.push({label:'Goals', count:d.goals.length, color:'#4CAF50'});
if (d.todos.length) ptypes.push({label:'Tareas', count:d.todos.length, color:'#9C27B0'});
if (d.rems.length) ptypes.push({label:'Reminders', count:d.rems.length, color:'#FFC107'});
ptypes.push({label:'Proyecto', count:1, color:'#E91E63'});
// ... build HTML ...
```

## ⚠️ PITFALLS

### PITFALL 1: JS escaping en HTML — `\\\\''` rompe todo

El JS dentro de `web_ui.html` es un string HTML, NO un archivo .js. Las reglas de escape son DIFERENTES:

- En un `.js`: `\\'` → `\'` → quote literal. Funciona.
- En HTML que será evaluado como JS: `\\\\''` → el parser de JS ve `\\` `\\` `''` → **SyntaxError**.

**Error real que rompió toda la app:**

```javascript
// ROTO — SyntaxError: Unexpected string
var sel='a.nav-link[onclick*=\"showTab(\\\\''+_currentTab+'\\\\')\"]';
```

**Solución: concatenación de strings**

```javascript
// CORRECTO
var sel='a.nav-link[onclick*="showTab(' + "'" + _currentTab + "'" + ')"]';
```

**Regla general para JS en HTML:** si necesitas un apóstrofe/single-quote literal dentro de un string JS que está embebido en HTML, usa concatenación `"'"` o `"\\'"` (una sola barra), NUNCA `\\\\''`.

**Síntoma:** el browser muestra la estructura HTML (sidebar, título) pero "● cargando..." eternamente — el JS nunca se ejecutó. El parser encontró el SyntaxError en la primera pasada y abortó todo el script.

### PITFALL 2: Llamar funciones que no existen

`renderProjectsView()` llamaba a `activateView('projects')` — pero esa función no existía. Resultado: `ReferenceError` que silenciosamente mataba el render de la vista de proyectos (el div quedaba vacío sin error visible).

**Detección:** si una vista renderiza vacía (el div existe en el DOM pero no tiene contenido), revisar la consola del browser por `ReferenceError`. La función `showCurrentView()` ya maneja la activación del div — las funciones `render*View()` solo deben poblar el innerHTML, no activar/desactivar visibilidad.

**Patrón correcto en render*View():**
```javascript
function renderProjectsView(){
  // NO llamar activateView() — showCurrentView ya activó el div
  var active = PAGES.filter(function(p){return p.page_type==='project';});
  // ... build HTML ...
  document.getElementById('view-projects').innerHTML = h;
}
```

### PITFALL 4: Usar screencapture / AppleScript / Chrome local para capturar UI

**NUNCA usar herramientas del sistema OS para screenshots de la UI web.** Hermes tiene el browser tool nativo (`browser_navigate`, `browser_vision`, `browser_vision`) que puede capturar la UI directamente sin necesidad de abrir Chrome/Safari o usar AppleScript.

- `browser_vision` renderiza la página en un browser remoto y devuelve screenshot + descripción
- No requiere Chrome local, accesibilidad, permisos de pantalla, ni coordenadas de ventana
- No hay problemas de ventanas ocultas, profile pickers, o monitores múltiples
- Es la única manera confiable de capturar screenshots cuando el servidor corre en `localhost`

**Correcto:** `browser_vision(url="http://localhost:8899/", question="Show the kanban")`  
**Incorrecto:** `open -a Chrome`, `screencapture`, `osascript`, `python -c Quartz`

### PITFALL 5: Terminal heredoc/echo inyecta código corrupto en HTML

**NUNCA usar `terminal` con heredoc/echo para escribir CSS largo en HTML.** Las herramientas de terminal pueden corromper el contenido (se inyectan líneas como `CSSEOF && echo "Written"` dentro del archivo).

**Correcto:** Escribir a archivo temporal con `write_file` o `execute_code` (Python), luego inyectar vía `read_file` + `patch`.  
**Incorrecto:** `terminal` con `cat > file.css << 'CSSEOF'` — el delimitador del heredoc puede escapar y quedar dentro del archivo.

### PITFALL 6: Posición del night toggle en sidebar

El night toggle debe posicionarse al **final del sidebar** (después de los nav links, antes del status), no junto al título. Esto es preferencia UX.

**Correcto:**
```html
<div id="sidebar">
  <h2 class="sidebar-title">PocketBrain</h2>
  <select id="brain-selector">...</select>
  <input id="search" placeholder="Buscar...">
  <div id="nav">...</div>          <!-- links principales -->
  <div id="night-toggle" onclick="toggleNight()">🌙 Noche</div>  <!-- aquí -->
  <div id="status">● live</div>    <!-- footer -->
</div>
```

### PITFALL 7: Variables no definidas en JavaScript crashean silenciosamente tabs

Si una variable se refiere en `renderProjectView()` pero no se define (ej. `pfiles` que no existe en el array de datos), el script JS se detiene en ese punto y los tabs nunca se renderizan. Sin error visible en la consola (a menos que se abra DevTools). Siempre verificar que todas las variables de template existen antes de usarse en HTML/JS inline.

**Ejemplo del bug:**
```javascript
// renderProjectView() usaba `pfiles.length` pero `pfiles` nunca se declaró
// El JS crashea, la barra de tabs no aparece, la vista queda vacía silenciosamente
```

### PITFALL 8: `#view-graph.active` necesita `position:relative` para hijos absolutos

La leyenda del grafo (`#graph-legend`) usa `position:absolute;bottom:12px;right:12px`. El padre `#view-graph.active` DEBE tener `position:relative` para que la leyenda se ancle a él y no al `<body>`. Si falta:

- La leyenda puede aparecer en una esquina del viewport en vez del canvas.
- El canvas de vis.js (`#graph-view` con `position:absolute;top:0;left:0;right:0;bottom:0`) necesita un padre posicionado para calcular su altura.

**Fix:**
```css
#view-graph.active{display:flex;flex-direction:column;position:relative;max-width:none;padding:0;height:100%;animation:none}
```

### PITFALL 9: `_graphInit` bloquea re-render después de `loadAll()`

`renderGraph()` guarda `_graphInit=true` en la primera corrida para evitar recrear la red. Cuando `loadAll()` refresca los datos cada 30s, si `_graphInit` sigue en `true`, la leyenda no se regenera con los nuevos `GRAPH.counts`.

**Fix:** Resetear `_graphInit` al inicio de `loadAll`:
```javascript
function loadAll() {
    // ...
    _graphInit = false;  // permite re-render del grafo y leyenda
    // ...
}
```

**Síntoma:** la leyenda del grafo aparece vacía después del primer polling, o muestra counts desactualizados. El DOM existe (`#graph-legend.innerHTML === ''`).

### PITFALL 10: Cambios en `brain_web.py` requieren reiniciar el servidor; `web_ui.html` no

- `brain_web.py` se carga una vez al iniciar el proceso Python. Cualquier cambio en funciones de backend (`get_pages()`, `get_graph()`, etc.) requiere **matar y levantar el proceso** (`pkill -f brain_web.py; python3 brain_web.py`).
- `web_ui.html` se lee en cada request (`_load_html()`). Los cambios de CSS/JS/HTML se reflejan inmediatamente sin reinicio.

**Síntoma del error:** editas `get_graph()` para agregar `counts`, pero `curl http://localhost:8899/api/graph` sigue devolviendo solo `{nodes, edges}` sin `counts`. El server sigue corriendo con el código antiguo.

### PITFALL 11: H1 sin `margin-bottom` rompe consistencia visual

`.view-header h1` tiene `margin:0` y el `.view-header` maneja `margin-bottom:20px`. Pero cuando un `<h1>` se genera fuera de `.view-header` (wiki page detail, project detail), carece de margen inferior y el contenido queda pegado al título.

**Fix:** Agregar `style="margin-bottom:20px"` inline a los `<h1>` fuera de `.view-header`:
```javascript
// Wiki page detail
h+='<h1 style="margin-bottom:20px">'+p.title+'</h1>';

// Project detail
h+='<h1 style="margin-bottom:20px">'+p.title+'</h1>';
```

**Regla:** Siempre verificar que TODOS los H1 de la app tengan `margin-bottom:20px`, sea por el contenedor `.view-header` o por estilo inline.
