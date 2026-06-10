---
name: pocketbrain
description: "Wiki/cerebro de conocimiento multi-contexto sobre PocketBase — 12 colecciones, búsqueda rankeada, versionado, todos, goals, journal, reminders, deliverables, graph y servidor web live."
version: 2.0.0
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
python3 brain_web.py --brain personal
# → http://localhost:8080

# 3. Exportar a markdown
python3 sync.py --brain personal --full
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

---

## Scripts

| Script | Uso |
|--------|-----|
| `brain_web.py` | Servidor web live en `localhost:8080`. Brain selector, 7 tabs. |
| `sync.py` | Export a markdown local con frontmatter YAML |
| `brain.py` | Cliente Python para agentes |

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
