# CLI Migration: brain → context

## Parámetros de línea de comandos

Todos los scripts CLI usan `--context` (no `--brain`):

| Script | Comando ejemplo |
|--------|-----------------|
| `brain_web.py` | `python3 brain_web.py --context personal --port 8899` |
| `graph.py` | `python3 graph.py --context personal` |
| `sync.py` | `python3 sync.py --context personal --full` |

## Variables internas

| Ámbito | Antes | Ahora |
|---------|-------|-------|
| Python global | `BN = "personal"` | `CTX = "personal"` |
| Python local | `brain_name` | `context_name` |
| Query param | `?brain=personal` | `?context=personal` |
| Endpoint | `GET /api/brain` | `GET /api/brains` |
| JS variable | `currentBrain` | `currentContext` |
| Colección PB | `brains` | `contexts` (campo `relation` en hijas sigue como `brain`) |

## Checklist de mass rename

Cuando renombrar una variable/colección en todo el codebase, verificar 4 clases de referencias:

1. **String constants**: `pb.collection('brains')` → `pb.collection('contexts')` — strings con nombre de colección
2. **Assignment RHS**: `self.context_name = brain_name` — lado derecho no renombrado
3. **Attribute access**: `brain.context_name` (cuando la variable se llama `brain` pero el atributo cambió a `context_name`)
4. **Local variable**: `brain.get('schema_config')` dentro de un método donde la variable local se renombró a `context`

**Verificación post-rename:** ejecutar el script y seguir el traceback. Un grep rápido falla con nombres que aparecen como substring de otros identificadores (`brain` dentro de `brain_pages`).

## Vinculación de datos por proyecto

Los items (goals, todos, reminders, journal) deben tener el campo `page` (relation a `brain_pages`) vinculado al proyecto para que:
- El dropdown de filtro por proyecto en TODOs/Goals muestre el proyecto
- La vista de proyecto muestre los tabs con contenido (Goals, Kanban, Recordatorios, etc.)
- El graph del proyecto muestre los nodos conectados

**Script de vinculación por keywords:**
```python
for t in todos:
    if any(kw in t['title'].lower() for kw in ['vuelo', 'japon', 'tokyo', 'kyoto']):
        pb.update('brain_todos', t['id'], {'page': project_page_id})
```

Items creados sin `page` aparecen en "Sin proyecto" en el dropdown. No aparecen en la vista de proyecto.
