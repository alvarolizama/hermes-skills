# Schema Refactor Patterns

Patrones y convenciones para refactorizar el schema de `brain_pages` sin romper relaciones ni duplicar campos.

## Convención de nombres

- **Siempre usar `snake_case` con underscore.** PocketBase acepta espacios en valores de `select`, pero nosotros usamos underscore para consistencia y evitar problemas en filtros y URLs.
- **Campos compartidos no llevan prefijo.** Si un campo aplica a múltiples tipos, es genérico:
  - `status`
  - `owner`
  - `deadline`
  - `date`
  - `time`
  - `done`
  - `done_date`
  - `mood`
  - `project` (relation al proyecto padre)
- **Campos específicos de un tipo llevan prefijo del tipo.** Ejemplos:
  - `todo_goal` (un todo puede estar asociado a un goal)
  - `file_type`, `file_version`, `file_attachment`
  - `kb_confidence`, `kb_contested`, `kb_contradictions`, `kb_source_url`, `kb_source_sha256`

> **Regla de oro del usuario:** si un campo se repite en varios tipos, pasa a ser genérico. Nunca uses espacios en valores de `select`; siempre `snake_case` con underscore.

## Decidir si un campo es compartido o prefijado

| ¿Se repite en 2+ tipos? | Acción | Ejemplo |
|---------------------------|--------|---------|
| Sí | Campo genérico compartido | `status`, `deadline`, `project` |
| No | Campo con prefijo de tipo | `todo_goal`, `file_attachment` |

## Relaciones por contexto

- Todas las colecciones hijas apuntan a `brain_contexts` mediante el campo `context`.
- Nunca usar `brain` como nombre de campo de relación en un schema nuevo. El nombre actualizado es `context`.
- Las relaciones padre (ej. un todo a un proyecto) usan el campo genérico `project` cuando es compartido, o un campo tipado como `todo_goal` cuando es específico.

## Variables de entorno

- Credenciales de PocketBase: `POCKETHOST_HOST`, `POCKETHOST_EMAIL`, `POCKETHOST_PASSWORD`.
- Contexto default del agente: `POCKETBRAIN_CONTEXT` (sin cambios).

## Mass rename checklist

Al renombrar campos o colecciones, verificar:

1. Schema en `BRAIN_SCHEMA`.
2. Filtros PB que usan el campo viejo.
3. Payloads de creación/actualización.
4. Respuestas de endpoints.
5. Vistas JS que lean el campo.
6. Scripts auxiliares (`sync.py`, `graph.py`, `seed.py`).
7. Documentación y ejemplos.

## Ejemplo de schema reducido

```python
{"name": "brain_pages", "type": "base", "fields": [
    # Core
    {"name": "title", "type": "text", "required": True},
    {"name": "slug", "type": "text", "required": True, "unique": True},
    {"name": "context", "type": "relation", "collectionId": "brain_contexts", "maxSelect": 1},
    {"name": "page_type", "type": "select", "required": True,
     "values": ["entity", "concept", "comparison", "query", "raw",
                "project", "plan", "note", "idea", "todo",
                "goal", "milestone", "reminder", "journal", "file"]},
    {"name": "body", "type": "text"},
    {"name": "summary", "type": "text"},
    {"name": "tags", "type": "relation", "collectionId": "brain_tags"},
    {"name": "related_pages", "type": "relation", "collectionId": "brain_pages"},
    {"name": "archived", "type": "bool"},

    # Shared
    {"name": "status", "type": "select", "values": ["planned", "active", "completed", "cancelled", "backlog", "this_week", "today", "in_progress", "done"]},
    {"name": "owner", "type": "text"},
    {"name": "deadline", "type": "date"},
    {"name": "date", "type": "date"},
    {"name": "time", "type": "text"},
    {"name": "done", "type": "bool"},
    {"name": "done_date", "type": "date"},
    {"name": "mood", "type": "text"},
    {"name": "project", "type": "relation", "collectionId": "brain_pages", "maxSelect": 1},

    # Type-specific
    {"name": "todo_goal", "type": "relation", "collectionId": "brain_pages", "maxSelect": 1},
    {"name": "file_type", "type": "text"},
    {"name": "file_version", "type": "text"},
    {"name": "file_attachment", "type": "file", "maxSelect": 1},
    {"name": "kb_confidence", "type": "select", "values": ["high", "medium", "low"]},
    {"name": "kb_contested", "type": "bool"},
    {"name": "kb_contradictions", "type": "text"},
    {"name": "kb_source_url", "type": "url"},
    {"name": "kb_source_sha256", "type": "text"},
]}
```

## Migración de datos

1. Hacer backup/export con `sync.py`.
2. Borrar **colecciones** antiguas (ver pitfall abajo).
3. Recrear con `setup_contexts()`.
4. Crear contextos con `Brain.create_context()` si se partió de schema vacío.
5. Insertar seed data densa con `seed.py`.
6. Verificar visualmente que la UI carga datos y relaciones correctamente.

### ⚠️ Pitfall: `nuke_context()` NO borra el schema

`nuke_context(pb, confirm='YES_DELETE_ALL')` solo **trunca registros** de las colecciones (`brain_pages`, `brain_tags`, etc.). Las colecciones y sus campos antiguos siguen existiendo en PocketBase. Si renombraste campos o cambiaste el schema, `setup_contexts()` no actualizará las colecciones existentes: dirá "ya existen" y dejará el schema viejo.

**Para un wipe real del schema**, borrar las colecciones explícitamente antes de recrear:

```python
for col in ['brain_log', 'brain_page_versions', 'brain_pages', 'brain_tags', 'brain_contexts']:
    pb._request('DELETE', f'/api/collections/{col}')
setup_contexts(pb)
```

Luego verifica en el Admin UI de PocketBase que los campos antiguos (`brain`, `domain`, `confidence`, etc.) desaparecieron y los nuevos (`context`, `kb_*`, compartidos) están presentes.

### ⚠️ Pitfall: relaciones pasadas como slugs en `create_page`

PocketBase requiere IDs (`pbc_xxx`) en los campos `relation`, no slugs. Si `seed.py` o un script de carga pasa `project="migracion-k8s"` o `todo_goal="lanzar-mvp"`, `create_page()` debe resolver esos slugs a IDs **antes** de enviar el payload a PocketBase.

El patrón en `brain.py` es:

```python
relation_fields = {'project', 'todo_goal'}
for rel_key in relation_fields:
    if rel_key in kwargs:
        rel_val = kwargs[rel_key]
        if isinstance(rel_val, str) and rel_val and not rel_val.startswith('pbc_'):
            rel_page = self._get_page(rel_val)
            if rel_page and 'id' in rel_page:
                kwargs[rel_key] = rel_page['id']
            else:
                kwargs[rel_key] = None
```

Esto permite que el API de alto nivel use slugs legibles (como en `seed.py` y en ejemplos del agente) mientras el backend envía IDs válidos a PocketBase.

### ⚠️ Pitfall: relaciones self/cross-reference en `setup_contexts`

Cuando una colección tiene relaciones a sí misma (ej. `brain_pages.related_pages`) o a colecciones creadas posteriormente (ej. `brain_page_versions.page` -> `brain_pages`), `setup_contexts()` debe crear las colecciones en **dos pasos**:

1. **Paso 1**: crear cada colección SIN los campos de relación no resueltos.
2. **Paso 2**: PATCH cada colección para agregar los campos diferidos, usando los `pbc_xxx` IDs reales ya conocidos.

Si intentas crear `brain_pages` con `related_pages` apuntando a `brain_pages` antes de que exista, PocketBase responde:

```
{"data":{"fields":{"22":{"collectionId":{"code":"validation_field_relation_missing_collection",
  "message":"The relation collection doesn't exist."}}}},"message":"Failed to create collection.","status":400}
```

La solución es mantener un registro `SELF_REF_FIELDS` con los campos diferidos por colección, omitirlos en la creación inicial, y PATCHearlos después. Ver `brain.py` `setup_contexts()` para la implementación actual.

## Subagentes y fases

Un refactor de schema completo (brain.py + brain_web.py + sync.py + graph.py + vistas JS + seed.py) excede la ventana de atención de un solo subagente. Dividir en fases:

1. Schema y backend (`brain.py`, `brain_web.py`, `sync.py`, `graph.py`) — validar con `python3 -m py_compile`.
2. Frontend JS (`views/*.js`) — validar con `node --check`.
3. Seed data (`seed.py`) — ejecutar contra base limpia.
4. Deploy + validación visual — levantar `brain_web.py` y verificar tabs.

Si un subagente se atasca, continuar manualmente con lecturas directas y scripts de reemplazo controlados.

## Validación post-refactor

Después de cualquier cambio de schema o relaciones:

1. `python3 -m py_compile brain.py brain_web.py sync.py graph.py seed.py`
2. `node --check app.js router.js store.js api.js markdown.js components/*.js views/*.js`
3. Listar colecciones en PocketBase y confirmar que no quedan campos legacy.
4. Crear un registro de prueba de cada `page_type` con relaciones.
5. Levantar `brain_web.py` y verificar que la UI renderiza counts, tabs y relaciones sin errores de consola.
