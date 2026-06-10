---
name: pocketbrain
description: "Wiki/cerebro de conocimiento multi-contexto sobre PocketBase — 12 colecciones, búsqueda rankeada, versionado, todos, goals, journal, reminders, deliverables, graph y servidor web live."
version: 2.2.0
author: Alvaro L.
platforms: [macos, linux]
metadata:
  hermes:
    tags: [wiki, knowledge-base, pocketbase, contexts, markdown]
    category: productivity
    related_skills: [pocketbase, llm-wiki]
---

# PocketBrain — Segundo cerebro digital

Knowledge base multi-cerebro sobre PocketBase. Los agentes escriben, tú consultas.
Un servidor web live, 12 colecciones, todo conectado con trazabilidad completa.

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

### brain_web.py: JS pitfalls en web_ui.html

Ver `references/web-ui.md` para pitfalls críticos:
- **Escape de comillas en JS inline**: `\\\\\\\\''` rompe el parser → toda la app en blanco.
- **Funciones inexistentes**: llamar `activateView()` (que no existe) → `ReferenceError` silencioso.
- **Filtro por contexto**: cada contexto tiene sus propios proyectos. No esperar cross-context.
- **Tabs en proyecto/página**: `switchProjectTab()` y `switchPageTab()` renderizan bajo demanda. Usan `window._projectData` y `window._pageData` como caché. El Graph del proyecto usa vis.js con barnesHut, nodo central del proyecto + goals + tareas + reminders como satélites.

---

## Scripts

| Script | Uso |
|--------|-----|
| `brain_web.py` | Servidor web live en `localhost:8080`. Lee HTML de `web_ui.html`. |
| `brain.py` | Cliente Python para agentes |
| `sync.py` | Export a markdown local con frontmatter YAML |
| `graph.py` | Graph HTML standalone per-contexto |
| `web_ui.html` | Frontend: HTML+CSS+JS del servidor web |

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
| `references/rename-checklist.md` | Antes y después de cualquier mass rename en el código |
