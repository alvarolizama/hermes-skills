# Migración a context-only

PocketBrain ya no usa `domain` como concepto funcional. El **contexto** (`Brain('nombre')`) es el único silo organizacional.

## Qué se quitó

- Colección `brain_domains` del schema.
- Campo `domain` de `brain_pages`.
- Parámetro `domain` de `create_page()`, `create_todo()`, `ingest_text()`, `list_pages()`, `todos()`, `search()`.
- Método `get_or_create_domain()` y cache `_domain_cache`.
- UI: labels de dominio en tarjetas de proyecto, todo, wiki, project-detail.

## Qué se conservó por compatibilidad

- Datos existentes en PocketBase que tengan `domain` quedan como están; no se migran ni borran automáticamente.
- Si una colección vieja `brain_domains` aún existe en la instancia, no se usa ni se crea en nuevas instalaciones.

## Impacto en el schema

```python
BRAIN_SCHEMA = {
    "contexts": {...},
    "brain_tags": {...},
    "brain_pages": {...},   # sin campo domain, sin deliverable
    "brain_log": {...},
    "brain_page_versions": {...},
}

CREATION_ORDER = ["contexts", "brain_tags", "brain_pages", "brain_log", "brain_page_versions"]
```

## Impacto en reportes

Los reportes ya no incluyen columna `domain`:

```python
# Antes
{'slug': 'x', 'title': 'X', 'domain': 'proyectos', 'todos_count': 3}

# Ahora
{'slug': 'x', 'title': 'X', 'todos_count': 3}
```

## Lecciones

1. **No tocar schema en producción sin migrar datos.** Si una instancia tiene `brain_domains` poblada, borrar la colección en PocketBase rompe las relaciones de `brain_pages.domain`.
2. **Quitar un campo del schema no limpia datos existentes.** Si se quiere borrar físicamente, hacerlo explícitamente con un script de migración.
3. **Actualizar `CREATION_ORDER` y `DEPENDENCIES` juntos.** Si no, `setup_contexts()` falla por dependencias faltantes.
4. **Quitar también de la UI, no solo del backend.** Los usuarios ven primero la UI; un label huérfano de `domain` genera confusión.
