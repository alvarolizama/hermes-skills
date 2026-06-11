# PocketBrain

Un segundo cerebro digital multi-contexto. Backend en PocketBase (12 colecciones), servidor web live, y un cliente Python para que los agentes de IA escriban conocimiento, gestionen tareas y proyectos.

Los agentes guardan. Tú consultas.

## Screenshots

### Proyectos
Vista principal con tarjetas de proyecto, sidebar de navegación por tipo, y conteos.

![Proyectos](../assets/screenshot-projects.png)

### Goals
Goals filtrables por estado: activos, terminados, cancelados. Con filtro de proyecto.

![Goals](../assets/screenshot-goals.png)

### Grafo de Conocimiento
Visualización de nodos (páginas, goals, tareas, recordatorios) y sus relaciones via vis.js.

![Graph](../assets/screenshot-graph.png)

---

## Features

- **16 page types**: entity, concept, comparison, query, raw, project, plan, note, idea, todo, goal, milestone, okr, reminder, journal, file, deliverable
- **Auto-linking**: `[[wikilinks]]` en el body resuelven slugs existentes y generan backlinks automáticos
- **Auto-suggest page_type**: el agente infiere el tipo de página del título y contenido
- **Interactive graph**: grafos con vis.js, nodos coloreados por tipo, filtros por leyenda
- **Project management**: proyectos con goals, milestones, todos kanban, reminders, journal
- **Hash-based URLs**: toda navegación genera URLs compartibles
- **Live status**: heartbeat polling con indicador live/offline
- **Multi-contexto**: 5 contextos (personal, projects, bravo, learning, health)

---

## Dependencia

Requiere el skill `pocketbase` → módulo `pb.py`. Las credenciales se cargan del archivo `~/.hermes/.env`:

```bash
POCKETBRAIN_HOST=http://localhost:8090
POCKETBRAIN_EMAIL=admin@example.com
POCKETBRAIN_PASSWORD=***
```

Independientes de las variables `POCKETBASE_*`.

---

## Quick Start

```bash
# 1. Crear colecciones (una vez)
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 -c "from brain import _pocketbrain_pb, setup_contexts; setup_contexts(_pocketbrain_pb())"

# 2. Servidor web live
python3 brain_web.py --context personal --port 8899
# → http://localhost:8899

# 3. Exportar a markdown
python3 sync.py --context personal --full
```

### Desde el agente

```python
from brain import Brain

brain = Brain('personal')

# Páginas de conocimiento
brain.create_page("GPT-4o", body="Modelo multimodal de [[OpenAI]]", page_type="entity")
brain.create_page("Arquitectura hexagonal", body="Patron de diseno...", page_type="concept")

# Proyectos y tareas
brain.create_page("Migración K8s", page_type="project", domain="bravo")
brain.create_todo("Configurar CI/CD", domain="bravo")
brain.create_goal("Migrar 50% servicios", type="milestone", deadline="2026-09-30")
brain.move_todo(todo_id, "in progress")

# Diario y recordatorios
brain.journal_write("## Hoy\n- Avance en [[proyecto-x]]")
brain.create_reminder("Reunión", date="2026-12-25", time="10:00")
```

---

## Flujos Agentivos

PocketBrain está diseñado para ser usado **100% por scripts** desde el agente. No necesitas abrir la UI si no quieres. El flujo de trabajo:

1. **El agente entiende** el contenido, identifica entidades y relaciones
2. **El agente busca** contenido existente para evitar duplicados
3. **El agente escribe** con [[wikilinks]] y page_type correcto
4. **La UI web** es para consulta rápida y visualización

### Guardar conocimiento

```python
from brain import Brain

brain = Brain('personal')

# Buscar primero (Regla #0)
existing = brain.search("arquitectura cache")
if existing:
    brain.append_to_page(existing[0]['slug'], "- Nueva info: [[otra-pagina]]")
else:
    brain.create_page(
        "Arquitectura de cache",
        body="## Cache de write-through vs write-back\n\nRelacionado con [[rendimiento]]",
        page_type="concept",
        domain="bravo",
        tags=["backend", "perf"]
    )
```

### Gestión de Proyectos

```python
# Crear proyecto
brain.create_page("App Móvil", body="## MVP\n- Auth con OAuth", page_type="project", domain="projects")

# Crear goals/milestones
brain.create_goal("Lanzar MVP", type="milestone", project_slug="app-movil", deadline="2026-09-30")

# Tareas del proyecto
brain.create_todo("Diseñar UI", domain="projects", related_slugs=["app-movil"])
brain.create_todo("Setup backend", domain="projects", related_slugs=["app-movil"])

# Recordatorios
brain.create_reminder("Demo con cliente", date="2026-07-15", time="10:00", related_slugs=["app-movil"])
```

### Día a día

```python
# ¿Qué tengo para hoy?
brain.todos(status="today")
brain.reminders(date="today")

# Mover tarea
brain.move_todo("TODO_ID", "done")

# Diario automático
brain.journal_write("## Hoy\n- Terminé el PR #42\n- Revisar [[arquitectura-cache]]", mood="great")
```

### Auditoría

```python
brain.lint()          # Links rotos, huérfanos
brain.index()         # Catálogo completo
brain.recent_logs(20) # Trazabilidad
```

---

## Arquitectura

12 colecciones en PocketBase. Ver `references/schema.md` para detalle completo.

| Colección | Para |
|-----------|------|
| `contexts` | Contextos independientes (personal, projects, bravo, learning, health) |
| `brain_pages` | Páginas markdown unificadas con page_type discriminante |
| `brain_page_versions` | Historial de cambios de cada página |
| `brain_tags` | Tags para organización |
| `brain_domains` | Dominios/áreas de conocimiento |
| `brain_log` | Bitácora — quién hizo qué y para quién |

Los tipos específicos (todos, goals, reminders, journal) viven en `brain_pages` con `page_type` discriminante, no en colecciones separadas.

---

## Hash URLs

Toda navegación genera URLs con hash:

| Vista | Hash |
|-------|------|
| Projects | `#tab=projects` |
| Goals | `#tab=goals` |
| Goals con filtro | `#tab=goals&gstatus=active` |
| Reminders semanales | `#tab=reminders&rstatus=week` |
| Proyecto detalle | `#project=slug` |
| Proyecto tab | `#project=slug&ptab=goals` |
| Wiki page | `#tab=wiki&page=slug` |
| Wiki page tab | `#tab=wiki&page=slug&wtab=backlinks` |

---

## Scripts

| Script | Uso |
|--------|-----|
| `brain_web.py` | Servidor web live. `python3 brain_web.py --port 8899 --context personal` |
| `brain.py` | Cliente Python para agentes |
| `sync.py` | Export a markdown con frontmatter YAML |
| `graph.py` | Grafo HTML standalone per-contexto |
| `validate_ui.py` | Valida `web_ui.html` con `node --check` |

---

## Tracing

Cada operación registra quién (agente) y para quién (usuario). La tabla `brain_log` tiene `details: {agent, requested_by}` automático.

---

## Estado

Live. Funcionando en http://localhost:8899 con el contexto `personal`.
