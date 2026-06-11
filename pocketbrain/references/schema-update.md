# PocketBrain — Schema Updates

Como actualizar colecciones de PocketBase que ya existen, cuando el BRAIN_SCHEMA cambia.

## El problema

setup_contexts() verifica si una coleccion existe (pb.get_collection(name)) y si ya existe, la salta. No actualiza campos nuevos ni values de select.

## Soluciones

### Opcion 1: Agregar campos uno por uno

```python
col = pb.get_collection('brain_pages')
existing_names = {f['name'] for f in col['fields']}

nuevos_campos = [
    {'name': 'status', 'type': 'select', 'values': ['backlog', 'done', 'planned'], 'maxSelect': 1},
    {'name': 'file_type', 'type': 'select', 'values': ['pdf', 'image', 'doc'], 'maxSelect': 1},
]

for field in nuevos_campos:
    if field['name'] not in existing_names:
        pb.update_collection(col['id'], {'fields': col['fields'] + [field]})
        col = pb.get_collection('brain_pages')  # refresh
```

### Opcion 2: Actualizar values de un select existente

Para cambiar los values de page_type (agregar nuevos tipos):

```python
col = pb.get_collection('brain_pages')
for f in col['fields']:
    if f['name'] == 'page_type':
        f['values'] = ['entity', 'concept', 'comparison', ..., 'nuevo_tipo']
        break

pb.import_collections([{
    'id': col['id'],
    'name': 'brain_pages',
    'type': 'base',
    'fields': col['fields'],
}], delete_missing=False)
```

### Opcion 3: Borrar y recrear (solo para datos descartables)

```python
pb.delete_collection('brain_pages')
from brain import setup_contexts
setup_contexts(pb)  # recrea con BRAIN_SCHEMA actual
```

## Pitfalls

- **collectionId en relaciones**: cuando agregas un campo relation via update_collection, collectionId debe ser el ID interno (pbc_xxx), no el nombre. Usa pb.get_collection('brain_pages')['id'] para obtenerlo.
- **Self-ref fields**: campos que referencian a su propia coleccion (ej. brain_pages.related_pages) no se pueden crear en el POST inicial. Deben agregarse con PATCH post-creacion.
