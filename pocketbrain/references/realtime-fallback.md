# PocketBrain Realtime: Pitfall SSE + Alternativa Heartbeat

## Contexto

PocketBase tiene un sistema de realtime (WebSocket/SSE) para escuchar cambios en colecciones. Sin embargo, depende de la versión del servidor y de si el plugin de realtime está instalado/configurado.

## El Pitfall: SSE no funciona en esta instancia

**Síntoma:** Al intentar conectar `EventSource` a `/api/collections/brain_goals/sse?auth=TOKEN`, el servidor responde:
```json
{"data":{},"message":"File not found.","status":404}
```

**Causa:** La versión actual de PocketBase no expone SSE por ese endpoint. Puede que sea una versión anterior o que el plugin de realtime no esté activo.

## Alternativa Implementada: Heartbeat + Diff de Conteos

Dado que el SSE nativo no funciona, se implementa una detección de cambios basada en polling:

### 1. Heartbeat (ping a /api/health)
- Cada 10 segundos se hace `fetch(pb_url + '/api/health')`
- Si responde 200 → status verde (live)
- Si falla 2 veces seguidas → status rojo (offline)

### 2. Detección de cambios
- En cada `loadAll()` (cada 30s o manual) se guarda `_lastSnap` con los conteos de cada colección
- Después de la primera carga (`_firstLoad = false`), se compara el nuevo resultado vs `_lastSnap`
- Si `goals.length`, `todos.length`, etc. cambiaron → se muestra toast:
  ```
  "Goals, Tareas: Actualizado"
  ```

### 3. Toast system
- Contenedor fijo bottom-right (`position:fixed;bottom:16px;right:16px`)
- Max 3 toasts visibles (FIFO — si llega el 4to, bota el primero)
- Cada toast dura 5 segundos, luego fade-out de 300ms
- Colores: verde=create, gris=update, rojo=delete
- Contenido: `<strong>Acción</strong>Collecciones: cambio`

### Backend necesario

`brain_web.py` debe exponer `/api/config`:
```python
elif path == "/api/config":
    brain = get_brain()
    self.serve_json({
        "pb_url": env["POCKETBRAIN_HOST"],
        "token": brain.pb.get_token(),
        "context": CTX
    })
```

El frontend usa `token` y `pb_url` para hacer heartbeat y, en el futuro, para SSE si se activa.

### Cuándo reevaluar SSE

Si PocketBase se actualiza o se instala el plugin de realtime:
1. Verificar si `/api/collections/{col}/sse` dejó de devolver 404
2. Reemplazar `startHeartbeat()` + `checkDiff()` por `EventSource` subscriptions
3. Los toasts actuales ya funcionan como fallback: mostrar "Actualizado" cuando llegue un evento SSE

### Referencias cruzadas
- `web-ui-patterns.md` — Patrón de toasts y status indicators
- `web-ui.md` — Arquitectura del frontend SPA
- `brain_web.py` — Endpoint `/api/config` y servicio HTTP
