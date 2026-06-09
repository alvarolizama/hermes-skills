# PocketBrain — Workflows

Guía rápida de setup, uso y flujos de trabajo comunes.

---

## Setup inicial

### 1. Variables de entorno (`~/.hermes/.env`)

```bash
POCKETBASE_HOST=http://localhost:8090
POCKETBASE_EMAIL=admin@example.com
POCKETBASE_PASSWORD=***
```

### 2. Crear colecciones en PocketBase

```python
from pb import quick_pb
from brain import setup_brains

pb = quick_pb()
setup_brains(pb)  # crea las 11 colecciones
```

### 3. Crear tu primer cerebro

```python
from brain import Brain

brain = Brain('personal')
brain.create_brain(label='Cerebro Personal', description='Mi conocimiento')
brain.orient()  # carga el contexto
```

---

## Scripts disponibles

| Script | Comando | Qué hace |
|--------|---------|----------|
| `brain_web.py` | `python3 brain_web.py` | Servidor web live en `http://localhost:8080` |
| `brain_web.py` | `python3 brain_web.py --output ~/wiki.html` | Exportar HTML estático |
| `sync.py` | `python3 sync.py` | Exportar todos los cerebros a markdown |
| `sync.py` | `python3 sync.py --brain personal` | Exportar un cerebro |
| `sync.py` | `python3 sync.py --full --output ~/wiki` | Sync completo a directorio custom |

---

## Workflows comunes

### 📝 Crear una página de conocimiento

```
Usuario: "Investiga sobre X y guárdalo"
Agente:  brain.create_page(title="X", body="## X\n\n...", page_type="concept", domain="...", tags=[...])
```

### 📄 Ingestar un PDF

```
Usuario: [adjunta PDF]
Agente:  1. brain.ingest_file(filepath, title="...")  → sube el PDF, crea página raw
         2. Extrae texto del PDF, lo convierte a markdown
         3. brain.update_page(slug, body=markdown)     → llena el body
```

### 📋 Gestionar tareas

```
Usuario: "Agrega 'Revisar PR' a mis tareas de bravo"
Agente:  brain.create_todo("Revisar PR", domain="bravo")

Usuario: "¿Qué tengo para hoy?"
Agente:  brain.todos(status="today")

Usuario: "Marca 'Revisar PR' como done"
Agente:  brain.complete_todo(todo_id)
```

### 🎯 Crear un OKR con key results

```
Usuario: "Crea un OKR para Q3: mejorar rendimiento"
Agente:  okr = brain.create_goal("Mejorar rendimiento", type="okr")
         brain.create_goal("Latency <100ms", type="goal", parent_id=okr["id"], progress=0)
         brain.create_goal("Uptime 99.9%", type="goal", parent_id=okr["id"], progress=0)
```

### 📁 Crear un proyecto con todo

```
Usuario: "Crea el proyecto 'App Móvil' con goals y tareas"
Agente:  brain.create_page("App Móvil", body="## Objetivos\n- MVP en 3 meses", page_type="project")
         brain.create_goal("Lanzar MVP", type="milestone", project_slug="app-movil", deadline="2026-09-30")
         brain.create_todo("Diseñar UI", domain="projects", page_slug="app-movil")
         brain.create_todo("Setup backend", domain="projects", page_slug="app-movil")
```

### 📓 Escribir en el diario

```
Usuario: "Anota en el diario que hoy avancé el PR"
Agente:  brain.journal_write("## Hoy\n\n- Avancé el PR de auth. Ver [[auth-refactor]]", mood="great")
```

### 📊 Ver el estado de un proyecto

```
Usuario: "¿Cómo va App Móvil?"
Agente:  page = brain.get_page("app-movil")
         goals = brain.list_goals(project_slug="app-movil")
         todos = brain.todos()
         # Muestra el progreso
```

### 🔍 Auditar el cerebro

```
Usuario: "Revisa si hay links rotos"
Agente:  report = brain.lint()
         # report["broken_links"], report["orphans"], report["low_confidence"]
```

### 🖥️ Ver el wiki en el navegador

```bash
python3 brain_web.py --brain personal
# Abre http://localhost:8080
# Navega entre: Todo | Goals | Journal | Proyectos | Wiki | Graph
# Cambia de cerebro con el dropdown superior
```

### 📤 Exportar a markdown

```bash
python3 sync.py --brain personal --full
# → ~/brain-sync/personal/
#   SCHEMA.md | index.md | log.md | todos.md
#   entities/ | concepts/ | projects/ | raw/
#   journal/journal.md | files/
```

---

## Flujo diario típico

```
Mañana:
  1. brain.journal_write("## Planning\n- Hoy: [[tarea-1]], [[tarea-2]]")
  2. brain.todos(status="today")  → ver qué hay para hoy

Durante el día:
  3. brain.start_todo(id)  → mover a in progress
  4. brain.journal_write("Avance en [[proyecto-x]]", append=True)
  5. brain.complete_todo(id)  → marcar como done

Fin de día:
  6. brain.journal_write("## Review\n- Completado: ...\n- Pendiente: ...", append=True)
  7. python3 brain_web.py  → revisar el tablero visual
```

---

## Flujo semanal

```
Lunes:
  - brain.journal_write("## Semana X - Planning")
  - brain.create_todo(...)  → planear la semana
  - Revisar goals: brain.list_goals(status="active")
  - Mover tareas de backlog → this week

Viernes:
  - brain.lint()  → auditar contenido
  - brain.journal_write("## Retrospectiva semanal")
  - python3 sync.py  → backup a markdown
```

---

## Cambiar entre cerebros

```python
# Desde el agente
brain_personal = Brain('personal')
brain_bravo = Brain('bravo')
brain_projects = Brain('projects')

# Desde la web
# Usa el dropdown superior en http://localhost:8080
```

---

## Atajos rápidos

```python
# Búsqueda (case-insensitive, multi-palabra, rankeada)
brain.search("machine learning transformers")

# Agregar info a una página existente
brain.append_to_page("mantrams", "- Nuevo mantram: X", heading="2026-06-10")

# Ver historial de cambios de una página
brain.get_history("transformer-architecture")

# Ver árbol de goals/OKRs
brain.get_goal_tree(project_slug="proyecto-x")

# Adjuntar archivo a una página
brain.attach_file("proyecto-x", "/path/doc.pdf", name="Especificación", file_type="pdf")

# Crear entregable versionado
brain.create_deliverable("proyecto-x", "/path/v1.pdf", title="API Docs", version="v1", status="draft")
brain.version_deliverable(id, "/path/v2.pdf", "v2")
```
