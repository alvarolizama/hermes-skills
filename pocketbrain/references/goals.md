# PocketBrain — Goals, Milestones & OKRs

## Tipos

| Tipo | ¿Qué es? | ¿Tiene progreso? | ¿Deadline? |
|------|----------|-----------------|------------|
| `goal` | Resultado deseado | ✅ 0-100% | Opcional |
| `milestone` | Checkpoint binario | ❌ | ✅ recomendado |
| `okr` | Objetivo + key results | ❌ (los KRs sí) | Opcional |

## Flujo

```
planned → active → done (con retrospectiva opcional)
                → cancelled (con retrospectiva opcional)
```

## Uso

```python
# Milestone con deadline
brain.create_goal("MVP en staging", type="milestone", deadline="2026-07-15")

# Goal con progreso
g = brain.create_goal("Reducir errores 50%", type="goal", progress=0)
brain.update_goal(g["id"], progress=60, status="active")

# OKR con key results anidados
okr = brain.create_goal("Ser #1 en rendimiento", type="okr")
brain.create_goal("Latency <100ms", type="goal", parent_id=okr["id"], progress=0)
brain.create_goal("Uptime 99.9%", type="goal", parent_id=okr["id"], progress=0)

# Cerrar con retrospectiva
brain.complete_goal(g["id"], retrospective="Entregado a tiempo. Buen trabajo.")
brain.cancel_goal(g["id"], retrospective="Cambio de prioridades. Se retoma Q4.")

# Ver árbol jerárquico
tree = brain.get_goal_tree()
# → OKR "Ser #1" con 2 key results anidados

# Listar
brain.list_goals(status="active")
brain.list_goals(type="milestone")
brain.list_goals(project_slug="proyecto-x")
```

## Vincular con otras entidades

```python
# Goal vinculado a proyecto
brain.create_goal("Lanzar", type="milestone", project_slug="proyecto-x")

# Todo vinculado a goal
brain.create_todo("Setup CI/CD", domain="bravo", goal_id=goal_id)

# Deliverable vinculado a goal
brain.create_deliverable("proyecto-x", file, goal_id=goal_id)
```
