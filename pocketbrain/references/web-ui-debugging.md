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

## Headless browser limitation: visual JS libraries (vis.js, etc.) no cargan desde CDN

El browser tool remoto/headless puede cargar `localhost` y ejecutar JS inline, pero **scripts `<script src="https://cdn.example.com/...">` externos pueden fallar silenciosamente** sin lanzar error. El DOM se renderiza, la leyenda CSS aparece, pero el canvas WebGL/vis.js permanece vacío porque el objeto `vis` global nunca se define.

**Síntoma:** la vista Graph muestra la leyenda de colores pero sin nodos. `typeof vis === 'undefined'` en `browser_console`. Las APIs del backend devuelven datos correctamente. No hay errores en la consola del browser.

**Diagnóstico:**
```javascript
// Verificar si vis.js está cargado
expression="typeof vis !== 'undefined' ? 'vis OK' : 'vis MISSING — CDN not loaded'"
// Verificar si GRAPH existe
expression="typeof GRAPH === 'undefined' ? 'GRAPH missing' : 'GRAPH: ' + GRAPH.nodes.length + ' nodes'"
```

**Workarounds:**
1. **Prueba en Chrome/Safari local:** El headless browser tool es para validación automática, pero `vis.js` y otras librerías visuales pesadas pueden necesitar navegador real con soporte WebGL completo.
2. **Inyectar manualmente:** si el CDN falla, inyectar el script dinámicamente:
```javascript
if(typeof vis === 'undefined'){
  var s = document.createElement('script');
  s.src = 'https://unpkg.com/vis-network@9.1.6/dist/vis-network.min.js';
  s.onload = function(){ console.log('vis loaded'); };
  document.head.appendChild(s);
}
```
3. **No bloquear deploy por esto:** si `node --check` pasa y las APIs devuelven datos, pero el browser tool muestra Graph vacío, la causa es probablemente el entorno headless, no el código. Verificar en navegador local antes de descartar.

**Regla:** si la UI funciona (kanban, proyectos, tabs) pero una librería visual no renderiza, el código probablemente está bien. Verificar con `browser_console` que la librería está cargada antes de debuguear el código de renderizado.

## Errores comunes y síntomas

| Síntoma | Causa raíz | Cómo diagnosticar | Fix |
|---|---|---|---|
| Pantalla blanca con "● cargando..." | JS syntax error | `node --check` | Corregir escape de comillas |
| Sidebar renderiza, contenido vacío | `ReferenceError` en función de render | `browser_console()` | Eliminar llamada a fn inexistente |
| "Failed to fetch" en console | Server single-threaded (HTTPServer) | `curl -v` | Cambiar a `ThreadingHTTPServer` |
| Datos de contexto viejo tras cambiar | `get_brain()` cache global | `get_brain()` per-BN | `_brain_cache = {} # BN → Brain` |
| Columnas kanban con scroll horizontal | `overflow-x:auto` + `flex:none` | `browser_vision` | `flex:1 1 0` sin `overflow-x` |
| Project cards vacías | `page` field no vinculado en PB | `curl -s api/todos` | Vincular `page` en todos/goals/reminders |

## Síntoma: "No carga datos" / Sidebar vacío / JS no ejecuta

Este es un caso especial que parece API failure pero es un **JS syntax error global**. El HTML estático se renderiza (se ve el sidebar, el título "PocketBrain", la barra de búsqueda), pero todo el contenido JavaScript (menú, proyectos, select de contexto) aparece como "Cargando..." o vacío. Las APIs responden 200 OK con curl, pero el browser no las llama porque el script no arrancó.

**Causa típica:** un `\n` literal (backslash + n) escapado por `patch` en el JS global, o una comilla mal escapada que rompe el `<script>` tag antes de que cualquier función se defina. Ver `references/html-js-patching.md` para el `\n` literal pitfall.

**Diagnóstico en 3 segundos:**

```javascript
// En browser_console:
expression = "typeof api === 'undefined' ? 'JS_NO_ARRANCÓ' : 'JS_OK'"
expression = "typeof loadBrains === 'undefined' ? 'NO_FUNC' : 'OK'"
expression = "document.getElementById('nav').innerHTML === '' ? 'SIDEBAR_VACÍO' : 'SIDEBAR_OK'"
```

Si `typeof api` es `undefined` y el sidebar no tiene links, el script no ejecutó. **No es un problema de API ni de servidor.**

**Fix:**
1. `node --check` sobre el JS extraído (ver paso 1 arriba).
2. Si pasa `node --check` pero el browser sigue sin ejecutar, buscar `\n` literales: `grep -n '\\\\n' web_ui.html`.
3. Usar `execute_code` (Python) para corregir los `\n` literales a newlines reales. Ver `references/html-js-patching.md`.

## Runtime errors: `node --check` es solo syntax, no ejecuta

`node --check` solo valida sintaxis. Una llamada a una función inexistente (`activateView('projects')`) **pasa** `node --check` porque es sintácticamente válida JavaScript. Falla solo en runtime del browser.

**Cada función nueva o modificada (como `renderProjectsView()` que llama a `activateView()`) debe ejecutarse en el browser.** Verificar:
```javascript
// En browser_console: ¿la función existe y no lanza error?
expression="typeof activateView === 'function' ? 'EXISTS' : 'MISSING'"
expression="renderProjectsView(); typeof _projectData === 'object' ? 'OK' : 'FAILED'"
```

**Regla:** si agregas una función que llama a otra función (ej. `renderProjectsView()` → `activateView()`), verificar que la función destino exista en el mismo `<script>` tag antes de reiniciar el server.

## Regla de oro: verificar ANTES de afirmar

> Si el JS pasa `node --check` y las APIs devuelven datos, el UI debería renderizar. Si no, es un bug de JS runtime (función perdida, selector mal, etc.) que solo se ve en el browser.

**Nunca decir "ya jala" sin:** `node --check` + API curl + al menos una `browser_console` check o `browser_vision` screenshot.

**Preferir browser automation sobre desktop tools.** La herramienta `browser_*` (Hermes browser automation) SÍ accede a `localhost` y ejecuta JS en el contexto de la página. No usar `screencapture`, `osascript`, `open` de Chrome/Safari — son flaky en headless y no son reproducibles. Usar `browser_navigate` / `browser_console` / `browser_vision`.
