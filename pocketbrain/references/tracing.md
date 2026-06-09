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

## Qué se registra

TODAS las operaciones: `create_page`, `create_todo`, `update_page`, `move_todo`,
`complete_todo`, `create_goal`, `complete_goal`, `journal_write`, `create_reminder`,
`create_deliverable`, `attach_file`, `archive_page`, `delete_page`, etc.

## Estructura del log

```json
{
  "action": "create",
  "description": "Todo: Revisar PR de auth",
  "page": "abc123",
  "details": {
    "agent": "chaos-manager",
    "requested_by": "alvaro"
  }
}
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
