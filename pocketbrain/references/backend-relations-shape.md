# Backend relations shape — `expand=related_pages`

PocketBase devuelve `related_pages` de formas distintas según el tipo de relación y la query. `brain.py` y `brain_web.py` deben manejar ambas.

## Shapes observadas

### 1. Dict único (relación 1:N efectiva)

Cuando `related_pages` es `maxSelect: null` pero el registro solo tiene un vínculo, PocketBase puede devolver un dict expandido:

```json
{
  "expand": {
    "related_pages": {
      "id": "49e3859md4w8qyo",
      "slug": "pocketbrain",
      "title": "PocketBrain",
      "page_type": "project"
    }
  }
}
```

### 2. Lista de dicts

Si hay múltiples relaciones, o si el campo se expande en ciertos endpoints, llega como lista:

```json
{
  "expand": {
    "related_pages": [
      {"id": "...", "slug": "pocketbrain", ...}
    ]
  }
}
```

### 3. String de IDs

A veces `related_pages` es un string o lista de IDs sin expand:

```json
{
  "related_pages": "49e3859md4w8qyo"
}
```

## Helper recomendado

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

## Donde aplica en `brain_web.py`

- `get_goals()` → `page`, `page_slug`
- `get_todos()` → `page_slug`, `goal_id`, `goal_title`
- `get_deps()` → `page_slug`
- `get_files()` → `page_slug`
- `get_reminders()` → `page_slug`
- `get_journal()` → `page_slug`

Síntoma del bug: project detail muestra Goals 0 / Todo 0 / Reminders 0 aunque existan datos relacionados. El fix fue aplicado en `brain_web.py` v2.24.1 en `get_goals`, `get_todos`, `get_deps`, `get_files`, `get_reminders`, `get_journal`.
