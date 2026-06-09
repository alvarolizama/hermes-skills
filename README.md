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

Cliente genérico para interactuar con la API REST de PocketBase. Maneja autenticación, CRUD de colecciones y registros, archivos, realtime SSE, y más.

```python
from pb import quick_pb
pb = quick_pb()
records = pb.list('mi_coleccion', filter="status='active'")
```

Variables de entorno requeridas: `POCKETBASE_HOST`, `POCKETBASE_EMAIL`, `POCKETBASE_PASSWORD`.

---

## `pocketbrain` — Segundo Cerebro Digital

Knowledge base multi-cerebro sobre PocketBase. 12 colecciones interconectadas con trazabilidad completa.

### Servidor Web Live

```bash
python3 brain_web.py --brain personal
# → http://localhost:8080
```

7 secciones navegables con diseño limpio:

![Projects](screenshots/projects.png)

---

### Kanban de Tareas

Flujo completo: backlog → this week → today → in progress → done. Drag & drop entre columnas.

![Kanban](screenshots/kanban.png)

---

### Graph de Conexiones

Visualización de todas las relaciones entre páginas, goals, tareas, entregables y recordatorios.

![Graph](screenshots/graph.png)

---

### Desde el Agente

```python
from brain import Brain
brain = Brain('personal')

# Conocimiento
brain.create_page("Tema", body="## Ideas\n...", page_type="concept")
brain.search("machine learning")     # case-insensitive, rankeado

# Tareas
brain.create_todo("Revisar PR", domain="bravo")
brain.todos(status="today")
brain.move_todo(id, "done")

# Goals con retrospectiva
brain.create_goal("Lanzar MVP", type="milestone", deadline="2026-09-30")
brain.complete_goal(id, retrospective="Entregado a tiempo.")

# Proyectos con todo conectado
brain.create_page("App Móvil", page_type="project")
brain.create_deliverable("app-movil", file, title="Specs", version="v1")

# Diario
brain.journal_write("## Hoy\n- Avancé en [[proyecto-x]]", mood="great")

# Recordatorios
brain.create_reminder("Reunión", date="2026-06-15", time="10:00")

# Exportar a markdown
# python3 sync.py --brain personal --full
```

### 12 Colecciones

| Colección | Para |
|-----------|------|
| `brains` | Cerebros independientes (personal, bravo, proyectos...) |
| `brain_pages` | Páginas markdown con `[[wikilinks]]` |
| `brain_todos` | Tareas con kanban |
| `brain_goals` | Goals, milestones, OKRs con retrospectiva |
| `brain_reminders` | Recordatorios con fecha/hora |
| `brain_journal` | Diario (una entrada por día) |
| `brain_deliverables` | Entregables versionados |
| `brain_files` | Archivos adjuntos |
| `brain_tags`, `brain_domains` | Organización |
| `brain_page_versions` | Historial de cambios |
| `brain_log` | Bitácora con trazabilidad (agente + usuario) |

### Scripts

| Script | Uso |
|--------|-----|
| `brain_web.py` | Servidor web live |
| `brain.py` | Cliente Python para agentes |
| `sync.py` | Export a markdown local |
| `graph.py` | Graph HTML standalone |

---

## Autor

Alvaro L. — [@alvarolizama](https://github.com/alvarolizama)
