# Debug de UI runtime — PocketBrain Web

Técnicas para debuggear la SPA modular de PocketBrain cuando algo no carga, no navega, o muestra datos incorrectos.

## Verificación mínima antes de reportar "jala"

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 -m py_compile brain_web.py
python3 -m py_compile brain.py
node --check app.js
for f in views/*.js components/*.js; do node --check "$f"; done
```

## Problema: la UI se queda en "Cargando..."

1. Abrir DevTools → Console.
2. Buscar errores de ES module:
   ```
   The requested module './views/X.js' does not provide an export named 'Y'
   ```
3. Comparar export real del módulo vs import en `app.js`.
4. `node --check` no detecta errores de resolución de imports — solo syntax.
5. Si el JS está bien, limpiar cache del browser:
   - `Cmd+Shift+R` o
   - DevTools → Network → "Disable cache"
   - o navegar con `?nocache=N#...`
6. Verificar que el proceso viejo no siga vivo:
   ```bash
   lsof -i :8899
   kill -9 PID
   ```

## Problema: stacking de vistas

Symptom: al navegar, la nueva vista aparece debajo de la anterior.

```js
// En console de DevTools
document.querySelectorAll('#main > div.active').length
// Debe ser 1. Si es > 1, hay stacking.
```

Fix: buscar `classList.add('active')` en `views/` y reemplazar por `setActiveView('view-xxx')`.

```bash
grep -R "classList.add('active')" ~/.hermes/skills/productivity/pocketbrain/scripts/views/
```

Asegurar que `app.js` expone:

```js
window.setActiveView = setActiveView;
```

## Problema: project detail muestra counts en 0

```bash
# Verificar API devuelve page_slug
curl -s 'http://localhost:8899/api/goals?context=personal' | python3 -m json.tool | grep page_slug
curl -s 'http://localhost:8899/api/todos?context=personal' | python3 -m json.tool | grep page_slug
curl -s 'http://localhost:8899/api/reminders?context=personal' | python3 -m json.tool | grep page_slug
curl -s 'http://localhost:8899/api/journal?context=personal' | python3 -m json.tool | grep page_slug
```

Si `page_slug` es vacío para registros que deberían tener proyecto:
- Revisar `references/backend-relations-shape.md`.
- Verificar que `brain.py` guarda `related_pages`.
- Verificar que `seed.py` pasa `page_slug`/`project_slug`.

## Problema: wikilinks/backlinks no navegan

1. Inspeccionar el link generado:
   ```js
   document.querySelector('.wl').outerHTML
   ```
2. Debe ser `href="javascript:void(0)"`, no `href="#"`.
3. Debe tener listener que llame `window.showPage(slug)`.
4. Para markdown dinámico, llamar `bindMarkdownLinks(container)` después de insertar HTML.

## Problema: cache del browser sirve archivos viejos

```bash
curl -s http://localhost:8899/app.js | grep -n "renderFiles"
curl -s http://localhost:8899/views/projects.js | head -5
```

Si curl devuelve lo correcto pero el browser no, es cache del browser.

## Matar servidor zombie

```bash
lsof -i :8899
kill -9 PID
```

Luego reiniciar:

```bash
python3 brain_web.py --context personal --port 8899
```

## Verificación visual final

Antes de decir "ya quedó", capturar screenshot y confirmar:
- Sidebar alineado con iconos Heroicons.
- Project detail con todas las tabs y counts reales.
- Click en card navega y deja 1 solo div active.
- Backlinks tab muestra entradas clickeables.
