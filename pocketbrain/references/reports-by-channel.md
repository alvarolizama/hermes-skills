# Reportes y respuestas por canal

**Cuando el usuario pide información de PocketBrain por chat** ("proyectos", "status", "tareas", "journal", "recordatorios"), **nunca es una instrucción para modificar datos**. Es una consulta. El agente:

1. Usa `clarify()` si la solicitud es ambigua.
2. Obtiene datos con los métodos de reporte de `brain.py` o `/api/reports/*`.
3. Formatea la respuesta según el canal de comunicación.

PocketBrain expone datos estructurados vía `brain.py` y `/api/reports/*`. El agente formatea la respuesta según el canal y el tipo de reporte.

## Métodos de reporte en `brain.py`

| Método | Descripción |
|--------|-------------|
| `brain.report_projects()` | Lista de proyectos con goals, todos y progreso. |
| `brain.report_project_status(slug)` | Status completo de un proyecto. |
| `brain.report_todos(status=?, project_slug=?)` | Tareas con metadatos. |
| `brain.report_journal(days=7)` | Entradas de journal recientes. |
| `brain.report_reminders(date=?)` | Recordatorios próximos. |
| `brain.report_lint()` | Resumen de lint. |

Endpoints: `/api/reports/projects`, `/api/reports/project/{slug}`, `/api/reports/todos`, `/api/reports/journal?days=N`, `/api/reports/reminders?date=YYYY-MM-DD`, `/api/reports/lint`.

## Cuándo usar `clarify()`

Antes de consultar datos, usa `clarify()` si la solicitud es ambigua:

- El usuario dice "proyectos" → ¿listar todos o uno específico?
- "dame el status" → ¿de qué proyecto?
- "tareas" → ¿cuáles? ¿de hoy? ¿de un proyecto?
- "journal" → ¿de hoy, esta semana, últimos 7 días?

Ejemplo:

```python
# No se sabe cuál proyecto
clarify(
    question="¿De qué proyecto quieres el status?",
    choices=["PocketBrain", "Mundial 2026", "Otro (escribe)"]
)
```

## Formatos por canal

### Hermes Desktop (prioridad de integración)

**Si la conversación ocurre en Hermes Desktop, usa el formato más enriquecido posible:**
- Markdown enriquecido: tablas, headings, listas, emojis moderados.
- Si los datos son muchos, agrégalos como archivo adjunto en markdown.
- Incluye URLs hash cuando aporten: `http://localhost:8899/#project={slug}`.
- Destaca conteos y progreso en negritas.

Ejemplo:

```markdown
## 🎯 Proyectos (3)

| Proyecto | Todos | Progreso |
|----------|-------|----------|
| **PocketBrain** | 12/34 | **35%** |
| Mundial 2026 | 5/5 | **100%** |
```

### Telegram (rich messages)

**Mensajes cortos con markdown nativo de Telegram, emojis, y formato natural:**
- Máx 4096 chars. Si excede, resumir o partir.
- Fechas en formato natural: "hoy", "mañana", "esta semana".
- Para listas numeradas usar `1.`, `2.`.

Ejemplo:

```
📋 *Tareas de hoy* (4)

1. ✅ Revisar PR
2. 🔄 Configurar CI/CD
3. ⏳ Llamar a proveedor
```

### CLI / terminal

**Texto plano denso, pipes, sin emojis:**
- Una línea por ítem.
- Prioridad: rapidez de lectura.

Ejemplo:

```
PROJECTS | TODOS | PROGRESS
PocketBrain | 12/34 | 35%
Mundial 2026 | 5/5 | 100%
```

## Plantillas de reporte

### Proyectos

```markdown
## Proyectos ({count})
{tabla}
```

### Status de proyecto

```markdown
## {project.title}

- Goals: {counts.goals}
- Todos: {counts.todos} ({counts.todos_by_status})
- Reminders: {counts.reminders}
- Journal: {counts.journal}
- Notas: {counts.notes}
- Archivos: {counts.files}

### Goals
{lista}

### Todos pendientes
{lista}
```

### Todos

```markdown
## Tareas ({count})

**Pendientes:** {pending} | **En progreso:** {in_progress} | **Hechas:** {done}

{lista por status}
```

### Journal

```markdown
## Journal últimos {days} días ({count})

{fecha} — {mood}
{body}
```

### Reminders

```markdown
## Recordatorios ({count})

{fecha} {hora} — {título} {✅ if done}
```

### Lint

```markdown
## Lint

- Total páginas: {total_pages}
- Links rotos: {len(broken_links)}
- Huérfanos: {len(orphans)}
- Baja confianza: {len(low_confidence)}
```
