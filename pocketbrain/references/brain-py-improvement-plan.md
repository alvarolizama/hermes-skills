# Plan de mejora para `brain.py`

## Estado actual

`brain.py` es el cliente Python de PocketBrain. Tiene ~1900 líneas y mezcla responsabilidades: CRUD de páginas, gestión de proyectos/goals/todos/reminders/journal, schema, audit (lint), ingest de archivos, historial de versiones, búsqueda local, y helpers de relaciones.

## Problemas identificados

1. **Consumo inconsistente de `expand`**: el código asume que `related_pages` siempre es una lista, pero PocketBase lo devuelve como `dict` único para relaciones 1:N. Ya se parcheó en `brain_web.py`, pero `brain.py` no tiene helper centralizado.
2. **Mezcla de page_types con semánticas duplicadas**: `todo`, `goal`, `milestone`, `okr`, `reminder`, `journal`, `file`, `deliverable` conviven con `entity`, `concept`, etc. El campo `page_type` se usa tanto para tipos de conocimiento como para tipos de ejecución.
3. **`create_page` monolítica**: acepta ~25 parámetros opcionales. Es fácil olvidar propagar campos (ej. `content`, `version`, `file_type`) y difícil de testear.
4. **Relaciones a proyectos son ad-hoc**: `page_slug` y `project_slug` se pasan manualmente a `create_todo`/`create_goal`/`create_reminder`, pero `journal` necesita un hack post-creación en `seed.py`.
5. **No hay tests ni type safety real**: la API es dinámica, los errores de PocketBase se detectan en runtime.
6. **Ingest de archivos usa `subprocess curl`**: fragilidad con credenciales y escaping.
7. **`search()` trae TODO el cerebro a memoria**: no escala.
8. **`search()` trae TODO el cerebro a memoria**: no escala.
9. **Trabajo sin UI poco documentado**: el skill funciona sin `brain_web.py`, pero SKILL.md no destaca este modo de uso. El agente puede operar 100% desde conversación markdown usando `Brain()` directamente.

## Propuesta de mejora

### 1. Helper central de relaciones

```python
def _related_from_expand(page: dict) -> list:
    rel = page.get('expand', {}).get('related_pages') or page.get('related_pages') or []
    if isinstance(rel, dict):
        return [rel]
    if isinstance(rel, str):
        return [{'id': rel}] if rel else []
    return rel if isinstance(rel, list) else []

def _first_related_slug(page: dict) -> str:
    rels = _related_from_expand(page)
    return rels[0].get('slug', '') if rels else ''
```

Eliminar la decena de copy-paste `rel = p.get('expand', {}).get('related_pages', [])`.

### 2. Clases de modelo o dataclasses

Separar:
- `Page` (conocimiento): entity, concept, comparison, query, raw, note, idea, plan
- `Task` (ejecución): todo, goal, milestone, okr, reminder
- `JournalEntry`
- `FileRecord`

Cada una con su builder/validador. `create_page` se mantiene como constructor interno, pero el agente usa métodos específicos.

### 3. API de relaciones explícita

```python
brain.link_page('escribir-readme-de-pocketbrain-v2', 'pocketbrain')
brain.unlink_page('escribir-readme-de-pocketbrain-v2', 'pocketbrain')
brain.get_page_links('pocketbrain')  # -> list[Page]
```

Esto reemplaza el paso de `page_slug` como parámetro escondido.

### 4. Refactor de `create_page`

Dividir en:
- `_build_page_payload(page_type, **kwargs)`
- `_create_page_raw(payload)`
- `_link_page_to(page_id, target_ids)`

Validar schema con pydantic opcional.

### 5. Tests unitarios

- `pytest` con mock de `PB`
- Tests para cada helper de relaciones (dict/list/str/vacío)
- Tests para `extract_wikilinks`
- Tests para `suggest_page_type`
- Tests para `lint()`

### 6. Search server-side

Usar filtro de PocketBase sobre `title` y `body` en vez de traer todo:

```python
filter = "title ~ {:query} || body ~ {:query}".format(query=query)
```

### 7. Ingest de archivos sin curl

Subir con `requests`/`urllib` usando el token ya autenticado, o usar `pb.create` con multipart nativo si `pb.py` lo soporta.

### 8. Hooks de versionado automático

Usar reglas de PocketBase (collections rules) o un hook JSVM para crear `brain_page_versions` en `afterUpdate`, eliminando la lógica manual.

### 9. Documentación de contrato backend-frontend

Definir en `references/backend-frontend-contract.md`:
- shape de `related_pages` en la respuesta
- qué campos exponen `/api/goals`, `/api/todos`, etc.
- convención de nombres (`page_slug`, `goal_id`)

## Roadmap sugerido

| Fase | Tarea | Tiempo estimado |
|------|-------|-------------------|
| 1 | Helper `_related_from_expand` + reemplazar copy-paste en `brain.py` y `brain_web.py` | 2h |
| 2 | Tests unitarios para relaciones y wikilinks | 2h |
| 3 | API `link_page`/`unlink_page`/`get_page_links` | 3h |
| 4 | Refactor `create_page` + dataclasses Page/Task/Journal/File | 4h |
| 5 | Search server-side | 1h |
| 6 | Ingest de archivos sin curl | 2h |
| 7 | Hook de versionado automático en PocketBase | 3h |
| 8 | Documentar contrato backend-frontend | 1h |
| 9 | Documentar uso headless (sin UI) | 1h |

## Beneficios esperados

- Menos bugs de relaciones en frontend.
- Código testeable y mantenible.
- Seed.py más limpio sin hacks post-creación.
- Mejor performance en search.
- Seguridad: no exponer tokens en subprocess.
