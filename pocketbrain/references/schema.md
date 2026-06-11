# PocketBrain — Schema completo

6 colecciones. Todo campo, tipo y relación.

## 1. `contexts` — Cerebros

| Campo | Tipo |
|-------|------|
| `name` | text (required, unique) |
| `label` | text |
| `description` | text |
| `schema_config` | json |

## 2. `brain_domains` — Áreas

| Campo | Tipo |
|-------|------|
| `name` | text (required) |
| `label` | text |
| `brain` | relation → contexts |

## 3. `brain_tags` — Taxonomía

| Campo | Tipo |
|-------|------|
| `name` | text (required) |
| `category` | text |
| `brain` | relation → contexts |

## 4. `brain_pages` — Conocimiento (unificado)

Todas las entidades se guardan en `brain_pages`. El campo `page_type` discrimina el tipo:

| page_type | Uso |
|-----------|-----|
| `entity` | Personas, empresas, productos, lenguajes |
| `concept` | Temas, técnicas, patrones |
| `comparison` | Tablas comparativas, "vs" |
| `query` | Preguntas respondidas |
| `raw` | Fuentes externas, papers, URLs |
| `project` | Proyectos con roadmaps |
| `plan` | Roadmaps, specs, estrategias |
| `note` | Notas rápidas, minutas |
| `idea` | Brainstorming, propuestas |
| `todo` | Tareas con status kanban |
| `goal` | Objetivos amplios sin fecha |
| `milestone` | Hitos con deadline |
| `okr` | OKR con key results |
| `reminder` | Recordatorios con fecha/hora |
| `journal` | Entradas de diario, bitácora |
| `file` | Archivos adjuntos |
| `deliverable` | Entregables versionados |

### Campos de brain_pages

| Campo | Tipo | Notas |
|-------|------|-------|
| `title` | text (required) | |
| `slug` | text (required, unique) | lowercase-hyphens |
| `page_type` | select | 17 valores (ver tabla arriba) |
| `body` | text | **Markdown puro** con `[[wikilinks]]` |
| `summary` | text | |
| `confidence` | select | high, medium, low |
| `source_url` | url | |
| `source_sha256` | text | |
| `contested` | bool | |
| `contradictions` | text | |
| `archived` | bool | |
| `attachment` | file | PDF, imagen |
| `file_type` | select | pdf, image, doc, sheet, other |
| `version` | text | Versión del entregable |
| `related_pages` | relation → brain_pages (N:M) | Auto-link desde `[[wikilinks]]` |
| `content` | text | Cuerpo alternativo |
| `status` | select | backlog, this week, today, in progress, done, cancelled, planned, active, completed, draft, review, final |
| `deadline` | date | Fecha límite (goals, milestones) |
| `owner` | select | alvaro, chaos-manager, bravo-manager, etc. |
| `date` | date | Fecha (reminders, journal) |
| `time` | text | Hora (reminders) |
| `done` | bool | Completado (reminders) |
| `done_date` | date | Fecha de completado |
| `mood` | select | great, meh, bad (journal) |
| `started_date` | date | Iniciado (todos) |
| `completed_date` | date | Completado (todos) |
| `cancelled_date` | date | Cancelado |
| `comment` | text | Comentario opcional (deliverables: milestone) |
| `brain` | relation → contexts | |
| `domain` | relation → brain_domains | |
| `tags` | relation → brain_tags (N:M) | |

## 5. `brain_page_versions` — Historial

| Campo | Tipo |
|-------|------|
| `page` | relation → brain_pages |
| `version` | number (required) |
| `title` | text |
| `body` | text |
| `summary` | text |
| `change_summary` | text |
| `page_type` | text |
| `confidence` | text |

## 6. `brain_log` — Bitácora

| Campo | Tipo |
|-------|------|
| `brain` | relation → contexts |
| `action` | select: ingest, update, query, lint, create, archive, delete, setup |
| `page` | relation → brain_pages |
| `description` | text |
| `details` | json |

---

## Historial de unificación

| Colección legacy | Equivalente actual en brain_pages | Migración |
|------------------|-----------------------------------|-----------|
| `brain_todos` | `page_type='todo'` | ✅ Unificado |
| `brain_goals` | `page_type='goal'\|'milestone'\|'okr'` | ✅ Unificado |
| `brain_reminders` | `page_type='reminder'` | ✅ Unificado |
| `brain_journal` | `page_type='journal'` | ✅ Unificado |
| `brain_deliverables` | `page_type='deliverable'` | ✅ Unificado v2.22.0 |
| `brain_files` | `page_type='file'` | ✅ Unificado v2.22.0 |
