# Modular SPA — ES Module Import/Export Pitfalls

Apuntes del refactor de `web_ui.html` monolítico a módulos ES en PocketBrain.

## Estructura de módulos

```
scripts/
  app.js           # entry point: importa vistas y arranca la app
  api.js           # cliente HTTP
  store.js         # estado central
  router.js        # hash router
  markdown.js      # renderizador markdown + wikilinks
  web_ui.css       # estilos extraídos
  web_ui.html      # shell vacío con <script type="module" src="/app.js"></script>
  components/
    Tabs.js
    Icon.js
  views/
    projects.js
    todos.js
    goals.js
    milestones.js
    reminders.js
    journal.js
    files.js
    type.js
    wiki.js
    graph.js
    lint.js
```

## Reglas de imports/exports

- Cada vista debe exportar la función que `app.js` importa. Si `app.js` importa `{ renderGraph }`, el módulo debe exportar `renderGraph`, no `renderGraphView`.
- Usar alias cuando el nombre interno difiera del nombre externo:
  ```js
  import { renderFilesView as renderFiles } from './views/files.js';
  ```
- Nunca dejar stubs con exports distintos a lo que `app.js` espera. El browser falla silenciosamente con `SyntaxError: The requested module './views/X.js' does not provide an export named 'Y'`.

## Pitfall: módulo importa export incorrecto

Síntoma: la UI se queda en "Cargando..." y la consola dice:

```
The requested module './views/graph.js' does not provide an export named 'renderGraph'
```

Causa real: `views/graph.js` exportaba `renderGraphView` pero `app.js` importaba `renderGraph`.

Fix: cambiar el export del módulo o el import de `app.js`. Preferir cambiar el export del módulo para mantener nombres consistentes con la arquitectura.

## Cache agresivo del servidor

`brain_web.py` sirve JS estáticos con `Cache-Control: max-age=3600`. Reiniciar el servidor NO invalida el cache del browser para módulos ES.

Solución: después de cambiar módulos:
1. Matar el proceso viejo con `lsof -ti:PORT | xargs kill -9`.
2. Reiniciar `python3 brain_web.py --context personal --port 8899`.
3. Navegar con querystring `?nocache=N#tab=...`.
4. Si persiste, abrir DevTools → Network → "Disable cache" y recargar (`Cmd+Shift+R`).

## Verificación rápida

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
node --check app.js
for f in views/*.js; do node --check "$f"; done
python3 -m py_compile brain_web.py
python3 -m py_compile brain.py
```

## Lint view con datos reales

El endpoint `/api/lint?context=personal` devuelve:

```json
{
  "total_pages": 75,
  "summary": {
    "orphans": 75,
    "broken_links": 246,
    "low_confidence": 0,
    "contested": 0,
    "invalid_tags": 0,
    "oversized": 0,
    "drift": 0,
    "frontmatter_issues": 18
  },
  "orphans": ["slug1", "slug2"],
  "broken_links": [{"page": "...", "link": "..."}],
  ...
}
```

La UI debe mostrar:
- Tabla resumen Issue/Cantidad.
- Listas expandibles por tipo de issue.
- Cards clickeables que naveguen al slug afectado (para broken_links, preferir mostrar `page` pero navegar al `link` si es el destino).

## Backend relations expand shape

PocketBase `expand=related_pages` may return a **dict** (single relation) or a
**list of dicts** (multiple relations). Code in `brain_web.py` that assumes a list
silently fails to read `page_slug`, so project detail shows zero counts for
goals/todos/reminders/journal/files even though the relations exist.

See `references/backend-relations-shape.md` for the fix pattern.

## Project detail must always show all tabs

Even if counts are zero, the project detail should render tabs for:
Contenido, Goals, Milestones, Ideas, Planes, Todo, Reminders, Notas, Journal,
Archivos, Graph. Each tab needs an empty state. Hiding tabs makes the UI feel
incomplete.

## Project detail card clicks must navigate

Cards rendered for goals/milestones/todos/reminders/journal/files/notes inside
a project detail must be clickable and call `window.showPage(slug)`. Use a
delegated click handler on `#view-projects` for both `[data-pb-page]` and
`[data-pb-back-projects]`.

## Wikilinks must use `javascript:void(0)`

`href="#"` resets the hash after `setHashParams()` runs. Render wikilinks as
`<a href="javascript:void(0)" data-slug="...">` and bind a global listener.

## View stacking fix

Every view renderer must call the central `setActiveView(viewId)` helper
(exposed as `window.setActiveView`) instead of `container.classList.add('active')`.
This guarantees only one `#main > div` is `.active` at a time. Affected modules:
`views/wiki.js`, `views/graph.js`, `views/lint.js`.

## View stacking en SPA modular

Síntoma: al hacer click en un link/card, el nuevo contenido se renderiza **debajo** de la vista anterior en vez de reemplazarla.

Causa: módulos de vista llaman `container.classList.add('active')` directamente en vez de usar el helper global `setActiveView(viewId)`.

Fix:
1. En `app.js` exponer `window.setActiveView = setActiveView`.
2. En cada vista, reemplazar `container.classList.add('active')` por `setActiveView('view-xxx')` ANTES de renderizar contenido.
3. Verificar con `browser_console`:
   ```js
   document.querySelectorAll('#main > div.active').length === 1
   ```

Vistas que históricamente tuvieron este problema:
- `views/wiki.js` (`renderWikiPage`, `renderWikiIndex`)
- `views/graph.js` (`renderGraph`)
- `views/lint.js` (`renderLintView`)

## Card navigation: clicks delegados

Para que las cards de goals/todos/reminders/journal/archivos dentro de project detail naveguen correctamente:

1. Generar cards con `data-pb-page="${slug}"` y `style="cursor:pointer"`.
2. Delegar el click desde el contenedor padre:
   ```js
   container.addEventListener('click', e => {
     const card = e.target.closest('[data-pb-page]');
     if (card) {
       e.preventDefault();
       e.stopPropagation();
       const slug = card.dataset.pbPage;
       if (slug && typeof window.showPage === 'function') window.showPage(slug);
     }
   });
   ```
3. Incluir también el breadcrumb `data-pb-back-projects` para volver a proyectos.

## Backend relations

Si las tabs de proyecto muestran counts en 0 aunque existan goals/todos/reminders/journal, verificar que el backend guarde y exponga `page_slug`/`related_pages` correctamente. Los métodos `create_goal`, `create_todo`, `create_reminder`, `journal_write` deben propagar `project_slug` o `related_slugs` a `related_pages` de la página creada.

## Wikilinks y hash reset

Los links generados por `markdown.js` deben usar `href="javascript:void(0)"`, no `href="#"`, para evitar que el browser resetee el hash después de `setHashParams()`.
