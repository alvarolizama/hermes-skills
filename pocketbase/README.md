# PocketBase API Client

Cliente genérico para interactuar con la API REST de [PocketBase](https://pocketbase.io/docs/api-records/). Usa `curl` via subprocess, sin dependencias externas.

**No lee variables de entorno.** Recibe `host`, `email`, `password` como parámetros explícitos. Cada skill consumidor carga sus propias env vars y las pasa.

```python
from pb import PB, quick_pb

# Conexión explícita — sin magia de env vars
pb = quick_pb('http://localhost:8090', 'admin@example.com', 'secret')
records = pb.list('mi_coleccion', filter="status='active'")
```

---

## Quick Start

```bash
# 1. Autenticar y listar registros
cd ~/.hermes/skills/productivity/pocketbase/scripts
python3 -c "
from pb import quick_pb
pb = quick_pb('http://localhost:8090', 'admin@example.com', 'secret')
print(pb.list('contexts'))
"
```

```python
# 2. Desde cualquier script
import sys, os
sys.path.insert(0, os.path.expanduser(
    '~/.hermes/skills/productivity/pocketbase/scripts'))
from pb import quick_pb

pb = quick_pb('http://localhost:8090', 'admin@example.com', 'secret')

# Operaciones básicas
pages = pb.list('wiki_pages', filter="page_type='concept'")
page = pb.get('wiki_pages', 'RECORD_ID')
new = pb.create('wiki_pages', {'title': 'Mi página', 'slug': 'mi-pagina'})
pb.update('wiki_pages', 'RECORD_ID', {'title': 'Nuevo título'})
pb.delete('wiki_pages', 'RECORD_ID')
```

---

## Cliente Python (`pb.py`)

### `PB(host, email, password)`

| Método | Descripción |
|--------|-------------|
| `auth()` | Autentica como superusuario, guarda el token internamente |
| `get_token()` | Devuelve el token, auto-autentica si es necesario |
| `refresh_token()` | Refresca el token actual |
| `impersonate(user_id, duration)` | Genera token de impersonación |

### Records

| Método | Descripción |
|--------|-------------|
| `list(collection, **params)` | Lista registros con filtro, sort, paginación |
| `all(collection, **params)` | Lista TODOS los registros (paginación automática) |
| `get(collection, id)` | Obtiene un registro por ID |
| `create(collection, data)` | Crea un registro |
| `update(collection, id, data)` | Actualiza un registro |
| `delete(collection, id)` | Elimina un registro |

Query params útiles para `list()` y `all()`:
- `filter` — ej. `"(title~'abc' && status='published')"`
- `sort` — ej. `"-created"` (DESC)
- `expand` — ej. `"domain,tags"` (relaciones)
- `fields` — ej. `"id,title,slug"` (solo ciertos campos)
- `skipTotal` — mejora performance

### Collections (Admin)

| Método | Descripción |
|--------|-------------|
| `list_collections(**params)` | Lista todas las colecciones |
| `get_collection(name_or_id)` | Obtiene una colección por nombre o ID |
| `create_collection(name, fields, type, rules)` | Crea una colección |
| `update_collection(name_or_id, data)` | Actualiza una colección |
| `delete_collection(name_or_id)` | Elimina una colección |
| `truncate_collection(name_or_id)` | Borra todos los registros |
| `import_collections(collections, delete_missing)` | Import/update batch de colecciones |

### Utilidades

| Método | Descripción |
|--------|-------------|
| `health()` | Verifica que la instancia esté viva |
| `batch(requests)` | Múltiples operaciones en una transacción |
| `get_file_url(collection, record_id, filename)` | URL pública de un archivo |
| `list_logs(**params)` | Logs del sistema |
| `list_backups()` | Lista backups |
| `create_backup()` | Crea backup |
| `restore_backup(name)` | Restaura backup |
| `delete_backup(name)` | Elimina backup |
| `get_settings()` | Obtiene configuración |
| `update_settings(data)` | Actualiza configuración |

### `quick_pb(host, email, password)`

Shortcut que crea un `PB` y lo autentica en un solo paso.

```python
from pb import quick_pb
pb = quick_pb('http://localhost:8090', 'admin@example.com', 'secret')
records = pb.list('mi_coleccion')
```

---

## Operaciones Avanzadas

### Batch (transacciones)

```python
pb.batch([
    {"method": "POST", "url": "/api/collections/posts/records",
     "body": {"title": "Post 1"}},
    {"method": "POST", "url": "/api/collections/posts/records",
     "body": {"title": "Post 2"}},
])
```

### Import de colecciones

Para agregar/modificar campos sin perder los existentes:

```python
col = pb.get_collection("mi_coleccion")
fields = []
for f in col["fields"]:
    new_f = {"name": f["name"], "type": f["type"]}
    if f.get("required"): new_f["required"] = True
    if f.get("values"): new_f["values"] = f["values"]
    if f.get("collectionId"): new_f["collectionId"] = f["collectionId"]
    # Preservar cascadeDelete, maxSelect, etc.
    fields.append(new_f)

fields.append({"name": "nuevo_campo", "type": "text"})

pb.import_collections([{
    "id": col["id"], "name": col["name"],
    "type": col["type"], "fields": fields
}], delete_missing=False)
```

---

## ⚠️ Pitfalls

### Llaves `{` `}` son kriptonita en Hermes

Cualquier tool que escribe archivos o código — `write_file`, `patch`, `skill_manage`, `terminal` con heredoc — se come las llaves `{` y `}` y todo lo que esté entre ellas.

**❌ Se rompe:**
```python
auth = f"Bearer {token}"          # queda: auth = f"Bearer "
url = f"{host}/api"               # queda: url = f"/api"
```

**✅ Funciona:**
```python
auth = "Bearer " + token
url = host + "/api/collections"
auth = "Bearer %s" % token        # % formatting
```

### PATCH de colecciones → usar Import API

El endpoint `PATCH /api/collections/{id}` rechaza actualizaciones de campos. Usar `PUT /api/collections/import` en su lugar (ver ejemplo arriba).

---

## Referencia Completa

Ver [`pocketbase/SKILL.md`](SKILL.md) del skill para documentación completa de la API con ejemplos en curl, incluyendo:

- Autenticación (superusuario, usuario regular, impersonación)
- Reglas de seguridad (`listRule`, `viewRule`, etc.)
- Health check
- CRUD de colecciones y registros
- Subida y descarga de archivos
- Settings, logs, backups
- Realtime (SSE)
- Batch operations
- Workflow de tareas recomendado

**Referencia oficial:** https://pocketbase.io/docs/api-records/
