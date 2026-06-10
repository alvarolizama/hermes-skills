---
name: pocketbrain
description: "Wiki/cerebro de conocimiento multi-contexto sobre PocketBase — 12 colecciones, búsqueda rankeada, versionado, todos, goals, journal, reminders, deliverables, graph y servidor web live."
version: 2.9.3
author: Alvaro L.
platforms: [macos, linux]
metadata:
  hermes:
    tags: [wiki, knowledge-base, pocketbase, contexts, markdown]
    related_skills: [pocketbase, llm-wiki]
---

# PocketBrain — Segundo cerebro digital

Knowledge base multi-cerebro sobre PocketBase. Los agentes escriben, tú consultas.
Un servidor web live, 12 colecciones, todo conectado con trazabilidad completa.

## Novedades v2.9.0

- **UI refactor completo**: sidebar con iconos en todos los títulos (`📅`, `☐`, `🎯`, `⏰`, `📓`, `📚`, `◉`).
- **Goals con tabs internos**: listado con **Activos/Terminados/Cancelados** + paginación 50/50. Detalle con **Contenido/Tareas/Key Results/Progreso/Relación**.
- **Progreso automático**: calculado visualmente desde el estado de tareas (`backlog=0`, `in progress=50`, `done=100`).
- **Markdown renderer propio**: bold, italic, headers, lists, code blocks, `[[wikilinks]]`, links externos.
- **Toasts de notificación** en tiempo real al detectar cambios nuevos.
- **Footer de actividad reciente** (`brain_log`) en cada página, goal y proyecto.
- **Indicador live** verde con pulse animation en sidebar.
- **Paginación 50/50** también en Wiki (tabs por tipo de página).
- **Fixes de backend**: `get_goals()` ahora expande `page` y devuelve `page_slug` (antes devolvía ID, rompiendo el filtro de goals por proyecto en el frontend).
- **Fixes de frontend**: uso de `forEach + getAttribute + includes` en vez de `querySelector` con atributos que contienen comillas dinámicas. Typo `api('/de ps')` corregido a `api('/deps')`.
- **Nuevas vistas: Files y Deliverables** — listados independientes con filtro por proyecto (dropdown "Todos/Sin proyecto/Proyecto X"), igual que Todo, Goals y Reminders. Tabs Archivos y Entregables en detalle de cada proyecto.

### v2.9.1 (Refactor UI — Proyecto primera, Kanban full, markdown, Heroicons)
- **Proyecto como primera vista en sidebar** — "Proyectos" ahora es el primer ítem de navegación.
- **Vista de proyecto sin resumen/meta pills** — el primer tab es "Contenido" (renderiza markdown), eliminando el tab "Resumen" y las pills de status/goals/tasks que aparecían arriba de los tabs.
- **Sub-tabs de status en Goals** — tabs filtro "Todos | Activos | Terminados | Cancelados" tanto en la vista general de Goals como dentro de cada proyecto.
- **Kanban full-width/height** — dentro del tab Kanban de proyecto, el board ocupa `flex:1` y `min-height:0` para usar todo el espacio disponible.
- **Markdown renderer mejorado** — soporta bold, italic, listas ordenadas/desordenadas, links externo (`target="_blank"`), blockquotes, y escaping de HTML para evitar XSS.
- **Iconos Heroicons SVG inline** — reemplazo completo de emojis Unicode en sidebar y headers por SVG inline con paths de Heroicons 24 outline. Helper `icon(name, size)` en el JS.
- **Patrón de patching seguro** — documentado en `references/html-js-patching.md`: usar `execute_code` (Python) con `assert` para reemplazos masivos en `web_ui.html`, evitando `write_file` truncamientos y parches inconsistentes.

## Dependencia

Usa `pocketbase` skill → módulo `pb.py`. Variables en `~/.hermes/.env`:
`POCKETBRAIN_HOST`, `POCKETBRAIN_EMAIL`, `POCKETBRAIN_PASSWORD`. (independientes de POCKETBASE_*).

---

## Quick Start

```bash
# 1. Crear colecciones (una vez)
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 -c "from brain import _pocketbrain_pb, setup_contexts; setup_contexts(_pocketbrain_pb())"

# 2. Servidor web live
python3 brain_web.py --context personal
# → http://localhost:8080

# 3. Exportar a markdown
python3 sync.py --context personal --full
```

```python
# 4. Desde el agente
from brain import Brain
brain = Brain('personal')
brain.create_context(label='Contexto Personal')
brain.orient()
```

---

## Arquitectura

12 colecciones. Ver `references/schema.md` para detalle completo.

| Colección | Para |
|-----------|------|
| `contexts` | Contextos independientes (personal, projects, etc.) |
| `brain_pages` | Páginas markdown con `[[wikilinks]]` |
| `brain_todos` | Tareas (backlog → today → done) |
| `brain_goals` | Goals, milestones, OKRs con retrospectiva |
| `brain_reminders` | Recordatorios con fecha/hora |
| `brain_journal` | Diario (una entrada por día) |
| `brain_deliverables` | Entregables versionados |
| `brain_files` | Archivos adjuntos |
| `brain_tags`, `brain_domains` | Organización |
| `brain_page_versions` | Historial de cambios |
| `brain_log` | Bitácora con trazabilidad |

---

## ⚠️ Pitfalls

### CREATION_ORDER: las dependencias mandan

`setup_contexts()` crea las 12 colecciones en orden. Si una colección A tiene un campo relation a B, B debe crearse ANTES que A. El orden correcto es:

```
contexts → brain_domains → brain_tags → brain_pages → brain_goals
→ brain_todos → brain_journal → brain_files → brain_deliverables
→ brain_reminders → brain_log → brain_page_versions
```

**brain_goals va ANTES de brain_todos, brain_files y brain_deliverables** porque estos lo referencian con `goal`.

### SELF_REF_FIELDS: relaciones autoreferenciadas

`brain_goals` tiene campos `parent` y `goal` que apuntan a `brain_goals`. PocketBase rechaza crear una colección con campos relation a sí misma. La solución:

1. El campo se **quita** del schema antes de `create_collection()`.
2. Después de creada, se **agrega con PATCH** usando `update_collection()`.

Las colecciones con self-refs se declaran en `SELF_REF_FIELDS` (diccionario en `brain.py`). Si agregas una nueva colección autoreferenciada, declárala ahí.

### Naming: 'brain' en PocketBase ≠ 'brain' en el código

El campo relation en PocketBase se llama `brain` (por legado) pero la colección padre es `contexts`. No confundir:
- **Campo en PB**: `"brain"` (relation a `contexts`)
- **Variable en Python**: `context_name`, `_context_id`
- **Colección**: `contexts`

### Mass renames: verify EVERY reference

Cuando renombres una variable o colección en todo el código (ej. `brains` → `contexts`, `brain_name` → `context_name`), estas 4 clases de bugs son fáciles de pasar por alto:

1. **Assignment RHS**: `self.context_name = brain_name` — el lado derecho no se renombró.
2. **String constants**: `self.pb.create('brains', ...)` — strings con el nombre viejo de colección.
3. **Attribute access on external objects**: `brain.brain_name` en `graph.py` — la variable es `brain = Brain(...)` pero el atributo cambió a `.context_name`.
4. **Local variable in method body**: `brain.get('schema_config')` dentro de `orient()` — la variable local `brain` se renombró a `context` en la línea anterior pero esta referencia quedó sin actualizar.

**Verificación post-rename**: ejecuta el script y sigue el traceback. No confíes en que un grep rápido atrapó todo — los falsos negativos son comunes con nombres que aparecen como substring de otros identificadores (`brain` dentro de `brain_pages`, `Brain`).

### brain_web.py: usa ThreadingHTTPServer (NO HTTPServer)

El servidor web DEBE usar `ThreadingHTTPServer`. Con `HTTPServer` simple, el browser hace múltiples `fetch()` en paralelo y el servidor single-threaded solo atiende una a la vez — las demás reciben "Failed to fetch" y la UI muestra "● error".

```python
# CORRECTO
from http.server import ThreadingHTTPServer
server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)

# INCORRECTO — causa "Failed to fetch" en el browser
server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
```

### brain_web.py: cache de 30s para get_brain()

`get_brain()` cachea la instancia de `Brain` por contexto (dict `BN → Brain`). Esto evita re-autenticar en cada uno de los 8 `fetch()` paralelos que hace el browser al cargar. Sin cache: ~140ms por request (colapsan). Con cache: ~20ms por request después del primero. 

**IMPORTANTE:** usar dict por contexto (`_brain_cache[BN]`), NO cache global con timestamp. El cache global causaba que al cambiar de contexto en el selector (`personal` → `bravo`), la API devolviera datos del contexto anterior durante 30s.

### brain_web.py: HTML en archivo separado

Desde v2.0.0, el HTML/JS/CSS vive en `web_ui.html` (NO inline en brain_web.py). `_load_html()` lee el archivo cada request. Para mobile: `<span class="mobile-title">PocketBrain</span>` junto al hamburger, visible solo en `@media(max-width:768px)` con `display:block`.

### Browser tool vs screencapture

**NUNCA usar screencapture, open Chrome/Safari, o AppleScript para screenshots de UI web.** Hermes tiene un browser tool nativo (`browser_navigate`, `browser_vision`, `browser_vision`). Usar esas herramientas directamente:
- El browser remoto renderiza la página y captura screenshots nativamente
- No requiere Chrome local, AppleScript, ni permisos de accesibilidad
- No hay problemas de coordenadas negativas, ventanas ocultas, o profile pickers

**Correcto:** `browser_vision(url="http://localhost:8899/", question="Show the kanban board")`  
**Incorrecto:** `open -a Chrome`, `screencapture`, `osascript`

### brain_web.py: ejecutar SIEMPRE desde el directorio scripts/

`brain_web.py` lee `web_ui.html` con un path relativo (`open('web_ui.html')`). Si se levanta desde el home o cualquier otro directorio, falla inmediatamente:

```bash
# CORRECTO
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 brain_web.py --port 8899 --context personal

# INCORRECTO — "No such file or directory: '/Users/alvaro/brain_web.py'"
cd ~ && python3 brain_web.py --port 8899 --context personal
```

### web_ui.html: SPA tabs `<a>` sin `href` = page reload

En una SPA donde todos los tabs son `<a>` generados por JS, **cada tag `<a>` debe tener `href="#"` y `onclick="...; return false;"`**. Si no tiene `href`, el browser interpreta el click como navegación a la URL actual, causando un reload completo que rompe la tab view y se queda en la misma página o en blanco.

**Ejemplo correcto:**
```javascript
h += '<a href="#" onclick="switchGoalTab(\'content\',\''+g.id+'\'); return false;">Contenido</a>';
```

**Regla:** al generar tabs dinámicos en `web_ui.html`, siempre agregar `href="#"` y `return false;` al final del `onclick`. Esto aplica a `Views.goals`, `Views.goal`, `Views.project`, `wiki_showPage`, `switchPageTab`, `switchPageTab2`, y cualquier otro tab generado por `project-tabs`.

### web_ui.html: variable mixing en filtros de views

Al generar el HTML con strings concatenadas, es muy fácil copiar-pegar el `<select>` de una view (ej. Todo) a otra (ej. Goals) y dejar la función `onchange` y las variables de la view anterior. El resultado: el select no cambia nada porque setea `_todoFilter` en lugar de `_goalFilter`.

**Ejemplo de bug (copy-paste de Todo a Goals):**
```javascript
// VIEJO — roto: llama a setTodoFilter y referencia _todoFilter
var h = '<select onchange="setTodoFilter(this.value)">...' + (_todoFilter==='' ? ' selected' : '') + ...

// CORRECTO — setGoalStatus y _goalFilter
var h = '<select onchange="setGoalStatus(this.value)">...' + (_goalFilter==='' ? ' selected' : '') + ...
```

**Regla:** al modificar un `<select>` de filtro, verificar que la función `onchange`, la variable del estado, y el título `<h1>` coincidan con la vista actual. No confiar en el copiar-pegar.

### web_ui.html: JS quotes in strings generating HTML — systematic escaping

When `web_ui.html` generates HTML strings inside JavaScript (e.g. `h+='<div><a href="#" onclick="setProjGoalStatus('all')">...</a></div>'`), the single quotes inside `onclick` attributes break the surrounding JS string. This causes a **SyntaxError** that kills the entire parser, leaving the app stuck at "Cargando...".

**The root issue** is a pattern: `setXxxStatus('...')` inside HTML strings that are themselves inside single-quoted JS strings. This also affects variable assignments: `_reminderStatusTab='today'` inside an `onclick` attribute.

**Bulk fix with regex** (Python):
```python
import re

with open('web_ui.html','r') as f:
    content = f.read()

# 1. Fix setXxxStatus('arg') -> setXxxStatus(\\'arg\\')
content, c1 = re.subn(
    r"(set[A-Za-z]+Status)\('([^']+)'\)",
    lambda m: m.group(1) + "(\\'" + m.group(2) + "\\')",
    content
)

# 2. Fix variable assignments: _var='value' inside onclick strings
# Pattern: ;varName='value'; → ;varName=\\'value\\';
content, c2 = re.subn(
    r"(;\w+=)('[^']+');",
    lambda m: m.group(1) + "\\'" + m.group(2)[1:-1] + "\\';",
    content
)

with open('web_ui.html','w') as f:
    f.write(content)
```

After mass-escaping, always run `node --check` to verify. If the regex misses a case, the error will surface in a different line (the **consequence**, not the **cause**). Look at the line *before* the reported error line — the unescaped quote is usually two lines earlier in a concatenated string.

### web_ui.html: Graph blank canvas — nodes positioned off-screen before fit()

vis.js may position nodes far from the viewport before `fit()` is called. If `fit()` runs before the `afterDrawing` stabilization event, the graph is blank even though `GRAPH` has 79 nodes and 37 edges. The nodes are rendered but outside the visible area (e.g. y=-430).

**Fix for general graph**: call `fit()` both immediately AND in `afterDrawing`:
```javascript
window._net = new vis.Network(...);
if(window._net){
  window._net.once('afterDrawing', function(){ window._net.fit(); });
  window._net.fit();
}
```

**Fix for project graph**: assign the network instance to a variable and call `fit()`:
```javascript
var pnet = new vis.Network(container, {nodes: nds, edges: eds}, options);
if(pnet) pnet.fit();
```


```css
/* CORRECTO */
#view-graph.active{display:flex;flex-direction:column;position:relative;max-width:none;padding:0;height:100%;animation:none}

/* INCORRECTO — falta position:relative, graph-view no tiene altura */
#view-graph.active{display:flex;flex-direction:column;max-width:none;padding:0;height:100%;animation:none}
```

### web_ui.html: display:none perdido al cambiar max-width o padding

La línea CSS del selector principal `#main>div` tiene DOS propiedades críticas: `display:none` (para ocultar vistas inactivas) y `max-width:900px` (el ancho del contenido). Si haces un parche que reemplaza la línea completa para quitar `max-width` o cambiar padding, **el `display:none` se pierde si no se incluye explícitamente en el replacement**.

**Síntoma:** Todas las vistas se renderizan al mismo tiempo, unas encima de otras. El snapshot del browser muestra el Todo kanban Y el Wiki al mismo tiempo. La app parece desordenada pero sin errores JS.

**Bug:**
```css
/* Correcto */
#main>div{display:none;padding:40px 60px;max-width:900px}

/* Al cambiar max-width a none, si no pones display:none, se pierde: */
#main>div{padding:40px 60px;max-width:none}  /* ← display:none DESAPARECIDO, TODA LA APP ROTA */
```

**Fix:** Siempre preservar `display:none` al parchear el selector de CSS. Usar `patch` con `old_string` que incluya toda la línea original, no solo la parte que cambia.

**Regla:** Al hacer `replace` del `#main>div` CSS, el `new_string` debe incluir `display:none` explícitamente:
```css
#main>div{display:none;padding:40px 60px;max-width:none}
```

El icono Unicode `&#9745;` (☐ “Ballot Box with Check”) es ambiguo en algunos sistemas. Usar `&#10003;` (✓ “Check Mark”) para consistencia visual.

```javascript
h+='<span class="nav-icon">&#10003;</span>Todo</a>';  // sidebar y view-header
```

### web_ui.html: quitar meta pills de wiki_showPage

En la página de detalle de una wiki page (`wiki_showPage`), los pills de metadatos (page_type, goals count, tareas count, backlinks) arriba de los tabs distraían y ocupaban espacio. La solución es **no inyectar el div de `.meta` antes de los tabs**; la información se muestra ya en el tab “Relacionado” o en los breadcrumbs (`Wiki · concept`).

### web_ui.html: validación antes de deploy (node --check)

**Regla de oro:** `node --check` en el JS extraído de `web_ui.html` antes de levantar el servidor. Un typo como `api('/de ps')` (espacio en la API) da un 404 silencioso y la app queda en blanco con "loading" infinito.

```bash
# Extraer solo el JS inline para verificar
python3 -c "import re; h=open('web_ui.html').read(); js=re.split(r'</script>', re.split(r'<script>', h)[1])[0]; open('/tmp/pb.js','w').write(js); print('ok')"
node --check /tmp/pb.js
# Si pasa limpio, es safe deploy. Si no, no hay que buscar más.
```

### web_ui.html: JS pitfalls en web_ui.html

Ver `references/web-ui.md` y `references/web-ui-patterns.md` para arquitectura y pitfalls.

- **Escape de comillas en JS inline**: `\\\\\\\\''` rompe el parser → toda la app en blanco. Usar concatenación de strings en lugar de escapes: `var sel = 'a.nav-link[onclick*="showTab(' + "'" + _currentTab + "'" + ')"]'`
- **Funciones faltantes**: si el código llama a `activateView()` pero la función se perdió (ej. en un rebase), no hay `ReferenceError` visible en el snapshot — la app simplemente se queda en blanco. Verificar `function activateView` exista en el HTML.
- **Filtro por contexto**: cada contexto tiene sus propios proyectos. Un proyecto en `personal` no aparece en el dropdown de `projects`. La UI no es cross-context.
- **Tabs en proyecto/página**: `switchProjectTab()` y `switchPageTab()` renderizan bajo demanda. Usan `window._projectData` y `window._pageData` como caché. El Graph del proyecto usa vis.js con barnesHut, nodo central del proyecto + goals + tareas + reminders como satélites.
- **querySelector con `[onclick*='...']` es quebradizo**: el intento de `document.querySelector('a.nav-link[onclick*=..."showTab(...)"...]')` es imposible de escapar correctamente entre HTML+JS. Resultado: SyntaxError en el browser.  
  **Solución:** Usar `forEach` + `getAttribute` + `includes`:
  ```javascript
document.querySelectorAll('a.nav-link').forEach(function(a){
  if(a.getAttribute('onclick') && a.getAttribute('onclick').includes('showTab(' + "'" + _currentTab + "'" + ')'))
    a.classList.add('active');
  });
  ```
- **loadAll: typo en string de API = app rota**: `Promise.all([... api('/de ps') ...])` tiene un espacio en el path → `404` que no se muestra al usuario, solo se queda en loading. Los 9 paths son `pages`, `goals`, `todos`, `deps`, `files`, `reminders`, `journal`, `graph`, `logs`.

- **Archivos: `pfiles` usado antes de declarar** (`var pfiles = ...`) en `renderProjectView` crasheaba JS silenciosamente, dejando tabs vacíos. Siempre declarar todas las variables antes de usarse en el HTML/JS template.
- **Desktop**: `.kanban{display:flex;gap:8px;flex-wrap:wrap}` + `.kanban-col{flex:1 1 0;min-width:140px}` — columnas se distribuyen, hace wrap si no caben.
- **Mobile**: las columnas se apilan verticalmente con `.kanban: flex-direction: column` y `.kanban-col: flex: 1 1 auto`.
- **NO usar** `overflow-x: auto` con `flex-wrap: wrap` — son mutuamente excluyentes. `overflow-x: auto` fuerza scroll horizontal que rompe el layout responsive.

### Query parameters: brain → context

Toda la interfaz web usa `?context=personal` (no `?brain=personal`). El endpoint es `GET /api/contexts` (no `/api/brains`). La variable JS es `currentContext` (no `currentBrain`). Mantener consistencia end-to-end: CLI `--context`, query params `?context`, JS `currentContext`, endpoint `/api/contexts`.

### web_ui.html: variables JS sin declarar

El `renderProjectView` de `web_ui.html` referenció `pfiles` en el template pero no la declaró (`var pfiles = ...`). Resultado: JavaScript crashea en silencio, la vista del proyecto se queda en blanco, y los tabs no se renderizan. **Verificación:** antes de deploy, revisar que toda variable usada en `innerHTML` esté declarada en el scope. El browser muestra "blank page" sin error visible.

### backend: `create_goal` y `_get_page` pueden devolver error-dict sin `id`

`Brain.create_goal` llama `self._get_page(project_slug)` y si la página no existe (o el slug es incorrecto), el resultado puede ser un dict de error o un dict vacío. Luego hace `project['id']` lanzando `KeyError: 'id'` sin mensaje claro.

**Fix**: verificar que `project` es dict y tiene 'id' antes de usarlo:
```python
project = self._get_page(project_slug)
if project and 'id' in project:
    data['page'] = project['id']
```

Lo mismo aplica a `journal_write` y `_journal_date`: si la entrada no existe, `_get_page` puede devolver un error-dict. El método `journal_write` usa `date_val` (no `date`) como argumento, pero los scripts clientes a veces pasan `date=`. Si pasas `date` como keyword a `journal_write`, lanzará `TypeError: unexpected keyword argument 'date'`.

**Fix**: usar `date_val` consistentemente en el cliente:
```python
brain.journal_write(body, date_val='2026-06-15')  # correcto
brain.journal_write(body, date='2026-06-15')     # TypeError
```

### backend-frontend contract: goals `page` field es ID, no slug

`brain_web.py` → `get_goals()` usa `brain.pb.all("brain_goals", ...)` sin `expand="page"`. Por lo tanto, `g.page` devuelve el **ID interno** de la página (ej. `ww76mtkpqss4j7q`), NO el slug legible (`viaje-a-japon-2026`).

El frontend `web_ui.html` filtra goals por proyecto usando `g.page === p.slug` (string comparison). Esto siempre falla porque compara ID con slug → **0 goals en todas las tarjetas de proyecto**.

**Fix en backend** (`brain_web.py`): agregar `expand="page"` y devolver `page_slug` en la respuesta:
```python
def get_goals():
    goals = brain.pb.all("brain_goals", filter="(brain='...')", expand="page")
    return [{...
        "page": g.get("page","") or "",
        "page_slug": (g.get("expand",{}).get("page",{}) or {}).get("slug","") or "",
        ...} for g in goals]
```

**Fix en frontend** (`web_ui.html`): usar `g.page_slug` (no `g.page`) en todos los lugares donde se filtra por proyecto:
```javascript
// Project card stats
var pgoals = GOALS.filter(function(g){return g.page_slug===p.slug;}).length;
// Goal filter dropdown
filtered = GOALS.filter(function(g){return g.page_slug===_goalFilter;});
// Wiki page detail
var pgoals = GOALS.filter(function(g){return g.page_slug===slug;});
// Project detail view
var pgoals = GOALS.filter(function(g){return g.page_slug===slug;});
```

**Verificación**: después del fix, recargar la página y verificar que las tarjetas de proyecto muestran contadores correctos (ej: "5 goals · 6 tareas"). Si sigue en 0, el problema persiste en el contracto.


`Brain.create_goal` llama `self._get_page(project_slug)` y si la página no existe (o el slug es incorrecto), el resultado puede ser un dict de error o un dict vacío. Luego hace `project['id']` lanzando `KeyError: 'id'` sin mensaje claro.

**Fix**: verificar que `project` es dict y tiene 'id' antes de usarlo:
```python
project = self._get_page(project_slug)
if project and 'id' in project:
    data['page'] = project['id']
```

Lo mismo aplica a `journal_write` y `_journal_date`: si la entrada no existe, `_get_page` puede devolver un error-dict. El método `journal_write` usa `date_val` (no `date`) como argumento, pero los scripts clientes a veces pasan `date=`. Si pasas `date` como keyword a `journal_write`, lanzará `TypeError: unexpected keyword argument 'date'`.

**Fix**: usar `date_val` consistentemente en el cliente:
```python
brain.journal_write(body, date_val='2026-06-15')  # correcto
brain.journal_write(body, date='2026-06-15')     # TypeError
```


`Brain.create_goal` llama `self._get_page(project_slug)` y si la página no existe (o el slug es incorrecto), el resultado puede ser un dict de error o un dict vacío. Luego hace `project['id']` lanzando `KeyError: 'id'` sin mensaje claro.

**Fix**: verificar que `project` es dict y tiene 'id' antes de usarlo:
```python
project = self._get_page(project_slug)
if project and 'id' in project:
    data['page'] = project['id']
```

Lo mismo aplica a `journal_write` y `_journal_date`: si la entrada no existe, `_get_page` puede devolver un error-dict. El método `journal_write` usa `date_val` (no `date`) como argumento, pero los scripts clientes a veces pasan `date=`. Si pasas `date` como keyword a `journal_write`, lanzará `TypeError: unexpected keyword argument 'date'`.

**Fix**: usar `date_val` consistentemente en el cliente:
```python
brain.journal_write(body, date_val='2026-06-15')  # correcto
brain.journal_write(body, date='2026-06-15')     # TypeError
```

### web_ui.html: querySelector con comillas escapadas = SyntaxError

Intentar usar `document.querySelector('a.nav-link[onclick*=\'showTab(...)\']')` en JS inline dentro de HTML es imposible de escapar correctamente. Resultado: `SyntaxError` en `node --check` o blank page en el browser.

**Fix**: usar `querySelectorAll` + `forEach` + `getAttribute` + `includes`:
```javascript
document.querySelectorAll('a.nav-link').forEach(function(a){
  if (a.getAttribute('onclick') && a.getAttribute('onclick').includes('showTab(' + "'" + _currentTab + "'" + ')')) 
    a.classList.add('active');
});
```
**Regla:** Nunca usar `querySelector` con atributos que contienen comillas dinámicas. Usar `forEach + getAttribute + includes`.

### web_ui.html: write_file trunca archivos grandes (>~9KB)

Además de destruir archivos con contenido accidental, `write_file` puede **truncar silenciosamente** archivos de texto que superen ~9,000 bytes. El resultado es un archivo plan o un `web_ui.html` incompleto: `node --check` pasa en la mitad del JS que quedó, pero el browser carga HTML faltante, funciones que no existen, y la app queda en blanco sin traceback visible.

**Síntoma:** después de `write_file`, `wc -c` muestra 9,445 bytes en vez de los ~50,000 esperados del archivo original. El browser muestra loading infinito o UI incompleta.

**Fix / Verificación:**
```bash
# Después de toda escritura >5KB, verificar tamaño
wc -l ~/.hermes/skills/productivity/pocketbrain/scripts/web_ui.html
wc -c /Users/alvaro/.hermes/plans/2026-06-10_PocketBrain-WebUI-Refactor.md
# Si está truncado, reescribir completo o usar execute_code con open().write() para strings grandes
```

**Regla:** cuando un archivo es >5KB, después de `write_file`, hacer `wc -c` para verificar que se escribió completo. Si truncado, reescribir usando `execute_code` con `open(path,'w').write(content)` (el Python runtime no tiene límite de tamaño de Hermes). Luego volver a verificar `wc -c`.

---

### web_ui.html: comillas simples en JS inline generando HTML — SyntaxError sistémico

El generador de HTML dentro de strings JS en `web_ui.html` usa comillas simples para el string JS: `h+='<div ... onclick="...">...</div>'`. Pero dentro del HTML generado hay funciones que reciben strings con comillas simples: `setProjGoalStatus('all')`, `setProjReminderStatus('today')`, y asignaciones como `_reminderStatusTab='today'`. Estas comillas simples chocan con el delimitador del string JS, rompiendo todo el parser y dejando la app en "Cargando..." infinito.

**Síntoma:** `node --check` reporta `SyntaxError: Unexpected identifier 'all'` o similar. La app se queda en loading, el sidebar no aparece.

**Fix:** Escapar las comillas simples dentro del HTML generado: `setProjGoalStatus(\'all\')`, `_reminderStatusTab=\'today\'`. Esto aplica a TODO el generador de tabs de filtros en project views (`setProjGoalStatus`, `setProjReminderStatus`) y cualquier otra función que reciba string literals en el HTML generado por JS.

**Fix automatizado:**
```python
import re

def escape_quote(match):
    func = match.group(1)
    arg = match.group(2)
    return func + "(\\'" + arg + "\\')"

new_content, count = re.subn(
    r"(set[A-Za-z]+Status)\('([^']+)'\)",
    escape_quote,
    content
)

# También asignaciones de variables: _var='value' en onclick
content = re.sub(
    r"(;\w+=)('[^']+');",
    lambda m: m.group(1) + "\\'" + m.group(2)[1:-1] + "\\';",
    content
)
```

**Regla:** después de hacer parches grandes a `web_ui.html` con generación de HTML en JS, correr `node --check` sobre el JS extraído. Si el error es `Unexpected identifier` en una línea con comillas simples, buscar el patrón sistémico de string literals no escapadas en la generación de HTML. No es un typo único — es un bug de patrón que afecta múltiples funciones.

### web_ui.html: JS string literals con errores tipográficos en concatenados (`backlog'` / `noproject?`)

Cuando se generan strings HTML con concatenación de JS, una comilla o un signo de puntuación desaparecido rompe el JS inline sin que `node --check` lo detecte si el error está en una porción no verificada. Ejemplos reales detectados:

1. **Comilla simple faltante:** `var s=t.status||backlog';` → `'backlog'` (la comilla inicial del string literal se perdió en el copy-paste).
2. **Signo de interrogación dentro del string literal:** `(_reminderFilter==='noproject?' selected':''')` → `(_reminderFilter==='noproject'?' selected':'`)`.

**Fix:** `node --check` los captura como `SyntaxError: Unexpected identifier 'selected'` o similar. **Síntoma:** el error aparece en `node --check` en el archivo `/tmp/pb_check.js`, pero la línea reportada puede estar en medio del string concatenado, no al inicio del error real. Leer el error con cuidado: el `Unexpected identifier` suele ser la **consecuencia**, no la **causa**. Buscar la comilla o el signo de puntuación que abrió mal el string dos líneas arriba.

**Regla:** después de hacer parches grandes a `web_ui.html` con `patch` (especialmente en strings concatenados de JS), correr `node --check` y revisar la línea *anterior* a la que reporta el error si la línea indicada parece válida.

**NUNCA usar `write_file` con `path=web_ui.html` para mensajes de prueba, notas temporales, o verificaciones.** `write_file` sobreescribe el archivo COMPLETO sin advertencia. Un error como escribir `curl está vacío, checando archivo.` sobre el archivo de ~45KB de JavaScript lo convierte en 37 bytes, destruyendo toda la UI.

**Archivos largos también pueden truncarse:** si `write_file` recibe un contenido muy grande y el resultado tiene `wc -c` o `wc -l` menor de lo esperado, el archivo se truncó silenciosamente. Verificar siempre con `wc -l` o `wc -c` después de escrituras mayores a 5KB. Corregir con `patch` si es parcial, o reescribir completo si el truncamiento es catastrófico.

**Síntoma:** `wc -c` muestra 37 bytes en vez de ~45000. `curl http://localhost:8899/` devuelve HTML vacío o incompleto. El browser muestra página blanca. La app no carga funciones ni datos.

**Recuperación inmediata:** El usuario tiene un repo personal con copia limpiega:
```bash
cp ~/Repos/personal/hermes-skills/pocketbrain/scripts/web_ui.html \
   ~/.hermes/skills/productivity/pocketbrain/scripts/web_ui.html
```

**Regla:** Usar `write_file` SOLO cuando ya tienes el contenido COMPLETO y final del archivo (template scaffold, nuevo archivo). Para parches o pruebas, usar `read_file` + `execute_code` (Python) o `patch` con `old_string`/`new_string` (con precaución de backslash-n, usar `replace_all` si aplica). **Nunca usar `write_file` como bloc de notas temporal.**

### Sidebar: Proyectos al inicio del menú

El sidebar debe listar **📁 Proyectos** como primer ítem de navegación (antes de Todo, Goals, etc.), ya que es el entry point principal al flujo de trabajo. Luego el resto: Todo, Goals, Reminders, Journal, Wiki, Graph.

### Mobile: cerrar sidebar al navegar

En mobile, al hacer click en cualquier opción del menú (`showTab`, `showProject`, `showPage`), el sidebar debe cerrarse automáticamente. Agregar `closeSidebar()` que detecte `window.innerWidth <= 768` y llame `document.getElementById('sidebar').classList.remove('open')`.

---

### web_ui.html: análisis completo antes de modificar

El usuario puede solicitar explícitamente que se **analice el código antes de tocarlo**. Antes de modificar `web_ui.html` (CSS, JS, o HTML inline), **leer el archivo completo** y entender:
- Estructura CSS y los selectores que se afectarán
- Los renders de cada vista (qué funciones generan HTML, qué variables JS usan)
- El orden de pestañas y el manejo de estado
- Los `onchange` y `onclick` que pueden romperse si el copy-paste no se ajusta

**Pitfall:** parchear a ciegas sin leer los ~500-600 líneas del archivo produce desalineamientos, funciones que hacen referencia a variables no declaradas, y bugs silenciosos. La regla es: leer, analizar, presentar, esperar aprobación. No escribir hasta confirmar el plan.

---

### Tab counts: conteos en TODOS los tabs de filtrado y navegación

Cualquier vista que tenga tabs de categoría o filtrado debe mostrar el conteo de elementos en cada tab. No solo el sidebar: también los tabs de contenido principal (Goals, Wiki, Reminders, project detail, wiki page detail).

**Pitfall: key mismatch en dict de counts** — al generar un objeto `counts` para iterar sobre tabs, las keys deben coincidir EXACTAMENTE con el identificador del tab (`t.k`), no con el label (`t.l`):
```js
// BUG: dict keys en español, tab keys en inglés
var counts = { todos: PAGES.length, proyectos: byType['project'], ... };
// tabs: [{k:'all', l:'Todos'}, {k:'project', l:'Proyectos'}, ...]
// counts[t.k] → undefined para 'all', 'project' → "Todos (undefined)"

// FIX: keys del dict = keys del tab array
var counts = { all: PAGES.length, project: byType['project'], ... };
```

### Carácter Unicode U+2019 (’) en archivos de código

El `patch` tool o copiar-pegar desde chat pueden introducir U+2019 (Right Single Quotation Mark) en lugar de la apóstrofo ASCII U+0027. Visualmente son idénticos pero el parser JS falla con `SyntaxError: Invalid or unexpected token`.

**Fix:** Si `node --check` falla en una línea con comillas aparentemente correctas, buscar U+2019:
```python
with open('web_ui.html', 'rb') as f:
    data = f.read()
    if b'\xe2\x80\x99' in data:  # U+2019 encoded as UTF-8
        print('Found at', data.index(b'\xe2\x80\x99'))
```
**Prevention:** No escribir apóstrofos en `new_string` del patch si puede evitarse. Preferir dobles comillas o concatenación.

---

### Re-seeding de datos de demo: limpiar duplicados antes

Si se llenan datos densos de demo sobre una base que ya tiene registros previos, **pages y goals duplicados** rompen los contadores del frontend (tarjetas de proyecto muestran más de la cuenta, dropdowns duplicados). Antes de re-seed:

1. **Limpieza total** (si el contexto es de prueba): `nuke_context(..., confirm='YES_DELETE_ALL')`.
2. **Deduplicación selectiva**: listar goals/pages por contexto, agrupar por `title` (o `slug` para pages), y borrar los duplicados. Si el goal tenía tareas/reminders vinculados, estos quedan "huérfanos" (page/goal ID inexistente). Post-deduplicación: verificar `brain_todos` y `brain_reminders` para borrar referencias rotas.

**Pitfall común**: crear goals con `title` repetido para el mismo proyecto genera duplicados que hacen que los contadores y filtros se vean mal. Si el frontend muestra "X goals" pero parecen más, o el dropdown de filtros tiene entradas duplicadas, revisar el backend por duplicados.

---

## Scripts

| Script | Uso |
|--------|-----|
| `brain_web.py` | Servidor web live en `localhost:8080`. Lee HTML de `web_ui.html`. |
| `brain.py` | Cliente Python para agentes |
| `sync.py` | Export a markdown local con frontmatter YAML |
| `graph.py` | Graph HTML standalone per-contexto |
| `web_ui.html` | Frontend: HTML+CSS+JS del servidor web |
| `validate_ui.py` | Validador JS de `web_ui.html` + auto-fix de comillas (`node --check`) |

### Web UI

La interfaz web está en `web_ui.html` (archivo separado desde v2.0.0).
Ver `references/web-ui.md` para arquitectura completa (sidebar, vistas, mobile, debugging).

---

## Trazabilidad

Cada operación registra quién (agente) y para quién (usuario).
Ver `references/tracing.md`.

```python
brain = Brain('personal')
# Toda acción → brain_log.details: {agent, requested_by}
```

---

## Clean / Reset

```python
from brain import nuke_context, _pocketbrain_pb
pb = _pocketbrain_pb()

# Limpiar un contexto (requiere confirmación explícita)
stats = nuke_context(pb, context_name='personal', confirm='YES_DELETE_ALL')
# → {brain_log: 66, brain_todos: 11, brain_pages: 9, brain_goals: 8, ...}

# Limpiar TODA la base de datos
nuke_context(pb, confirm='YES_DELETE_ALL')
# → borra todo, incluyendo contexts
```

- Orden seguro: dependencias primero (hijos antes que padres)
- Sin `confirm='YES_DELETE_ALL'` → lanza `ValueError`
- `context_name=None` → limpia todo

---

## Operaciones principales

```python
# Conocimiento
brain.create_page("Tema", body="## Ideas\n...", page_type="concept")
brain.search("machine learning")     # case-insensitive, rankeado
brain.append_to_page("mantrams", "- Nuevo", heading="2026-06-10")

# Tareas
brain.create_todo("Revisar PR", domain="bravo")
brain.todos(status="today")
brain.move_todo(id, "done")

# Goals (ver references/goals.md)
brain.create_goal("Lanzar MVP", type="milestone", deadline="2026-09-30")
brain.complete_goal(id, retrospective="Entregado a tiempo.")
brain.get_goal_tree()

# Proyectos
brain.create_page("App Móvil", page_type="project")
brain.create_deliverable("app-movil", file, title="Specs", version="v1")

# Diario
brain.journal_write("## Hoy\n- Avancé en [[proyecto-x]]", mood="great")

# Recordatorios
brain.create_reminder("Reunión", date="2026-06-15", time="10:00")
brain.reminders(date="today")

# Auditoría
brain.lint()           # huérfanos, broken links
brain.index()          # catálogo
brain.recent_logs(20)  # trazabilidad
```

---

## Referencias

Carga cada referencia solo cuando la necesites:

```python
# Schema completo de las 12 colecciones
skill_view('pocketbrain', file_path='references/schema.md')

# Trazabilidad: quién hizo qué
skill_view('pocketbrain', file_path='references/tracing.md')

# Goals, milestones, OKRs y retrospectivas
skill_view('pocketbrain', file_path='references/goals.md')

# Flujos de trabajo diarios y semanales
skill_view('pocketbrain', file_path='references/workflows.md')

# Arquitectura de variables de entorno (POCKETBRAIN_* vs POCKETBASE_*)
skill_view('pocketbrain', file_path='references/env-architecture.md')
```

| Archivo | Cuándo cargarlo |
|---------|-----------------|
| `references/schema.md` | Al crear/modificar colecciones o debugear campos |
| `references/tracing.md` | Al revisar logs o configurar un nuevo perfil |
| `references/goals.md` | Al trabajar con goals, milestones u OKRs |
| `references/workflows.md` | Al iniciar una sesión de trabajo |
| `references/env-architecture.md` | Al configurar credenciales o debuguear conexión |
| `references/web-ui.md` | Al trabajar en la interfaz web (sidebar, vistas, mobile, JS pitfalls) |
| `references/web-ui-debugging.md` | Al debuguear JS runtime: validación con `node --check`, browser tools |
| `references/html-js-patching.md` | Antes de modificar JS inline en `web_ui.html` — pitfalls de `patch` con escaped quotes, usar Python + `node --check` |
| `references/web-ui-patterns.md` | Al hacer refactor del frontend: arquitectura modular, tabs, progreso auto, toasts, markdown renderer |
| `references/design-systems.md` | Al aplicar o modificar el diseño visual (Apple Design System, tokens, dark mode) |
| `references/cli-migration.md` | Al hacer mass rename de variables/colecciones, o al vincular datos a proyectos |
| `references/rename-checklist.md` | Antes y después de cualquier mass rename en el código |
| `references/frontend-icon-patterns.md` | Al reemplazar emojis/Unicode por iconos SVG inline (Heroicons) en el frontend |
| `references/web-ui-js-escaping.md` | Al debuguear SyntaxError en web_ui.html: escaping de comillas simples en strings JS generadores de HTML |
| `references/backend-frontend-contract.md` | Al debuggear por qué contadores (goals, tareas) aparecen en 0 en las tarjetas de proyecto a pesar de que los datos existen |
