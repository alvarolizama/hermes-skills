---
name: pocketbase
description: "Interactuar con la API REST de PocketBase usando curl + Python subprocess. Incluye auth, records, collections, files, settings, logs, backups, health, batch, realtime y workflow de tareas."
version: 2.0.0
author: Alvaro L.
platforms: [macos, linux]
metadata:
  source: https://pocketbase.io/docs/api-records/
---

# PocketBase API — curl + Python subprocess

## Variables de entorno y contexto

El módulo `pb.py` **NO lee variables de entorno**. Recibe `host`, `email`, `password` como parámetros explícitos.
Cada skill que lo use carga sus propias variables del `.env` y las pasa.

Ejemplo:
```python
from pb import PB, quick_pb
pb = quick_pb('http://localhost:8090', 'admin@example.com', 'secret')
```

El skill `pocketbase` tradicionalmente usaba `POCKETBASE_HOST`, `POCKETBASE_EMAIL`, `POCKETBASE_PASSWORD`,
pero ahora la responsabilidad de cargar env vars es de cada skill consumidor.

**Referencia oficial:** https://pocketbase.io/docs/api-records/

---

## ⚠️ PITFALL CRÍTICO: Llaves `{` `}` son kriptonita en Hermes

**Cualquier tool que escribe archivos o código** — `write_file`, `patch`, `skill_manage`, `terminal` con heredoc — **se come las llaves `{` y `}` y todo lo que esté entre ellas.** Esto rompe f-strings, `str.format()`, y cualquier string que contenga `{` literal.

### ❌ Esto SE ROMPE
```python
# f-strings: el {token} desaparece
auth = f"Bearer {token}"          # queda: auth = f"Bearer "

# str.format: igual
auth = "Bearer {}".format(token)  # queda: auth = "Bearer "

# Simple concatenación con llave literal
url = f"{host}/api"              # queda: url = f"/api"
```

### ✅ Esto SÍ funciona
```python
# Concatenación simple (sin llaves)
auth = "Bearer " + token
url = host + "/api/collections"

# % formatting (old-style)
auth = "Bearer %s" % token

# Pasar token por variable de entorno
os.environ["T"] = token
subprocess.run(..., env=os.environ)
```

### Regla de oro
**NUNCA uses `{` o `}` en código Python que escribas mediante tools de Hermes.**
Revisa dos veces antes de crear/editar skills, scripts, o archivos de configuración.
Ver `references/hermes-pitfalls.md` para workarounds detallados.

### ⚠️ PATCH de colecciones → usar Import API

El endpoint `PATCH /api/collections/{id}` **rechaza consistentemente** actualizaciones de campos (agregar campos nuevos, modificar valores de select). Devuelve `400: "Failed to load the submitted data due to invalid formatting"`.

✅ **Usar `PUT /api/collections/import` en su lugar:**
```python
col = pb.get_collection("mi_coleccion")

# Construir fields completos preservando TODOS los atributos
fields = []
for f in col["fields"]:
    new_f = {"name": f["name"], "type": f["type"]}
    if f.get("required"): new_f["required"] = True
    if f.get("values"): new_f["values"] = f["values"]  # modificar aquí
    if f.get("collectionId"): new_f["collectionId"] = f["collectionId"]
    # ... preservar cascadeDelete, maxSelect, etc.
    fields.append(new_f)

# Agregar nuevos campos
fields.append({"name": "nuevo_campo", "type": "text"})

# Import (requiere ID de la colección)
pb._request("PUT", "/api/collections/import", data={
    "collections": [{"id": col["id"], "name": col["name"], "type": col["type"], "fields": fields}],
    "deleteMissing": False,
})
```

> **Cuidado:** El import API **sobrescribe** los campos. Si omites un atributo (ej. `autogeneratePattern` del ID, `onCreate`/`onUpdate` de autodate), se pierde. Preservar TODO.

---

---

## 1. Autenticación (Superusuario)

```python
import subprocess, json, os

HOST = os.environ.get('POCKETBASE_HOST', 'http://localhost:8090')
EMAIL = os.environ.get('POCKETBASE_EMAIL', '')
PASSWORD=os.env...RD', '')

result = subprocess.run([
    "curl", "-s", "-X", "POST",
    f"{HOST}/api/collections/_superusers/auth-with-password",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"identity": EMAIL, "password": PASSWORD})
], capture_output=True, text=True)
auth_data = json.loads(result.stdout)
token = auth_data['token']  # ← guarda esto para todas las llamadas siguientes
```

**Response:** `{ "token": "JWT...", "record": { ... } }`

### Autenticación de usuario regular

```python
import os, subprocess, json

HOST = os.environ.get('POCKETBASE_HOST', 'http://localhost:8090')

result = subprocess.run([
    "curl", "-s", "-X", "POST",
    f"{HOST}/api/collections/users/auth-with-password",
    "-H", "Content-Type: application/json",
    "-d", '{"identity": "usuario@email.com", "password": "password123"}'
], capture_output=True, text=True)
```

### Listar métodos de auth disponibles

```python
import os, subprocess

HOST = os.environ.get('POCKETBASE_HOST', 'http://localhost:8090')

result = subprocess.run([
    "curl", "-s", f"{HOST}/api/collections/users/auth-methods"
], capture_output=True, text=True)
```

### Refrescar token

```python
import os, subprocess, json

HOST = os.environ.get('POCKETBASE_HOST', 'http://localhost:8090')
TOKEN=*** 'tu_token')

result = subprocess.run([
    "curl", "-s", "-X", "POST",
    f"{HOST}/api/collections/_superusers/auth-refresh",
    "-H", f"Authorization: Bearer ***
], capture_output=True, text=True)
```

---

## Reglas de seguridad en PocketBase

| Regla | `null` | `""` (vacío) | String con filtro |
|-------|--------|--------------|-------------------|
| **Significado** | Acción deshabilitada (solo superusuarios) | Todos pueden acceder | Filtro aplicado |
| **Ejemplo** `listRule: null` → 403 para no-superusers | ❌ | ✅ | `@request.auth.id != ''` |

> Los **superusuarios siempre bypassan todas las reglas**. Si `listRule: null`, solo superusuarios pueden listar.

---

## 2. Health Check

```bash
# Verificar que la instancia está viva
curl -s $POCKETBASE_HOST/api/health
```

**Response:** HTTP 200 si está bien.

---

## 3. Collections (Admin) — Requiere token de superusuario

### Listar colecciones

```bash
curl -s $POCKETBASE_HOST/api/collections \
  -H "Authorization: Bearer $TOKEN"
```

Query params: `?page=1&perPage=30&sort=-created&filter=type='auth'`

### Ver una colección

```bash
curl -s $POCKETBASE_HOST/api/collections/{collectionIdOrName} \
  -H "Authorization: Bearer $TOKEN"
```

### Crear colección

```bash
curl -s -X POST $POCKETBASE_HOST/api/collections \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mi_coleccion",
    "type": "base",
    "fields": [
      { "name": "title", "type": "text", "required": true },
      { "name": "body", "type": "text" }
    ]
  }'
```

### Actualizar colección

```bash
curl -s -X PATCH $POCKETBASE_HOST/api/collections/{collectionIdOrName} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "nuevo_nombre"}'
```

### Eliminar colección

```bash
curl -s -X DELETE $POCKETBASE_HOST/api/collections/{collectionIdOrName} \
  -H "Authorization: Bearer $TOKEN"
```
**Response:** 204 No Content.

### Truncar colección (borrar todos los registros)

```bash
curl -s -X DELETE $POCKETBASE_HOST/api/collections/{collectionIdOrName}/truncate \
  -H "Authorization: Bearer $TOKEN"
```
**Response:** 204 No Content.

### Importar colecciones (bulk)

```bash
curl -s -X PUT $POCKETBASE_HOST/api/collections/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "collections": [
      { "name": "posts", "type": "base", "fields": [...] }
    ],
    "deleteMissing": false
  }'
```

---

## 4. Records CRUD — Requiere token (superusuario o usuario según rules)

### Listar registros

```bash
curl -s "$POCKETBASE_HOST/api/collections/{collection}/records?page=1&perPage=30" \
  -H "Authorization: Bearer $TOKEN"
```

Query params útiles:
- `?sort=-created` — ordenar DESC por fecha de creación
- `?filter=(title~'abc' && created>'2022-01-01')` — filtrar
- `?expand=relField1,relField2` — expandir relaciones
- `?fields=id,title,created` — solo campos específicos
- `?skipTotal=true` — performance (no cuenta total)

### Ver un registro

```bash
curl -s $POCKETBASE_HOST/api/collections/{collection}/records/{recordId} \
  -H "Authorization: Bearer $TOKEN"
```

### Crear registro

```bash
curl -s -X POST $POCKETBASE_HOST/api/collections/{collection}/records \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mi post",
    "body": "Contenido del post"
  }'
```

### Actualizar registro

```bash
curl -s -X PATCH $POCKETBASE_HOST/api/collections/{collection}/records/{recordId} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Título actualizado"}'
```

Para cambiar password en colecciones auth, incluir `oldPassword`:

```bash
curl -s -X PATCH $POCKETBASE_HOST/api/collections/users/records/{recordId} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "nuevoPass123", "passwordConfirm": "nuevoPass123", "oldPassword": "passAnterior"}'
```

> **Nota:** Superusuarios y usuarios con permiso "Manage" pueden saltarse `oldPassword`.

### Eliminar registro

```bash
curl -s -X DELETE $POCKETBASE_HOST/api/collections/{collection}/records/{recordId} \
  -H "Authorization: Bearer $TOKEN"
```
**Response:** 204 No Content.

---

## 5. Files

### Descargar/Ver archivo

```bash
curl -s "$POCKETBASE_HOST/api/files/{collection}/{recordId}/{filename}"
```

Con thumbnail:
```bash
curl -s "$POCKETBASE_HOST/api/files/{collection}/{recordId}/{filename}?thumb=100x100"
```

Formats de thumb: `WxH` (crop center), `WxHt` (crop top), `WxHb` (crop bottom), `WxHf` (fit), `0xH` (resize height), `Wx0` (resize width).

Forzar descarga:
```bash
curl -s "$POCKETBASE_HOST/api/files/{collection}/{recordId}/{filename}?download=1"
```

### Subir archivo

Requiere multipart/form-data:
```bash
curl -s -X POST $POCKETBASE_HOST/api/collections/{collection}/records \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=Mi post" \
  -F "file=@/ruta/al/archivo.pdf"
```

### Generar file token (para archivos protegidos)

```bash
curl -s -X POST $POCKETBASE_HOST/api/files/token \
  -H "Authorization: Bearer $TOKEN"
```

**Response:** `{ "token": "..." }`

---

## 6. Settings (Admin) — Requiere superusuario

### Ver settings

```bash
curl -s $POCKETBASE_HOST/api/settings \
  -H "Authorization: Bearer $TOKEN"
```

### Actualizar settings

```bash
curl -s -X PATCH $POCKETBASE_HOST/api/settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": { "appName": "Mi App", "appUrl": "$POCKETBASE_HOST" }
  }'
```

### Test S3

```bash
curl -s -X POST $POCKETBASE_HOST/api/settings/test/s3 \
  -H "Authorization: Bearer $TOKEN"
```

### Test SMTP

```bash
curl -s -X POST $POCKETBASE_HOST/api/settings/test/smtp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

---

## 7. Logs — Requiere superusuario

### Listar logs

```bash
curl -s "$POCKETBASE_HOST/api/logs?page=1&perPage=30" \
  -H "Authorization: Bearer $TOKEN"
```

### Ver log específico

```bash
curl -s $POCKETBASE_HOST/api/logs/{logId} \
  -H "Authorization: Bearer $TOKEN"
```

### Obtener estadísticas de logs

```bash
curl -s $POCKETBASE_HOST/api/logs/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

## 8. Backups — Requiere superusuario

### Listar backups

```bash
curl -s $POCKETBASE_HOST/api/backups \
  -H "Authorization: Bearer $TOKEN"
```

### Crear backup

```bash
curl -s -X POST $POCKETBASE_HOST/api/backups \
  -H "Authorization: Bearer $TOKEN"
```

### Restaurar backup

```bash
curl -s -X PUT $POCKETBASE_HOST/api/backups/restore \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "backup_name.zip"}'
```

### Descargar backup

```bash
curl -s "$POCKETBASE_HOST/api/backups/{filename}" \
  -H "Authorization: Bearer $TOKEN" \
  --output backup.zip
```

### Eliminar backup

```bash
curl -s -X DELETE $POCKETBASE_HOST/api/backups/{filename} \
  -H "Authorization: Bearer $TOKEN"
```

---

## 9. Realtime (SSE) — Eventos en tiempo real

PocketBase soporta Server-Sent Events (SSE) para recibir cambios en tiempo real
sin polling. Ideal para dashboards, kanbans colaborativos, y web apps que reflejan
cambios al instante.

### Flujo SSE

```
1. Cliente ──GET──→ /api/realtime
        ←──SSE──  evento PB_CONNECT {clientId}

2. Cliente ──POST──→ /api/realtime  {clientId, subscriptions: ["posts/*"]}
        ←──SSE──  eventos de cambio en tiempo real
```

### 1. Conectar SSE

```bash
# Abre una conexión SSE persistente
curl -s -N $POCKETBASE_HOST/api/realtime
```

Recibes un evento `PB_CONNECT` con un `clientId`:
```
event: PB_CONNECT
data: {"clientId":"abc123"}
```

### 2. Enviar suscripciones

Formato de suscripciones:
- `coleccion/*` — todo cambio en la colección (usa ListRule)
- `coleccion/RECORD_ID` — cambios en un registro específico (usa ViewRule)

```bash
# Con auth token (requerido si la colección tiene listRule: null)
curl -s -X POST $POCKETBASE_HOST/api/realtime \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "abc123",
    "subscriptions": ["brain_pages/*", "brain_todos/*", "brain_goals/*"]
  }'
```

### 3. Recibir eventos

Los eventos llegan por el stream SSE:
```
event: PB_RECORD_CREATE
data: {"action":"create","record":{"id":"...","title":"Nueva tarea",...}}

event: PB_RECORD_UPDATE  
data: {"action":"update","record":{"id":"...","title":"Tarea actualizada",...}}

event: PB_RECORD_DELETE
data: {"action":"delete","record":{"id":"..."}}
```

### Sin auth: colecciones públicas

Para que el SSE funcione sin token:
1. La colección debe tener `listRule: ""` (vacío = acceso público)
2. Solo se reciben eventos de create/update — nunca datos sensibles
3. El cliente solo ve qué IDs cambiaron, no el contenido

```json
// Ejemplo: hacer brain_todos públicamente legible
{
  "listRule": "",
  "viewRule": "",
  "createRule": null,
  "updateRule": null,
  "deleteRule": null
}
```

### Implementación en JavaScript

```javascript
// Conectar SSE
const es = new EventSource('http://localhost:8090/api/realtime');

// Guardar clientId
es.addEventListener('PB_CONNECT', (e) => {
  const { clientId } = JSON.parse(e.data);
  // Suscribirse a cambios
  fetch('http://localhost:8090/api/realtime', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      clientId,
      subscriptions: ['brain_pages/*', 'brain_todos/*', 'brain_goals/*']
    })
  });
});

// Escuchar cambios
es.addEventListener('PB_RECORD_CREATE', () => refreshData());
es.addEventListener('PB_RECORD_UPDATE', () => refreshData());
es.addEventListener('PB_RECORD_DELETE', () => refreshData());
```

### Pitfalls

- **SSE requiere HTTP/1.1 persistente** — no funciona con HTTP/2 server push
- **El token es necesario si `listRule: null`** — hacer colecciones públicas si es solo lectura local
- **Un solo cliente por conexión SSE** — múltiples pestañas necesitan múltiples conexiones
- **Reconexión automática** — `EventSource` se reconecta solo si la conexión cae
- **CORS** — si PB está en otro dominio, requiere configurar `Origin` headers en PB settings

### Conectar SSE

```bash
curl -s -N $POCKETBASE_HOST/api/realtime
```

Recibes un evento `PB_CONNECT` con un `clientId`.

### Enviar suscripciones

```bash
curl -s -X POST $POCKETBASE_HOST/api/realtime \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "ID_DEL_CLIENTE",
    "subscriptions": ["posts/*", "users/RECORD_ID"]
  }'
```

Formato de suscripciones:
- `coleccion/*` — todo cambio en la colección (usa ListRule)
- `coleccion/RECORD_ID` — cambios en un registro específico (usa ViewRule)

---

## 10. Batch — Requiere habilitado en Settings

### Ejecutar múltiples operaciones en una transacción

```bash
curl -s -X POST $POCKETBASE_HOST/api/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      { "method": "POST", "url": "/api/collections/posts/records", "body": {"title": "Post 1"} },
      { "method": "PATCH", "url": "/api/collections/posts/records/RECORD_ID", "body": {"title": "Post actualizado"} },
      { "method": "DELETE", "url": "/api/collections/posts/records/OTRO_RECORD_ID" }
    ]
  }'
```

Para upsert usar `PUT` (body debe incluir `id`).

---

## 11. Impersonación (Superusuarios solamente)

Genera un token no-refrescable para actuar como otro usuario:

```bash
# Autenticar como superuser
TOKEN=*** -s -X POST $POCKETBASE_HOST/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d '{"identity": "'$POCKETBASE_EMAIL'", "password": "'$POCKETBASE_PASSWORD'"}' | jq -r '.token')

# Impersonar usuario (token válido 1 hora = 3600s)
IMP_TOKEN=*** -s -X POST $POCKETBASE_HOST/api/collections/users/impersonate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration": 3600}' \
  --data-urlencode "userId=ID_DEL_USUARIO" \
  | jq -r '.token')
```

---

## 12. Filtros PocketBase (referencia rápida)

| Operador | Significado |
|----------|-------------|
| `=` | Igual |
| `!=` | Diferente |
| `>` | Mayor que |
| `>=` | Mayor o igual |
| `<` | Menor que |
| `<=` | Menor o igual |
| `~` | Like (contiene) |
| `!~` | Not like |
| `?=` | Any-of igual |
| `?~` | Any-of like |
| `&&` | AND |
| `||` | OR |
| `()` | Agrupar |
| `//` | Comentario |

Ejemplo de filtro:
```
?filter=(title~'abc' && created>'2022-01-01') || (status='published')
```

---

## Tips rápidos

- **jq** es tu amigo para parsear JSON: `curl ... | jq '.items'`
- Guarda el token en variable `TOKEN` al inicio de la sesión
- Si un endpoint regresa 403, probablemente necesitas token de superusuario
- Los endpoints de collections, settings, logs y backups SOLO funcionan con superusuario
- Los records pueden funcionar con token de usuario regular si las reglas lo permiten
- Los secrets en settings siempre regresan como `*****`
- Subida de archivos SOLO con multipart/form-data, no JSON
- **URL encoding**: `pb._request()` ya encodea query params con `urllib.parse.quote()`. Si usas curl directo, encodea los filtros con `--data-urlencode` o `urllib.parse.quote()`.
- **`~` es case-sensitive**: `title~'transformer'` NO matchea "Transformer". No hay `lower()` en filtros PB: filtra en Python trayendo todos los registros y matcheando localmente con `.lower()`.
- **Relaciones en `create_collection`**: `collectionId` debe ser el ID real (`pbc_xxx`), no el nombre. Resuelve con `pb.get_collection(name)['id']` primero.
- **Relaciones autoreferenciadas**: Una colección con un campo relation apuntando a sí misma falla en la creación. Créala sin ese campo y agrégalo con PATCH después.

---
