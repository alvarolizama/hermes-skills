# PocketBrain — Trazabilidad

Cada acción registra quién (agente) y para quién (usuario).
Los detalles se guardan en `brain_log.details` (JSON).

## Configuración por perfil

```python
# Chaos Manager → cerebro personal
brain = Brain('personal', agent='chaos-manager', user='alvaro')

# Project Manager → cerebro proyectos
brain = Brain('projects', agent='project-manager', user='alvaro')

# Bravo Manager → cerebro bravo
brain = Brain('bravo', agent='bravo-manager', user='alvaro')
```

El `log()` se llama automáticamente desde todos los métodos. No hay que hacer nada extra.
Cada entrada de `brain_log` incluye `details.agent` y `details.requested_by`.

## Qué se registra

TODAS las operaciones que modifican datos: `create_page`, `create_todo`, `update_page`,
`move_todo`, `complete_todo`, `cancel_todo`, `start_todo`, `create_goal`, `complete_goal`,
`cancel_goal`, `update_goal`, `journal_write`, `create_reminder`, `complete_reminder`,
`create_deliverable`, `version_deliverable`, `attach_file`, `archive_page`, `delete_page`,
`ingest_file`, `create_brain`, `update_schema`, y `lint`.

## Estructura del log

```json
{
  "id": "eyw389xh82l9u6r",
  "action": "create",
  "description": "Todo: Revisar PR de auth",
  "page": "abc123",
  "brain": "5qd0l3i63bbj68k",
  "details": {
    "agent": "chaos-manager",
    "requested_by": "alvaro"
  }
}
```
```

## Consultas

```python
# Últimas acciones
logs = brain.recent_logs(20)

# Filtrar por tipo
brain.pb.list('brain_log', filter="(action='update')", sort='-created')

# Acciones sobre una página
brain.pb.list('brain_log', filter="(page='abc123')", sort='-created')
```
