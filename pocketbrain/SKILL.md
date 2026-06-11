---
name: pocketbrain
description: "Wiki/cerebro de conocimiento multi-contexto sobre PocketBase — 12 colecciones, búsqueda rankeada, versionado, todos, goals, journal, reminders, deliverables, graph y servidor web live."
version: 2.15.0
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

## Flujo de trabajo para el agente

Este skill está diseñado para que el agente **infiera y organice solo**, pero que **pregunte cuando tenga dudas reales**.

### Regla de oro: infiere primero, pregunta si hay ambigüedad

**Regla #0: SIEMPRE busca primero.** Antes de crear cualquier página, usa `brain.search()` para verificar si ya existe contenido similar. Si existe, actualiza la página existente con `brain.update_page()` o `brain.append_to_page()`. No dupliques.

- Si el título tiene "vs" o el cuerpo tiene tablas → `comparison`
- Si el título termina con "?" o es una pregunta → `query`
- Si es una fuente externa (URL, paper) → `raw`
- Si es una persona, empresa, producto o modelo conocido → `entity`
- Si es un tema, técnica o idea general → `concept`
- Si tiene fechas, tareas y entregables → `project`

**Solo pregunta al usuario si:**
- No puedes distinguir entre `entity` y `concept` (ej. nombre ambiguo)
- No sabes en qué `domain` categorizarlo
- El usuario te pide explícitamente que decidas

**No preguntes por:** `confidence`, `tags`, `summary`, `source_url` — infiérelos del contexto.

### Los 6 page_types

| Tipo | Cuándo usarlo | Ejemplos |
|------|---------------|----------|
| `entity` | Personas, empresas, productos, modelos | "OpenAI", "GPT-4o", "AWS" |
| `concept` | Temas, técnicas, ideas, patrones | "Arquitectura microservicios", "Cache distribuido" |
| `comparison` | Comparativas side-by-side | "React vs Vue", "PostgreSQL vs MySQL" |
| `query` | Preguntas respondidas | "¿Cómo optimizar consultas SQL?" |
| `raw` | Fuentes originales (artículos, papers, videos, archivos) | "Paper Attention Is All You Need", "Video de microservicios" |
| `project` | Proyectos con goals y tareas | "Lanzar MVP 2026", "Migración K8s" |

### Raw sources: tipos de fuentes

Las páginas con `page_type='raw'` capturan distintas categorías de fuentes. Identifícalas por el contenido:

| Categoría | Cómo detectarlo | Método de ingesta |
|-----------|----------------|-------------------|
| `raw:article` | Artículo web, blog post, newsletter | `ingest_text()` con `source_url` |
| `raw:paper` | Paper académico, PDF, arXiv | `ingest_file()` — sube el PDF como attachment |
| `raw:video` | Transcripción de video, charla | `ingest_text()` con link al video en body |
| `raw:file` | Documento, spreadsheet, imagen | `ingest_file()` — sube el archivo como attachment |
| `raw:note` | Nota propia, borrador, idea suelta | `ingest_text()` sin `source_url` |

Todas se guardan como `page_type='raw'`. La categoría se registra en los `tags`. El archivo físico se sube automáticamente via `ingest_file()`.

### Cómo se linkean las páginas

1. **`[[wikilinks]]` en el body** — los slugs existentes se resuelven solos y se guardan en `related_pages`
2. **Auto-backlinks** — si creas `[[gpt-4o]]` en una página, `gpt-4o` recibe un backlink automático
3. **`related_slugs`** — slugs adicionales manuales si el body no cubre todas las relaciones

**Siempre** usa `[[slug]]` cuando menciones otra página. No pongas texto plano si puedes linkear.

### Cómo organizar

```python
# Domain: agrupa por área
domain="investigacion"     # papers, descubrimientos
domain="proyectos"         # iniciativas concretas
domain="learning"          # aprendizaje personal
domain="bravo"             # trabajo en Bravo

# Tags: descriptivos, consistentes
tags=["machine-learning", "nlp", "transformers"]

# Confidence: sé honesto
confidence='high'    # múltiples fuentes confiables
confidence='medium'  # bien documentado, hay debate
confidence='low'     # fuente única, especulación
```

### Flujo completo

```python
# 0. BUSCAR primero: evitar duplicados
existing = brain.search("GPT-4o")
if existing:
    # Ya existe — actualizar en vez de crear
    brain.append_to_page(existing[0]['slug'], "- Nueva info: ...")
else:
    # No existe — crear

# 1. INGEST: fuente externa
brain.ingest_text(text=contenido, title="Paper X", source_url="...")

# 2. CREAR: páginas de conocimiento linkeadas
brain.create_page(
    title="GPT-4o",
    body="[[OpenAI]] lanzó GPT-4o...\nVs [[Claude 3.5 Sonnet]]...\n^[paper-x]",
    confidence='high',
    domain="investigacion",
    tags=["multimodal"]
)
# → page_type='entity' (auto-suggest), related_pages automático, backlinks automáticos

# 3. MANTENER: lint periódico
report = brain.lint()
if report['summary']['broken_links']:
    # Corregir typos o crear páginas faltantes
    pass
if report['summary']['orphans']:
    # Agregar [[wikilinks]] desde otras páginas
    pass
```

### Links rotos: manéjalos solo, no preguntes

Si `broken_links` aparece:
1. **Typo** → corrígelo directamente (ej. `transforrmer` → `transformer`)
2. **Página faltante** → créala con `create_page()`, confidence='low'
3. **No sabes** → créala igual con body mínimo, no bloquees el flujo

### Duda sobre page_type: guía rápida

| El contenido es... | page_type |
|---|---|
| Producto/empresa/persona/modelo | `entity` |
| Tema o técnica | `concept` |
| Comparativa | `comparison` |
| Pregunta respondida | `query` |
| Fuente externa (paper, artículo) | `raw` |
| Proyecto con fechas y tareas | `project` |

Si aún así tienes duda, **pregunta**: "¿Esto va como entity o concept?"

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


## Setup

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
python3 brain_web.py --context personal --port 8899
# → http://localhost:8899

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


---

## Referencias

El skill tiene documentación detallada referenciada. Carga cada archivo solo cuando lo necesites:

| Archivo | Cuándo cargarlo |
|---------|-----------------|
| `references/auto-linking.md` | Auto-link de wikilinks, auto-suggest page_type, auto-backlinks |
| `references/llm-wiki-workflow.md` | Flujo LLM Wiki: ingest, calidad, mantenimiento, consulta |
| `references/llm-wiki-comparison.md` | Mapeo PocketBrain vs LLM Wiki de Karpathy |
| `references/schema.md` | Detalle de las 12 colecciones y sus campos |
| `references/goals.md` | Sistema de goals, milestones y OKRs |
| `references/web-ui.md` | Navegación y vistas del servidor web live |
| `references/web-ui-patterns.md` | Refactor frontend: tabs, progreso, toasts, markdown |
| `references/web-ui-debugging.md` | Debug de JS runtime, validacion node --check |
| `references/web-ui-js-escaping.md` | Pitfalls de escaping en web_ui.html |
| `references/html-js-patching.md` | Modificar JS inline sin romperlo |
| `references/design-systems.md` | Diseño visual: tokens, dark mode |
| `references/frontend-icon-patterns.md` | Iconos SVG Heroicons |
| `references/browser-debugging.md` | Debug de UI con browser_console |
| `references/cli-migration.md` | Mass rename de variables/colecciones |
| `references/rename-checklist.md` | Checklist pre/post mass rename |
| `references/realtime-fallback.md` | Heartbeat vs SSE para notificaciones |
| `references/env-architecture.md` | Variables de entorno POCKETBRAIN_* |
| `references/repo-maintenance.md` | Mantener repo sync con skill runtime |
| `references/tracing.md` | Trazabilidad con brain_log |

### Changelogs

| Version | Cambios |
|---------|--------|
| v2.15.0 | Auto-linking, auto-suggest page_type, auto-backlinks, build_backlinks() |
| v2.14.0 | LLM Wiki gaps: metadata sidebar, confidence badges, provenance markers, archived toggle, lint view, detect_drift, validate_frontmatter, archive_old, rotate_log |
| v2.13.0 | Live status indicator, change toasts, heartbeat polling |
| v2.12.0 | Goal progress removed, status-only goals |
| v2.11.0 | Project kanban filters (all, no-goal, by-goal) |
| v2.10.0 | URL deep-linking, graph legends, consistent branding |
| v2.9.x | UI refactor: sidebar, tabs, Heroicons, wiki page layout, project view, lint |

### Scripts

| Script | Ruta |
|--------|------|
| `brain_web.py` | Servidor web live en localhost:8899 |
| `brain.py` | Cliente Python (Brain class) |
| `sync.py` | Export a markdown con frontmatter YAML |
| `graph.py` | Grafo HTML standalone per-contexto |
| `validate_ui.py` | Valida web_ui.html con node --check |

### Pitfalls

- **CREATION_ORDER**: las relaciones mandan. Ver setup_contexts() en brain.py.
- **Self-ref fields**: brain_goals.parent y brain_pages.related_pages se agregan con PATCH post-creacion.
- **Naming**: campo relation en PB se llama brain (legado) pero coleccion padre es contexts.
- **Mass renames**: verificar 4 clases de referencias. Ver references/cli-migration.md.

### Workflow notes (Alvaro's style)

- **"commit"** = commit inmediato sin discusion. git add + commit, reporta el hash.
- **Terse, directo, sin branding.** UI limpia sin texto de producto.
- **Diff contra runtime antes de editar repo.** Sync primero.