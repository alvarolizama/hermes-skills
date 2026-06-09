# Hermes Skills

Skills para [Hermes Agent](https://github.com/NousResearch/hermes-agent).

## Instalación

```bash
hermes skills tap add git@github.com:alvarolizama/hermes-skills.git
hermes skills install pocketbase
hermes skills install pocketbrain
```

---

## `pocketbase` — Cliente PocketBase API

Cliente genérico para interactuar con la API REST de PocketBase: autenticación, CRUD de colecciones y registros, archivos, realtime SSE.

```python
from pb import quick_pb
pb = quick_pb()
records = pb.list('mi_coleccion', filter="status='active'")
```

Variables de entorno: `POCKETBASE_HOST`, `POCKETBASE_EMAIL`, `POCKETBASE_PASSWORD`.

---

## `pocketbrain` — Segundo Cerebro Digital

Knowledge base multi-cerebro sobre PocketBase. 12 colecciones, servidor web live, trazabilidad completa.

```bash
python3 brain_web.py --brain personal
# → http://localhost:8080
```

### Proyectos

Cada proyecto agrupa goals, tareas, entregables y archivos.

![Projects](screenshots/projects.png)

### Kanban

Flujo de tareas con filtro por proyecto: backlog → this week → today → in progress → done.

![Kanban](screenshots/kanban.png)

### Goals & OKRs

Milestones con deadline, goals con progreso, OKRs con key results anidados y retrospectiva al cerrar.

![Goals](screenshots/goals.png)

### Graph

Visualización de todas las relaciones entre páginas, goals, tareas, deliverables y reminders.

![Graph](screenshots/graph.png)

### Desde el Agente

```python
from brain import Brain
brain = Brain('personal')

brain.create_page("Tema", body="## Ideas\n...", page_type="concept")
brain.search("machine learning")
brain.create_todo("Revisar PR", domain="bravo")
brain.create_goal("Lanzar MVP", type="milestone", deadline="2026-09-30")
brain.complete_goal(id, retrospective="Entregado a tiempo.")
brain.create_page("App Móvil", page_type="project")
brain.journal_write("## Hoy\n- Avancé en [[proyecto-x]]", mood="great")
brain.create_reminder("Reunión", date="2026-06-15", time="10:00")
```

### 12 Colecciones

| Colección | Para |
|-----------|------|
| `brains` | Cerebros independientes |
| `brain_pages` | Páginas markdown con `[[wikilinks]]` |
| `brain_todos` | Tareas con kanban |
| `brain_goals` | Goals, milestones, OKRs con retrospectiva |
| `brain_reminders` | Recordatorios con fecha/hora |
| `brain_journal` | Diario |
| `brain_deliverables` | Entregables versionados |
| `brain_files` | Archivos adjuntos |
| `brain_tags`, `brain_domains` | Organización |
| `brain_page_versions` | Historial de cambios |
| `brain_log` | Bitácora con trazabilidad (agent + user) |

### Scripts

| Script | Uso |
|--------|-----|
| `brain_web.py` | Servidor web live con 7 secciones |
| `brain.py` | Cliente Python para agentes |
| `sync.py` | Export a markdown local |
| `graph.py` | Graph HTML standalone |

---

## Autor

Alvaro L. — [@alvarolizama](https://github.com/alvarolizama)
