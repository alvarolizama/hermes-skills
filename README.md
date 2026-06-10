# Hermes Skills

Skills para [Hermes Agent](https://github.com/NousResearch/hermes-agent).

## Instalacion

```bash
hermes skills tap add git@github.com:alvarolizama/hermes-skills.git
hermes skills install pocketbase
hermes skills install pocketbrain
```

---

## `pocketbase` — Cliente PocketBase API

Cliente generico para interactuar con la API REST de PocketBase. **No lee variables de entorno.**
Recibe `host`, `email`, `password` como parametros explicitos. Cada skill consumidor
carga sus propias env vars y las pasa.

```python
from pb import quick_pb
pb = quick_pb('http://localhost:8090', 'admin@example.com', 'secret')
records = pb.list('mi_coleccion', filter="status='active'")
```

Ver [`pocketbase/README.md`](pocketbase/README.md) para documentacion completa de la API (auth, records, files, backups, batch, realtime).

---

## `pocketbrain` — Segundo Cerebro Digital

Knowledge base multi-contexto sobre PocketBase. 12 colecciones, servidor web live,
trazabilidad completa.

Ver [`pocketbrain/README.md`](pocketbrain/README.md) para screenshots, flujos de uso por scripts,
flujos de conocimiento y configuración completa.

### Quick Start

```bash
# 1. Crear colecciones (una vez)
cd pocketbrain/scripts
python3 -c "from brain import _pocketbrain_pb, setup_contexts; setup_contexts(_pocketbrain_pb())"

# 2. Servidor web live
python3 brain_web.py --context personal --port 8899
# → http://localhost:8899

# 3. Exportar a markdown
python3 sync.py --context personal --full
```

### Desde el Agente

```python
from brain import Brain

brain = Brain('personal')

# Páginas, tareas, goals, diario, recordatorios
brain.create_page("Tema", body="## Ideas\n...", page_type="concept")
brain.create_todo("Revisar PR", domain="projects")
brain.create_goal("Lanzar MVP", type="milestone", deadline="2026-09-30", project_slug="app-movil")
brain.journal_write("## Hoy\n- Avance en [[proyecto-x]]")
brain.create_reminder("Reunión", date="2026-12-25", time="10:00")
```

---

## Autor

Alvaro L. — [@alvarolizama](https://github.com/alvarolizama)
