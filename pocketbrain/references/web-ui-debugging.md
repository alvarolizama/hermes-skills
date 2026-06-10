# Web UI Debugging & Testing Workflow

> Cómo probar cambios en web_ui.html localmente antes de decir "ya jala".

## Flujo de validación (obligatorio para TODO cambio a web_ui.html)

### 1. JS syntax validation con node --check

El JS de `web_ui.html` se ejecuta como inline HTML. Errores de sintaxis silenciosamente matan TODO el script.

```bash
# Extraer JS de <script> tags para validación
python3 -c "
import re
html = open('web_ui.html').read()
m = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if m:
    open('/tmp/pb_js.js', 'w').write(m.group(1))
" && node --check /tmp/pb_js.js && echo "JS SYNTAX OK" || echo "JS SYNTAX FAIL"
```

**NUNCA saltar este paso.** Si hay `SyntaxError: Unexpected string`, el server sirve el HTML pero el browser nunca ejecuta nada → pantalla blanca con "● cargando...".

### 2. Restart del servidor OBLIGATORIO

`brain_web.py` lee `web_ui.html` en cada `GET /` (no cachea el HTML). PERO: el servidor Python cachea la conexión a PocketBase (`get_brain() → dict BN`). Si el archivo JS cambia, el server lo sirve en la próxima request. PERO:

- Si cambias variables en `brain_web.py` (caché, endpoints), SÍ necesita restart.
- Si cambias solo el HTML, teóricamente el server lee el archivo cada vez. EN PRÁCTICA: si el server estaba crasheado o en estado de error, no se recupera solo. Kill + restart es más confiable.

```bash
# Kill y restart
lsof -ti:8899 | xargs kill -9 2>/dev/null; sleep 1
python3 brain_web.py --context personal --port 8899 2>&1 &
```

### 3. Verificar APIs con curl (no con browser)

```bash
for ep in brains pages goals todos deps files reminders journal graph; do
  len=$(curl -s "http://localhost:8899/api/$ep?brain=personal" | wc -c)
  echo "$ep: $len bytes"
done
```

**Todas las APIs deben devolver >0 bytes.** Si alguna devuelve 0 bytes, el server está mal configurado o la conexión a PocketBase falló.

## Browser testing vs. curl — reglas

| Herramienta | Cuándo usar | Cuándo NO usar |
|---|---|---|
| `curl` | Verificar APIs, payload size, JSON structure | Verificar renderizado visual |
| `browser_navigate` / `browser_vision` | Verificar UI, tomar screenshots, testar JS | Testar APIs con payloads grandes |
| **Chrome local** | Validación final con interacción real | NO depender solo de esto para "ya jala" |
| `screencapture` (macOS) | NO funciona en headless | NO usar en workflows automáticos |

**Regla: el browser tool de Hermes SÍ puede acceder a localhost:8899.** 
- `browser_navigate(url='http://localhost:8899/')` funciona si el server está corriendo.
- `browser_vision(image_url='http://localhost:8899/')` toma screenshots del servidor local.
- `browser_console(expression='...')` ejecuta JS contra el DOM del server local.
- **NO usar `screencapture` o `osascript` de Chrome local** — son flaky en headless y no son reproducibles.

## Errores comunes y síntomas

| Síntoma | Causa raiz | Cómo diagnosticar | Fix |
|---|---|---|---|
| Pantalla blanca con "● cargando..." | JS syntax error | `node --check` | Corregir escape de comillas |
| Sidebar renderiza, contenido vacío | `ReferenceError` en función de render | `browser_console()` | Eliminar llamada a fn inexistente |
| "Failed to fetch" en console | Server single-threaded (HTTPServer) | `curl -v` | Cambiar a `ThreadingHTTPServer` |
| Datos de contexto viejo tras cambiar | `get_brain()` cache global | `get_brain()` per-BN | `_brain_cache = {} # BN → Brain` |
| Columnas kanban con scroll horizontal | `overflow-x:auto` + `flex:none` | `browser_vision` | `flex:1 1 0` sin `overflow-x` |
| Project cards vacías | `page` field no vinculado en PB | `curl -s api/todos` | Vincular `page` en todos/goals/reminders |

## Regla de oro: verificar ANTES de afirmar

> Si el JS pasa `node --check` y las APIs devuelven datos, el UI debería renderizar. Si no, es un bug de JS runtime (función perdida, selector mal, etc.) que solo se ve en el browser.

**Nunca decir "ya jala" sin:** `node --check` + API curl + al menos una screenshot o browser console check.
