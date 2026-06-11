# PocketBrain — Schema completo

12 colecciones. Todo campo, tipo y relación.

## 1. `brains` — Cerebros

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
| `brain` | relation → brains |

## 3. `brain_tags` — Taxonomía

| Campo | Tipo |
|-------|------|
| `name` | text (required) |
| `category` | text |
| `brain` | relation → brains |

## 4. `brain_pages` — Conocimiento

| Campo | Tipo | Notas |
|-------|------|-------|
| `title` | text (required) | |
| `slug` | text (required, unique) | lowercase-hyphens |
| `page_type` | select | entity, concept, comparison, query, raw, project |
| `body` | text | **Markdown puro** con `[[wikilinks]]` |
| `summary` | text | |
| `confidence` | select | high, medium, low |
| `source_url` | url | |
| `source_sha256` | text | |
| `contested` | bool | |
| `contradictions` | text | |
| `archived` | bool | |
| `attachment` | file | PDF, imagen |
| `related_pages` | relation → brain_pages (N:M) | Auto-link desde [[wikilinks]] |
| `brain` | relation → brains | |
| `domain` | relation → brain_domains | |
| `goal` | relation → brain_goals | |
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
| `brain` | relation → brains |
| `action` | select: ingest, update, query, lint, create, archive, delete, setup |
| `page` | relation → brain_pages |
| `description` | text |
| `details` | json |

## 7. `brain_todos` — Tareas

| Campo | Tipo |
|-------|------|
| `title` | text (required) |
| `content` | editor |
| `status` | select: backlog, this week, today, in progress, done, cancelled |
| `domain` | select: personal, projects, bravo |
| `owner` | select: alvaro, chaos-manager, project-manager, bravo-manager, minion, alv-bot, bravo-bot, ops-bot |
| `comment` | text |
| `started_date` | date |
| `completed_date` | date |
| `cancelled_date` | date |
| `brain` | relation → brains |
| `page` | relation → brain_pages |
| `goal` | relation → brain_goals |

## 8. `brain_goals` — Goals, Milestones, OKRs

| Campo | Tipo |
|-------|------|
| `title` | text (required) |
| `description` | text |
| `type` | select: goal, milestone, okr |
| `status` | select: planned, active, done, cancelled |
| `progress` | number (0-100) |
| `deadline` | date |
| `retrospective` | text |
| `brain` | relation → brains |
| `page` | relation → brain_pages |
| `parent` | relation → brain_goals |
| `tags` | relation → brain_tags |

## 9. `brain_reminders` — Recordatorios

| Campo | Tipo |
|-------|------|
| `title` | text (required) |
| `content` | text |
| `date` | date (required) |
| `time` | text |
| `done` | bool |
| `done_date` | date |
| `brain` | relation → brains |
| `page` | relation → brain_pages |

## 10. `brain_journal` — Diario

| Campo | Tipo |
|-------|------|
| `title` | text (required) |
| `body` | text |
| `date` | date (required) |
| `mood` | select: great, meh, bad |
| `brain` | relation → brains |
| `page` | relation → brain_pages |
| `tags` | relation → brain_tags |

## 11. `brain_deliverables` — Entregables

| Campo | Tipo |
|-------|------|
| `title` | text (required) |
| `description` | text |
| `version` | text |
| `status` | select: draft, review, final, archived |
| `milestone` | text |
| `file` | file |
| `brain` | relation → brains |
| `page` | relation → brain_pages |
| `goal` | relation → brain_goals |
| `tags` | relation → brain_tags |

## 12. `brain_files` — Archivos

| Campo | Tipo |
|-------|------|
| `name` | text (required) |
| `file` | file |
| `file_type` | select: pdf, image, doc, sheet, other |
| `brain` | relation → brains |
| `page` | relation → brain_pages |
| `goal` | relation → brain_goals |
