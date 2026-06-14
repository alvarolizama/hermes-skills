---
name: pocketbrain
description: "Segundo cerebro digital sobre PocketBase. Prioridad: responder al usuario en conversación con markdown (tablas, listas, metadata). Web UI live es secundaria."
version: 2.29.0
author: Alvaro L.
platforms: [macos, linux]
metadata:
  hermes:
    tags: [wiki, knowledge-base, pocketbase, contexts, markdown]
    related_skills: [pocketbase, llm-wiki]
---

# PocketBrain — Segundo cerebro digital

Knowledge base multi-cerebro sobre PocketBase. **Prioridad #1: responder en la conversación con markdown.** La web UI es secundaria.

## Contexto obligatorio

**Todo** en PocketBrain requiere un contexto. Cada página, tarea, goal, reminder, journal está scoped a un contexto. No hay operaciones globales.

El agente usa `POCKETBRAIN_CONTEXT` del env, o un override explícito:

```python
brain = Brain()             # → POCKETBRAIN_CONTEXT o contexto default
brain = Brain('work')       # → override explícito de contexto
```

Cada contexto es un silo: sus propias páginas, tags, goals, todos, reminders, journal, log. Las queries siempre filtran por `context='{context_id}'`. Se crean los contextos que se requieran.

## Cómo responder al usuario

Cuando el usuario pregunte sobre datos en PocketBrain, responde **directo en la conversación** con markdown formateado. No le digas "ve a la web", no le compartas links de la UI. La conversación ES la interfaz.

### Antes de responder: claridad

Si la pregunta es ambigua, usa `clarify()` para confirmar:

- "proyectos" → ¿listar todos o uno específico?
- "dame el status" → ¿de qué proyecto?
- "tareas" → ¿cuáles? ¿de hoy? ¿de un proyecto?
- "journal" → ¿hoy, esta semana, últimos 7 días?

Ejemplo:

```python
clarify(
    question="¿De qué proyecto quieres el status?",
    choices=["PocketBrain", "Mundial 2026", "Otro (escribe)"]
)
```

### Formatos por canal

**Hermes Desktop (prioridad de integración):**
- Usa el formato más enriquecido posible: tablas, headings, listas, emojis moderados.
- Si hay muchos datos, adjunta archivo markdown.
- Destaca conteos y progreso en negritas.
- Incluye URLs hash cuando aporten: `http://localhost:8899/#project={slug}`.

**Telegram (rich messages):**
- Mensajes cortos con markdown nativo de Telegram, emojis.
- Máximo 4096 caracteres; si excede, resume o parte.
- Fechas en formato natural: "hoy", "mañana", "esta semana".

**CLI / terminal:**
- Texto plano denso, pipes, sin emojis.
- Una línea por ítem.

Ver `references/reports-by-channel.md` para plantillas completas.

### Patrones de respuesta

**Listar entidades con tabla:**
```markdown
## Proyectos (3)
| Proyecto | Pages | Links |
|----------|-------|-------|
| **PocketBrain** | 4 | 10 |
| Viaje a Japon 2026 | 2 | 5 |
| Rediseno web | 1 | 3 |
```

**Detalle de una página con metadata:**
```markdown
## GPT-4o
**Tipo:** entity · **Confianza:** high
**Tags:** multimodal, llm

OpenAI lanzó GPT-4o, un modelo multimodal...

**Relaciones:**
- → [[openai]]
- → [[claude-35-sonnet]]
```

**Status de tareas con columna visual:**
```markdown
## Todo (10)
| Tarea | Status | Proyecto |
|-------|--------|----------|
| Revisar PR #42 | ✅ done | PocketBrain |
| Configurar CI/CD | 🔄 in progress | K8s |
| Comprar vuelos | ⏳ backlog | Viaje Japon |
```

**Dashboard rápido de un contexto:**
```markdown
## Resumen: personal
- **Páginas:** 45 activas
- **Proyectos:** 3 · **Goals:** 4 · **Milestones:** 4
- **Todo:** 10 (3 in progress, 4 backlog, 3 done)
- **Reminders:** 8 (2 hoy, 3 esta semana)
- **Journal:** 7 entradas
```

### Reglas de respuesta

1. **Markdown first** — tablas, listas, code blocks, headings. Nunca texto plano.
2. **Nunca derivar a la web UI** — la respuesta debe ser autónoma en el chat.
3. **Contar todo** — siempre muestra conteos: "10 tareas", "4 milestones", etc.
4. **Relaciones visibles** — si una página tiene links, goals, tareas, muéstra los conteos.
5. **Si no hay datos, dilo claro** — "No hay milestones en este proyecto." en vez de dejar el espacio vacío.
6. **Agrupa por tipo** — usa headings para separar entidades, conceptos, tareas, etc.

## Flujo de trabajo para el agente — LLM Wiki compliance

PocketBrain es un LLM Wiki. Cada página tiene un page_type, relaciones trazables, y metadatos completos. El agente debe **entender, clasificar, relacionar y persistir** datos siguiendo un proceso estructurado.

### PASO 0 — Entender el contenido ANTES de guardar

Cuando el usuario te pida guardar algo, NO crees páginas de inmediato. Primero:

1. **Lee y procesa** el contenido completo. Identifica:
   - Entidades (personas, empresas, productos, modelos, lenguajes)
   - Conceptos (técnicas, patrones, ideas generales)
   - Acciones (tareas, proyectos, planes, metas)
   - Eventos (reuniones, fechas, recordatorios)
   - Relaciones entre todo lo anterior

2. **Determina el page_type** usando la tabla de inferencia abajo
3. **Busca existentes** con `brain.search()` antes de crear nada nuevo

**Regla #0: SIEMPRE busca primero.** Antes de crear cualquier página, usa `brain.search()` para verificar si ya existe contenido similar. Si existe, actualiza la página existente con `brain.update_page()` o `brain.append_to_page()`. **Nunca dupliques información.**

### PASO 1 — Inferir page_type

Usa esta tabla de decisión para determinar el tipo correcto:

| Señal en el contenido | page_type | Ejemplo de título |
|-----------------------|-----------|-------------------|
| Es una persona, empresa, producto, lenguaje, framework conocido | `entity` | "Álvaro Lizama", "OpenAI", "Elixir", "Phoenix" |
| Es un tema, técnica, disciplina, patrón de diseño | `concept` | "Arquitectura hexagonal", "CI/CD", "Machine Learning" |
| Tiene "vs" en el título o tablas comparativas en el body | `comparison` | "React vs Vue", "PostgreSQL vs MySQL" |
| Termina con "?" o es una pregunta que se responde | `query` | "¿Cómo optimizar consultas SQL?" |
| Es una fuente externa (artículo, paper, video, URL, PDF) | `raw` | "Paper Attention Is All You Need" |
| Tiene presupuesto, roadmaps, estrategias, especificaciones | `plan` | "Roadmap Q1 2026", "Estrategia de marketing" |
| Es una nota rápida, apunte, minuta de reunión, observación | `note` | "Nota reunión diseño", "Apunte sobre Rust" |
| Es una idea, brainstorming, propuesta, "qué tal si..." | `idea` | "Idea: app de fitness", "Qué tal si hacemos X?" |
| Tiene personas asignadas, fechas, entregables, estados | `project` | "Lanzar MVP 2026", "Migración a Kubernetes" |
| Es una tarea individual que puede tener status (backlog→done) | `todo` | "Revisar PR #42", "Comprar vuelos a Japón" |
| Es un objetivo general amplio, sin fecha fija | `goal` | "Mejorar rendimiento del equipo" |
| Es un hito con fecha límite específica | `milestone` | "Lanzar MVP antes del 30 Sep", "Beta cerrada" |
| Es un recordatorio con fecha y hora | `reminder` | "Reunión 10am con cliente", "Pagar factura luz" |
| Es una entrada de diario, bitácora del día | `journal` | "Journal 2026-06-10" |
| Es un archivo adjunto (PDF, imagen, doc) | `file` | "Diagrama arquitectura v2.pdf" |

> **Auto-suggest:** si no pasas `page_type`, se infiere solo via `suggest_page_type()`. Por ejemplo, `create_page(title="Nota reunión diseño")` → `page_type='note'` porque el título contiene "nota". Si quieres forzar un tipo, pásalo explícitamente.

**Si hay ambigüedad real** (ej. "Álvaro" podría ser entity o concept): pregunta al usuario.

**No preguntes por:** `confidence`, `tags`, `summary`, `source_url` — infiérelos del contexto.

### PASO 2 — Buscar contenido previo (evitar duplicados)

```python
# Siempre buscar ANTES de crear
existing = brain.search("GPT-4o")
if existing:
    brain.append_to_page(existing[0]['slug'], "- Nueva info: ...")
    # Si la info contradice lo existente, agregar nota de contestación
else:
    brain.create_page(title="GPT-4o", ...)
```

Busca con términos clave, no solo el título exacto. Ej: "arquitectura microservicios" también encuentra "microservicios arquitectura", "event-driven microservices".

### PASO 3 — Relacionar con [[wikilinks]]

Todo contenido debe estar linkeado con su contexto:

1. **`[[wikilinks]]` en el body** — los slugs existentes se resuelven solos y se guardan en `related_pages`
2. **Auto-backlinks** — si creas `[[gpt-4o]]` en una página, `gpt-4o` recibe un backlink automático
3. **`related_slugs`** — slugs adicionales manuales si el body no cubre todas las relaciones
4. **`^[ref-slug]`** — referencias a fuentes (raw pages)

**Siempre** usa `[[slug]]` cuando menciones otra página. No pongas texto plano si puedes linkear. Ejemplos:

```python
# BIEN: linkeado
body = "[[OpenAI]] lanzó [[GPT-4o]], un modelo [[multimodal]] que compite con [[Claude]]."

# MAL: texto plano sin links
body = "OpenAI lanzó GPT-4o, un modelo multimodal que compite con Claude."
```

Reglas de linking:
- Toda mención a una entidad conocida → `[[slug]]`
- Toda mención a un concepto relevante → `[[slug]]`
- Links a proyectos que mencionas → `[[slug-del-proyecto]]`
- ^[slug] para referencias a fuentes (raw pages)

### PASO 4 — Gestión de proyectos (goals, milestones, todos, reminders)

Cuando el contenido involucre ejecución, usa el sistema de proyectos:

```
proyecto (page_type='project')
  ├── goals (objetivos amplios, sin fecha)
  ├── milestones (hitos con deadline)
  ├── todos (tareas con status: backlog→this week→today→in progress→done)
  ├── reminders (recordatorios con fecha/hora)
  ├── ideas (propuestas relacionadas)
  ├── plans (roadmaps, specs)
  ├── notes (apuntes del proyecto)
  └── files (archivos adjuntos)
```

**Flujo de proyecto:**
```python
# 1. Crear el proyecto
brain.create_page("Migración K8s", page_type="project")

# 2. Definir goals y milestones
brain.create_goal("Migrar 50% servicios", status="active", deadline="2026-09-30",
                  project="migracion-k8s")  # relaciona al proyecto

# 3. Crear tareas
brain.create_todo("Configurar CI/CD para K8s", project="migracion-k8s")

# 4. Agendar recordatorios (reuniones, fechas límite)
brain.create_reminder("Demo migración", date="2026-08-15", time="10:00",
                      project="migracion-k8s")
```
```

**Para goals, usa el tipo correcto:**
- `goal` → objetivo amplio sin fecha: "Mejorar rendimiento"
- `milestone` → hito con deadline: "Lanzar MVP 30 Sep"

**Para todos, usa el sistema kanban integrado:**
- `backlog` → ideas pendientes de priorizar
- `this week` → comprometido para esta semana
- `today` → arrancando hoy
- `in progress` → en ejecución
- `done` → completado
- `cancelled` → cancelado

### PASO 5 — Tags

```python
# Tags: descriptivos, consistentes, en inglés
tags=["machine-learning", "nlp", "transformers"]
tags=["elixir", "phoenix", "ecto"]
tags=["devops", "kubernetes", "cicd"]

# Confidence: sé honesto sobre la certeza
kb_confidence='high'    # múltiples fuentes confiables, experiencia directa
kb_confidence='medium'  # bien documentado, hay debate, fuente única confiable
kb_confidence='low'     # fuente única, especulación, inferencia propia
```

### Resumen del flujo completo

```python
# 0. ENTENDER: leer, procesar, identificar entidades y relaciones

# 1. BUSCAR: evitar duplicados
existing = brain.search("GPT-4o")
if existing:
    brain.append_to_page(existing[0]['slug'], "- Nueva info: [[link-a-otra-pagina]]")
else:
    # 2. CREAR: con wikilinks y metadatos
    brain.create_page(
        title="GPT-4o",
        body="[[OpenAI]] lanzó GPT-4o...\nVs [[Claude 3.5 Sonnet]]...\n^[paper-x]",
        page_type="entity",
        kb_confidence='high',
        tags=["multimodal", "llm"]
    )
```

# 3. MANTENER: lint periódico
report = brain.lint()
if report['summary']['broken_links']:
    corregir_typos_o_crear_paginas()
if report['summary']['orphans']:
    agregar_links_desde_paginas_relacionadas()
```

### Links rotos: manéjalos solo, no preguntes

Si `broken_links` aparece:
1. **Typo** → corrígelo directamente (ej. `transforrmer` → `transformer`)
2. **Página faltante** → créala con `create_page()`, kb_confidence='low'
3. **No sabes** → créala igual con body mínimo, no bloquees el flujo

---

## Operaciones principales

```python
# Conocimiento
brain.create_page("Tema", body="## Ideas\n...", page_type="concept")
brain.search("machine learning")     # case-insensitive, rankeado
brain.append_to_page("mantrams", "- Nuevo", heading="2026-06-10")

# Tareas
brain.create_todo("Revisar PR", related_slugs=["proyecto-x"])
brain.todos(status="today")
brain.move_todo(id, "done")

```python
# Goals
brain.create_goal("Lanzar MVP", status="active", deadline="2026-09-30")
brain.create_milestone("Beta cerrada", status="active", deadline="2026-08-15")

# Proyectos
brain.create_project("App Móvil")
```
# Diario
brain.journal_write("## Hoy\n- Avancé en [[proyecto-x]]", mood="great")

# Recordatorios
brain.create_reminder("Reunión", date="2026-06-15", time="10:00")
brain.reminders(date="today")
```

```python
# Auditoría
brain.lint()           # huérfanos, broken links
brain.index()          # catálogo
brain.recent_logs(20)  # trazabilidad

# Seed data (para tests/demos)
# python3 scripts/seed.py  # crea ~72 páginas interconectadas
```

---

## Setup (headless por default)

PocketBrain funciona **sin necesidad de levantar servidor web**. Desde el agente se opera directamente sobre PocketBase y se responde al usuario con markdown.

### Dependencias

| Dependencia | Uso | Cómo se resuelve |
|-------------|-----|------------------|
| `pocketbase` skill → `pb.py` | Cliente HTTP PocketBase | `sys.path.insert(0, ~/.hermes/skills/productivity/pocketbase/scripts)` |
| `curl` (en PATH) | File uploads vía multipart en `create_page()`, `ingest_file()` | `which curl` |
| `POCKETHOST_HOST`, `_EMAIL`, `_PASSWORD` | Credenciales PocketBase | `~/.hermes/.env` (independiente de `POCKETBASE_*`) |
| `POCKETBRAIN_CONTEXT` | Contexto default del agente | `~/.hermes/.env` o variable de entorno. |

### Quick Start headless

```bash
# 0. Verificar dependencias
which curl || brew install curl

# 1. Crear las 6 colecciones (una vez)
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 -c "from brain import _pocketbrain_pb, setup_contexts; setup_contexts(_pocketbrain_pb())"

# 2. Exportar a markdown (opcional)
python3 sync.py --context personal --full
```

```python
# 3. Desde el agente — esto es el modo normal
from brain import Brain
brain = Brain('personal')  # o Brain() usando POCKETBRAIN_CONTEXT
brain.orient()
brain.create_page("Nueva idea", page_type="idea")
brain.create_todo("Revisar logs", page_slug="nueva-idea", status="today")
brain.lint()
```

### Levantar la UI web (opcional)

Si quieres ver datos en navegador, el servidor live es opt-in:

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 brain_web.py --context personal --port 8899
# → http://localhost:8899
```

Requisitos:
- PocketBase corriendo con las colecciones creadas.
- Variables `POCKETHOST_HOST`, `POCKETHOST_EMAIL`, `POCKETHOST_PASSWORD` en `~/.hermes/.env`.
- Usa `--context <name>` para seleccionar el contexto.

Después de modificar módulos ES o CSS, reiniciar el servidor no basta por el cache del browser (`max-age=3600`). Usa `Cmd+Shift+R` o DevTools → Disable cache.

---

## Referencias

El skill tiene documentación detallada referenciada. Carga cada archivo solo cuando lo necesites:

| Archivo | Cuándo cargarlo |
|---------|-----------------|
| `references/auto-linking.md` | Auto-link de wikilinks, auto-suggest page_type, auto-backlinks |
| `references/llm-wiki-workflow.md` | Flujo LLM Wiki: ingest, calidad, mantenimiento, consulta |
| `references/llm-wiki-comparison.md` | Mapeo PocketBrain vs LLM Wiki de Karpathy |
| `references/schema.md` | Detalle de las 6 colecciones y sus campos, historial de unificación |
| `references/schema-audit.md` | Auditoría de integridad del schema: checklist 10 puntos para detectar colecciones legacy, stale references e inconsistencias lectura/escritura |
| `references/goals.md` | Sistema de goals y milestones |
| `references/reports-by-channel.md` | Reportes predefinidos y formatos por canal: Hermes Desktop, Telegram, CLI |
| `references/web-ui.md` | Navegación y vistas del servidor web live (opcional) |
| `references/web-ui-patterns.md` | Refactor frontend: tabs, progreso, toasts, markdown, modular SPA |
| `references/frontend-es-modules.md` | Guía completa para refactorizar web_ui.html a módulos ES |
| `references/modular-spa-pitfalls.md` | Pitfalls del refactor a módulos ES: imports/exports, cache del browser, lint view, wikilinks case-insensitive, view stacking, navegación de cards, backend relations |
| `references/sidebar-layout.md` | Layout del sidebar: alineación icono-label-count y orden de items |
| `references/backend-relations-shape.md` | PocketBase `expand=related_pages` puede devolver dict o list; cómo manejar ambas shapes en `brain_web.py` |
| `references/ui-consistency-patterns.md` | Patrones de consistencia visual: headers con icono, tabs con iconos, filter select uniforme, kanban unificado, sin emoji, hash state |
| `references/project-detail-validation.md` | Checklist para completar y verificar la vista de detalle de proyecto: tabs, counts, navegación de cards, verificación de stacking |
| `references/web-ui-debugging.md` | Debug de UI con browser_console, node --check, validación de backend relations |
| `references/web-ui-js-escaping.md` | Pitfalls de escaping en web_ui.html |
| `references/html-js-patching.md` | Modificar JS inline sin romperlo |
| `references/design-systems.md` | Diseño visual: tokens, dark mode |
| `references/frontend-icon-patterns.md` | Iconos SVG Heroicons |
| `references/browser-debugging.md` | Debug de UI con browser_console |
| `references/cli-migration.md` | Mass rename de variables/colecciones |
| `references/rename-checklist.md` | Checklist pre/post mass rename |
| `references/realtime-fallback.md` | Heartbeat vs SSE para notificaciones |
| `references/env-architecture.md` | Variables de entorno POCKETHOST_* y POCKETBRAIN_CONTEXT; separación de responsabilidades con pocketbase skill |
| `references/repo-maintenance.md` | Mantener repo sync con skill runtime |
| `references/tracing.md` | Trazabilidad con brain_log |
| `references/collection-unification.md` | Como migrar colecciones a brain_pages y agregar nuevos tipos al sidebar |
| `references/ui-filter-pattern.md` | Filtro Todos/Con proyecto/Sin proyecto en type views, basado en [[wikilinks]] al body |
| `references/schema-update.md` | Como actualizar colecciones en PocketBase existentes |
| `references/pocketpages-migration.md` | Alternativa PocketPages: web UI server-rendered con EJS, FAB, Command Palette, Kanban drag & drop |
| `references/view-activation-pitfall.md` | showIndex() y otras funciones deben activar view-wiki explícitamente |
| `references/ui-validation-checklist.md` | Checklist de validación visual y de navegación tras cambios en la UI |
| `references/screenshots-readme-workflow.md` | Cómo refrescar screenshots y README.md tras cambios UI (secuencia de vistas, rutas relativas, README conciso) |
| `references/domain-to-context-cleanup.md` | Domain ya no se usa; contexto es el único silo. Schema, API y UI actualizados |
| `references/context-only-migration.md` | Guía de migración a context-only: schema, reportes, UI, lecciones |
| `references/schema-refactor-patterns.md` | Convenciones para refactorizar el schema de brain_pages: campos compartidos vs prefijados, relaciones por contexto, mass rename checklist |
| `references/project-detail-ui.md` | Implementación completa de vista de proyecto: métricas, 12 tabs, kanban, grafo local |
| `references/ui-consistency-patterns.md` | Patrones de consistencia visual: headers con icono, tabs con iconos, filter select uniforme, kanban unificado, sin emoji, hash state |

### Changelogs

| Version | Cambios |
|---------|--------|
| v2.29.0 | Schema refactor: prefixed/shared fields (`status`, `owner`, `deadline`, `date`, `time`, `done`, `done_date`, `mood`, `project`) and type-specific fields (`todo_goal`, `kb_*`, `file_*`). Renamed env vars `POCKETBRAIN_HOST/EMAIL/PASSWORD` → `POCKETHOST_HOST/EMAIL/PASSWORD`. Rewrote `setup_contexts()` to create collections in two passes with deferred self/cross-relations. Rewrote `seed.py` with dense generic demo data. Wiped and re-seeded live PocketBase. See `references/schema-refactor-patterns.md` and `references/env-architecture.md`. |
| v2.28.0 | Domain concept removed entirely. Schema drops `brain_domains` collection and `domain` field from `brain_pages`. API no longer accepts/returns `domain`. UI no longer renders domain chips. Updated `references/domain-to-context-cleanup.md`. Context is the only organizational silo. |
| v2.27.1 | Added predefined reports (`report_projects`, `report_project_status`, `report_todos`, `report_journal`, `report_reminders`, `report_lint`) in `brain.py` plus `/api/reports/*` endpoints in `brain_web.py`. Added channel-aware response formatting: use `clarify()` for ambiguous queries, then format for Hermes Desktop (rich markdown), Telegram (short + emojis), or CLI (dense pipes). See `references/reports-by-channel.md`. |
| v2.26.1 | Removed `okr` and `deliverable` page types (14 types total). Updated `brain.py` PAGE_TYPES, `create_goal` validation, and `sync.py` to match. Docs no longer list real/default contexts as examples. Added `references/screenshots-readme-workflow.md`. |
| v2.25.0 | Skill optimizado para uso headless: Setup reordenado, UI web documentada como opcional. Project detail completo: dashboard de métricas + 12 tabs (Contenido, Goals, Milestones, Ideas, Planes, Todo kanban, Notas, Reminders, Journal, Archivos, Pages, Graph). brain.py: PAGE_TYPES, validaciones en create_page/create_goal/create_todo/create_reminder, list_goals filtra por project_slug. brain_web.py: fix `related` no definido en `get_todos` cuando related_pages es lista. |
| v2.24.1 | Modular SPA refactor completado: view stacking fix, project detail con todas las tabs y counts reales, cards navegables, wikilinks/backlinks navegables sin stacking, sidebar iconos alineados, Entregables eliminado. Backend: normalizar `expand.related_pages` (dict vs list) en `brain_web.py`. Seed: reminders/journal ahora vinculan `page_slug`. Nuevas referencias: `backend-relations-shape.md`, `project-detail-validation.md`, `modular-spa-project-tabs.md`, `modular-spa-journal.md`, `brain-py-improvement-plan.md`. |
| v2.24.0 | Markdown-first + contexto obligatorio + POCKETBRAIN_CONTEXT + showIndex view activation + Wiki sidebar link + breadcrumb ← Todos tipo linkeable. Fix: status tabs en goals/milestones (gt is not defined, typeFilter perdido). Cards clickeables. Links con href=# → javascript:void(0). |
| v2.24.0 | Markdown-first + contexto obligatorio + POCKETBRAIN_CONTEXT + showIndex view activation + Wiki sidebar link + breadcrumb ← Todos tipo linkeable. Fix: status tabs en goals/milestones (gt is not defined, typeFilter perdido). Cards clickeables. Links con href=# → javascript:void(0).
| v2.20.0 | Minimalist cards (title only, no chips/status/metadata). Sidebar `;return false` en todos los onclicks. Pitfall: read_file() corrompe archivos si se escribe de vuelta. |
| v2.18.0 | Filter select: Todo y Reminders cambian a Todos/Con proyecto/Sin proyecto. Fix goal filter else-if bug ('project' atrapado por else-if generico). Actualizado ui-filter-pattern.md con page_slug filter y pitfall. |
| v2.17.0 | fix: showPage() desactiva vistas previas antes de activar view-wiki para evitar stacking. |
| v2.14.0 | LLM Wiki gaps: metadata sidebar, confidence badges, provenance markers, archived toggle, lint view, detect_drift, validate_frontmatter, archive_old, rotate_log |
| v2.13.0 | Live status indicator, change toasts, heartbeat polling |
| v2.12.0 | Goal progress removed, status-only goals |
| v2.11.0 | Project kanban filters (all, no-goal, by-goal) |
| v2.10.0 | URL deep-linking, graph legends, consistent branding |
| v2.9.x | UI refactor: sidebar, tabs, Heroicons, wiki page layout, project view, lint |

### Pitfalls

- **CREATION_ORDER**: las relaciones mandan. Ver setup_contexts() en brain.py.
- **Self-ref fields**: `brain_pages` auto-relaciones (`related_pages`, `project`, `todo_goal`) y relaciones cruzadas (`brain_log.page`, `brain_page_versions.page`) se agregan con PATCH post-creación. Ver `setup_contexts()` en `brain.py`.
- **Naming**: campo relation se llama `context` y la colección padre es `brain_contexts`.
- **`_get_page()` returns error dicts on 404, not None**: PocketBase devuelve `{"data":{}, "message":"not found", "status":404}` cuando una página no existe. La función `_get_page()` lo retorna directamente. **Siempre verifica `'id' in result` antes de usar cualquier campo del dict retornado.** Usa `page = self._get_page(slug); if page and 'id' in page:` como patrón.
- **PocketBase schema updates**: `setup_contexts()` solo CREA colecciones que no existen. No actualiza colecciones existentes con nuevos campos o valores. Para actualizar una colección existente:
  1. Usar `pb.import_collections()` con el schema completo (requiere resolver IDs de relaciones a pbc_xxx)
  2. O usar `pb.update_collection(id, {'fields': ...})` agregando campos uno por uno
  3. O borrar la colección con `pb.delete_collection(name)` y recrear con `setup_contexts()` (pierde datos)
  Ver `references/schema-update.md`.
- **Mass renames**: verificar 4 clases de referencias. Ver references/cli-migration.md.
- **showPage() debe desactivar vistas previas**: `showPage()` renderiza en `view-wiki` pero no llama a `showCurrentView()`. Si una vista previa (project, type view, etc.) sigue activa, su `display:block` se mantiene y el contenido de `view-wiki` se renderiza **debajo**. Fix: agregar `document.querySelectorAll('#main>div').forEach(function(d){d.classList.remove('active');});` al inicio de `showPage()`, ANTES de activar `view-wiki`. Verificar con `curl -s http://localhost:PORT/ | sed -n '597,601p'` que la línea esté presente en el HTML servido.
- **Zombie server process after restart**: al editar `web_ui.html` y reiniciar `brain_web.py`, el proceso OLD puede quedar vivo escuchando en el mismo puerto y sirviendo la versión vieja. `process(action='kill')` puede fallar silenciosamente. Siempre verificar con `lsof -i :PORT` y `kill -9 PID` si es necesario. Confirmar con `curl -s http://localhost:PORT/ | grep -n 'document.querySelectorAll.*remove.*active'` que el fix está siendo servido.
- **read_file + write_file corrompe archivos**: Hermes `read_file()` devuelve contenido con prefijos de línea (`LINE_NUM|content`). Si haces `content = result['content']` y luego `write_file(path, content)`, los prefijos de línea se escriben al archivo, corrompiéndolo. **Solución**: NUNCA escribir `result['content']` de vuelta. Usar `terminal()` para leer/escribir, o `execute_code()` que maneja archivos directamente con `open()`. Para parchar web_ui.html, usar `patch` tool (el más seguro) o escribir un script Python a /tmp/ y ejecutarlo.\n- **switchProjectTab sections sin handler**: en `renderProjectView()` se agregan tabs (milestones, ideas, plans, notes) que linkean a `switchProjectTab()`. Si no existe un bloque `if(tab==='...')` en `switchProjectTab`, el tab se clickea y el `#project-tab-content` queda vacío sin mensaje. **Regla**: por cada tab que agregues en `renderProjectView()`, agrega un handler correspondiente en `switchProjectTab()` con `if(!items.length)h+='<p>No hay X.</p>'`.```
- **Filter select consistency**: Todo y Reminders views usaban per-project dropdown (`<option value="slug">Nombre</option>`) en vez del patrón estándar `Todos / Con proyecto / Sin proyecto` que usan Goals y type views. **Regla**: todas las vistas usan el mismo select de 3 opciones. El mechanismo de filtrado varía (body wikilinks vs page_slug), pero el HTML del select es idéntico. Ver `references/ui-filter-pattern.md`.
- **Goal filter else-if bug**: `renderGoalsView()` tenía `else if(_goalFilter) filtered = ...` que atrapa el valor `'project'` y ejecuta `page_slug === 'project'` (nunca match). El fix es `else if(_goalFilter==='noproject')`. Ver `references/ui-filter-pattern.md` para el patrón correcto.
- **Goal filter chaining**: en `renderGoalsView()`, `_goalFilter` y `typeFilter` se aplican secuencialmente. Si `_goalFilter` usa `GOALS.filter` en vez de `filtered.filter`, el typeFilter previo se pierde y filtra sobre el array completo. Siempre encadenar: `filtered = GOALS.filter(...)` primero, luego `filtered = filtered.filter(...)`.
- **Status tabs en Goals/Milestones pierden el typeFilter**: los onclick de los tabs de status (Todos/Activos/Terminados/Cancelados) llaman a `renderGoalsView()` sin argumento, perdiendo el typeFilter actual ('goal' o 'milestone'). Fix: guardar `typeFilter` en `window._goalTypeFilter` y pasar `renderGoalsView(window._goalTypeFilter)` en los onclick.
- **`gt` es undefined en onclick de status tabs**: la variable local `var gt=typeFilter||'goal'` dentro de `renderGoalsView()` se usa en los onclick generados como string HTML, pero cuando el onclick se ejecuta, `gt` ya salió de scope. Fix: usar `window._goalTypeFilter` en vez de `gt` en los onclick handlers.
- **showIndex() debe activar view-wiki**: `showIndex()` renderiza el índice completo en `view-wiki` pero NO activa la vista (no remueve `active` de las otras vistas, no llama `closeSidebar()`). Fix: agregar `document.querySelectorAll('#main>div').forEach(function(d){d.classList.remove('active');});closeSidebar();document.getElementById('view-wiki').classList.add('active');` al inicio de `showIndex()`. Igual que el fix de `showPage()`.
- **browser_vision poco confiable para detectar stacking de vistas**: el modelo de visión puede reportar "se ve solo una vista" cuando en realidad hay dos divs con `display:block` apilados. Para verificar stacking, usar `browser_console` con expresión `document.querySelectorAll('#main > div.active').length` para contar vistas activas, o inspeccionar el HTML servido con curl.
- **Layout unificado: H1 + select en view-header, tabs debajo**: todas las vistas tienen el H1 y el *filter select* juntos en `view-header` (select a la derecha del H1). Los *status tabs* van debajo en `div.project-tabs` con `margin:12px 0`. NO poner status tabs inline con el H1. Ver `references/ui-filter-pattern.md` seccion "Layout correcto".
- **Cards minimalistas (solo titulo)**: en listas de proyectos, goals, milestones y type views, las cards deben mostrar solo el titulo. Sin chips de tipo (goal/milestone), sin contadores de tareas, sin status/deadline. Solo `<h3>title</h3>`.
- **Sidebar onclicks con return false**: todos los `<a href="#" class="nav-link">` del sidebar deben tener `;return false` al final del onclick para que el sidebar se cierre en mobile. Si no, el `href="#"` puede causar navegacion antes de que JS ejecute `closeSidebar()`.
- **renderTypeView usa `var h=` no `h+=` para la primera linea**: `renderTypeView()` asigna `var h=...` mientras que las otras vistas usan `h+=...` despues de `var h=...`. Al hacer patch, diferenciar entre `var h=` (primera linea) y `h+=` (concatenacion).
- **Toda navegacion debe generar hash URL**: cada vez que se agrega un sub-tab o filtro, debe llamar a `setHashParams()` para reflejar el estado en la URL. Puntos clave: `switchProjectTab()`, `switchPageTab()`, goal status tabs, reminder status tabs. Si agregas un nuevo sub-tab, agrega `setHashParams` en el template Y actualiza `restoreFromHash()`.
- **restoreFromHash debe manejar sub-tabs**: al anadir un nuevo parametro hash (ptab, wtab, gstatus, rstatus), `restoreFromHash()` debe restaurarlo. Los sub-tabs que dependen de datos async (project, wiki page) usan `setTimeout` para esperar que los datos esten disponibles.
- **href=\\"#\\" resetea el hash después de setHashParams()**: los links del sidebar y navegación usaban `href="#"` con onclick handlers. El browser procesa `#` DESPUÉS de que el onclick termina, sobrescribiendo el hash que `history.replaceState/acaba de poner con `setHashParams()`. **Fix**: usar `href="javascript:void(0)"` en vez de `href="#"`. Verificado con `location.hash` después de click. **Aplica también a wikilinks en mdToHtml()** — los `[[wikilinks]]` generan `<a href="#">` que causan el mismo problema.
- **Graph screenshot requiere fit() manual**: vis.js physics puede dejar nodos dispersos fuera del viewport. Antes de tomar screenshot, ejecutar `window._net.setOptions({physics:{enabled:false}}); window._net.fit();`. Si aún se ve vacío, probar `window._net.moveTo({scale:0.08})`. Verificar con `'nodes=' + GRAPH.nodes.length + ' edges=' + GRAPH.edges.length` que los datos existen.
- **vis.js destruye innerHTML del contenedor**: cuando se inicializa vis.Network en un contenedor (<div id="graph-view">), vis.js reemplaza el innerHTML del contenedor con sus propios elementos SVG/Canvas. Cualquier elemento hijo (como leyendas, controles) debe ser hermano de graph-view, no hijo. Ver web_ui.html: view-graph > graph-view + graph-legend.
- **Goals/Milestones cards no tienen onclick**: `renderGoalsView()` renderiza `<div class=\\\"card\\\"><h3>'+g.title+'</h3></div>` sin onclick handler. Fix: agregar `slug` en `get_goals()` de brain_web.py, y en la card poner `onclick=\\\"showPage(\\\\'+g.slug+'\\\\')\\\"` con `cursor:pointer`, `padding:12px`, y `esc(g.title)`. Ver references/web-ui-patterns.md.
- **Wikilink href=\\\"\\\\#\\\" en mdToHtml resetea hash**: los `[[wikilinks]]` en el body se renderizan como `<a href=\\\"\\\\\\\\#\\\" class=\\\"wl\\\" ...>`, mismo bug del `href=#` que resetea el hash después de `setHashParams()`. Fix: cambiar `href=\\\"\\\\\\\\#\\\"` → `href=\\\"javascript:void(0)\\\"` en `mdToHtml()`.
- **Status tabs pierden typeFilter**: `renderGoalsView()` genera status tabs (Todos/Activos/Terminados/Cancelados) con `onclick` que llama `renderGoalsView()` SIN argumento, perdiendo el `typeFilter` actual (goal vs milestone). Symptom: al clickear un tab en Milestones, el heading cambia a "Goals" y el filtro se aplica a ALL types. Fix: (1) almacenar `window._goalTypeFilter=gt` al inicio de la función, (2) reemplazar `gt===` en los onclick handlers con `window._goalTypeFilter===`, (3) cambiar `renderGoalsView()` por `renderGoalsView(window._goalTypeFilter)`. Ver references/web-ui-patterns.md.
- **Breadcrumb showPage no muestra tipo clickable**: el breadcrumb en `showPage()` tenía `← Wiki · '+p.page_type+'` con page_type como texto plano. Fix: (1) cambiar `← Wiki` → `← Todos`, (2) page_type como `<a>` con `onclick="showTab(\\'type_\\'+p.page_type)"`, (3) incluir título en el breadcrumb con `'+p.title+'`. La estructura JS: `\\'+p.page_type+\\'` usa `\\'` para escapar comillas dentro del string exterior (JS string concatenation). Al hacer patch, usar Python double-quoted strings con `\\'` para escaped quotes y `'` sin backslash para los terminadores de string exterior. Ver references/web-ui-js-escaping.md.
- **JS string terminators vs escaped quotes**: Al editar JS que concatena HTML con `'+exp+'`, la `'` que sirve como **terminador del string** debe ser `'` (0x27) sin backslash. La `'` dentro de atributos HTML (onclick) debe ser `\'` (0x5c 0x27) para no terminar el string exterior. Si ves `'+p.page_type+'` renderizado como texto literal en vez de evaluado, es porque la `'` tiene un backslash antes (`\'`) y JS la trata como caracter escapado, no como terminador. Usar byte-level editing (ver `references/html-js-patching.md`) para este tipo de fixes.
- **CDN script bloquea inline script
- **node --check debe saltar scripts CDN**: al validar web_ui.html, extraer el SEGUNDO <script> tag (el inline, sin src). El primero suele ser el CDN de vis.js. Usar html.split('<script>')[2].split('</script>')[0] en vez de regex que empareje el primero.

- **PocketPages data injection**: en templates EJS de PocketPages, los datos retornados por `+middleware.js` y `+load.js` se inyectan en la variable `data`, NO en `context`. Usa `const { ctxId, counts } = data` en las templates. `context` es el contexto interno de PocketPages (`ctx`, `params`, `log`, etc.). Ver `references/pocketpages-migration.md`.
- **PocketPages API routes**: para endpoints POST, lee el body con `ctx.body()` y responde con `ctx.json(code, obj)`. No existen `request.body` ni `response.status` en el scope de las páginas EJS de PocketPages.
- **PocketPages no tiene CLI**: `bunx pocketpages serve` no funciona. Es un plugin de JSVM de PocketBase; se corre con `./pocketbase serve --hooksDir=./pb_hooks`.

### Workflow notes (Alvaro's style)

- **Sample data must stay generic.** Seed scripts, SKILL.md examples, and any reusable skill code must NOT mention the user's company, role, or real projects (e.g., no "Bravo", "CTO", work-specific contexts). Default to generic placeholders (`proyectos`, `work`, `personal`) and ask before inserting real context.
- **`bravo` is a context, not a domain.** In PocketBrain, context names are passed to `Brain('...')`. Keep all examples neutral and avoid using real context names as examples. If you need a placeholder, use generic ones like `"work"` or `"personal"`.
- **No fake/default contexts in README examples.** Do not list `personal, projects, bravo, learning, health` as if they were predefined. The docs should say contexts are created as needed and use `<context_name>` placeholders.
- **"commit"** = commit inmediato sin discusion. git add + commit, reporta el hash.
- **Terse, directo, sin branding.** UI limpia sin texto de producto.
- **Diff contra runtime antes de editar repo.** Sync primero.
- **Siempre verificar visualmente** después de cambios UI. No decir "jala" sin ver screenshot.
- **Subagentes con tareas UI grandes pueden quedarse atascados:** cuando una tarea requiere coordinar múltiples archivos JS/CSS/backend y verificación visual, es más seguro dividirla en pasos manuales directos (backend → CSS → JS → browser) que delegarla en una sola corrida larga a un subagente. El subagente puede dejar avance parcial e inconcluso si se queda sin tiempo.
- **`--no-gpg-sign`** en commits. GPG key no disponible en este entorno.
- **Layout UI preferido**: el *filter select* (Todos/Con proyecto/Sin proyecto) va dentro del `view-header` a la DERECHA del H1. Los *status tabs* (Todos/Activos/Terminados) van debajo en `div.project-tabs` con `margin:12px 0`. NO mover el select debajo del H1 (eso fue un error mio).
- **Sidebar layout**: cada item debe ser un flex container con `align-items:center; justify-content:space-between`. El icono SVG y el label deben compartir una línea de base con `gap:8px` y `line-height` común. Los contadores van alineados a la derecha. Ver `references/sidebar-layout.md`.
- **Entregables no va en sidebar**: Álvaro usa solo `Archivos`. Deliverables ya no es un item de navegación principal.
- **Hard refresh obligatorio**: `brain_web.py` sirve assets JS con `Cache-Control: max-age=3600`. Después de cambiar módulos ES, reiniciar el servidor NO basta. Usar `Cmd+Shift+R` o DevTools con "Disable cache" para ver los cambios.
- **Subagentes para fixes UI no son garantía**: los subagentes pueden llegar al límite de iteraciones sin aplicar el fix, dejando solo análisis parcial. Si el fix es pequeño y crítico (ej. un import roto, un `classList.add` que causa stacking), es más rápido hacerlo directamente, validar con `node --check`, y luego lanzar subagentes solo para verificación o tareas paralelas grandes. Siempre re-verificar visualmente después de subagentes.
- **Subagentes para refactors de backend también pueden quedarse cortos**: refactorizar `brain.py`, `brain_web.py`, `sync.py`, `graph.py` y todo el schema a la vez excede la ventana de atención de un subagente. Dividir en fases (schema → backend → frontend → seed → validación visual) y verificar `py_compile` / `node --check` en cada paso. Si un subagente se atasca, continuar manualmente con lecturas directas y scripts de reemplazo controlados.
- **Modular SPA: validar imports y registros de router**: al extraer funciones a módulos ES (ej. `views/project-detail.js`), asegurar que el handler registrado en `Router.register('project', handler)` coincida con la firma `(slug, ptab)`. Si el router pasa `ptab` pero el handler lo ignora, las tabs internas no se restauran desde el hash.
- **Validación mínima de project detail**: al terminar el project detail, confirmar en browser: (a) todas las tabs visibles con counts reales, (b) tab Contenido renderiza markdown, (c) click en goal/todo/reminder/journal/file navega a la página sin stacking (`#main > div.active` === 1), (d) wikilinks dentro del markdown y backlinks también navegan sin stacking.
- **Breadcrumb links must use valid targets**: in `wiki.js` the page-type breadcrumb calls `showTab('type_' + type)`. That only works if the matching `view-type-*` container exists in `web_ui.html`. When adding a new `page_type`, also add its `<div id="view-type-NAME">` to `web_ui.html` or the breadcrumb click will blank the main area without an error. Verified by checking `document.querySelectorAll('#main > div.active').length === 1` after navigation.
- **`Store.setFilter` throws on unknown view keys**: `initialState.filters` only defines slots for `page`, `goal`, `todo`, `reminder`, `file`, and `journal`. Type views call `Store.setFilter(typeName, value)` with keys like `concept` or `project`, which used to throw. Fix: make `setFilter` silently ignore unknown keys instead of throwing, or pre-register every `page_type` in `initialState.filters`.
- **Header icon alignment**: `web_ui.css` must style `.view-header h1` with `display:inline-flex;align-items:center;gap:10px` and `.view-header h1 svg { display:block; flex-shrink:0; color:var(--body) }`, otherwise the Heroicon may appear misaligned or not render at all in the accessibility tree. Also make sure `.project-tabs a .tab-label` uses `display:inline-flex;align-items:center;gap:6px` so icons align with labels inside tabs.
- **Browser cache on `brain_web.py` assets**: `brain_web.py` serves JS/CSS with `Cache-Control: max-age=3600`. Restarting the server is not enough after editing modules; use `?nocache=N`, DevTools disable cache, or hard refresh to see changes.
- **UI consistency across all views**: headers, tabs, status filters, kanban columns, and cards must all use Heroicons. No emoji. Filter select is always `Todos / Con proyecto / Sin proyecto`. See `references/ui-consistency-patterns.md`.
- **Project graph tab must render a real network**: when `ptab=graph`, `renderProjectGraph()` must receive data that includes `goals`, `todos`, and `reminders` (not `rems`). The graph container must be visible; if the tab bar clips, add `flex-wrap:wrap` to `.project-tabs`. Verify with `document.querySelector('#project-graph-view canvas, #project-graph-view svg')`.
- **Graph legend labels must start with capital letter**: any label rendered in the graph legend should use `capitalize()` or a mapped display name so the first letter is uppercase. This applies to both global graph (`graph.counts`) and project graph (`ptypes`) legends. Mixed casing looks inconsistent in the UI.
- **Type view summaries must not leak markdown headings into cards**: `summary` fields can contain markdown, but card summaries should not render as full-size headings. Strip markdown to plain text or clamp `.card .md-content` styles. Verify cards do not show literal `**` asterisks.
- **Every hash-driven walkthrough must leave exactly one active view**: after navigating to any `#tab=...`, `#project=...`, or `#page=...` URL, run `document.querySelectorAll('#main > div.active').length === 1`. More than one means a view activation pitfall. See `references/ui-validation-checklist.md`.
- **Mobile header must stack title → breadcrumb → select**: on narrow viewports, the `.view-header` should use a flex column layout where the H1 is first, the breadcrumb is second, and the filter select is third. Do not leave them in a single horizontal row. This is the expected mobile layout. See `references/ui-validation-checklist.md`.
- **Screenshots and README must be refreshed together after UI changes**: when the user asks to update screenshots, follow the workflow in `references/screenshots-readme-workflow.md`: delete old PNGs, capture each view, update README paths/captions, sync runtime→repo, commit, and push.
