# UI Patterns — web_ui.html

Patrones arquitectónicos y diseño de la interfaz web de PocketBrain.

## Layout unificado: H1 + select en view-header, tabs debajo

**Regla de diseño:** En TODAS las vistas, el `<h1>` y el *filter select* (Todos/Con proyecto/Sin proyecto) van juntos dentro del `view-header` (select a la derecha del H1). Los *status tabs* (Todos/Activos/Terminados) van debajo en `div.project-tabs` con `margin:12px 0`.

```
┌──────────────────────────────────────┐
│  📖 Title          [Todos ▼]         │  ← view-header (H1 + select a la derecha)
├──────────────────────────────────────┤
│  [Todos] [Activos] [Terminados]      │  ← project-tabs debajo con margin:12px 0
├──────────────────────────────────────┤
│  contenido...                        │
└──────────────────────────────────────┘
```

### Vistas que cumplen este patrón:

| Vista | H1 + select en view-header | Status tabs debajo |
|-------|---------------------------|-------------------|
| Todo | `Todo` + `[Todos ▼]` | No tiene tabs |
| Type views (Conceptos, Entidades...) | `Conceptos (X de Y)` + `[Todos ▼]` | No tiene tabs |
| Goals | `Goals` + `[Todos ▼]` | `Todos / Activos / Backlog / Terminados / Cancelados` |
| Milestones | `Milestones` + `[Todos ▼]` | `Todos / Activos / Backlog / Terminados / Cancelados` |
| Reminders | `Reminders` + `[Todos ▼]` | `Hoy / Esta semana / Próximos / Atrasados / Completados / Todos` |
| Files | `Files` + `[Todos ▼]` | No tiene tabs |
| Journal | `Journal` + `[Todos ▼]` + `[Junio 2026 ▼]` | No tiene tabs |

## Project detail: tabs principales

El proyecto tiene **tabs principales fijos** ordenados por importancia: `Contenido` → `Goals` → `Milestones` → `Ideas` → `Planes` → `Todo` → `Reminders` → `Notas` → `Journal` → `Archivos` → `Graph`.

**Reglas actuales:**
- Todos los tabs se muestran siempre, con count badge (incluso si es 0). No ocultar tabs vacíos.
- Cada tab tiene un **empty state** claro: "No hay goals.", "No hay tareas.", etc.
- `Entregables` ya no es tab. Álvaro consolidó todo en `Archivos`.
- El breadcrumb `← Proyectos` va arriba del H1, no entre tabs y contenido.
- Las cards dentro de cada tab (goals, todos, reminders, journal, archivos, notas/ideas/planes) deben tener `data-pb-page="slug"` y navegar a la wiki page al hacer click.
- Las relaciones de un proyecto con goals/todos/reminders/journal/archivos se detectan vía `page_slug` y `related_pages` devueltos por el backend. Si counts quedan en 0 con datos existentes, revisar `references/backend-relations-shape.md` y `references/project-detail-validation.md`.

## Tab active state: nunca hardcodear `class="active"`

**Regla de oro:** ninguna tab `<a>` debe nacer con `class="active"` hardcodeada. El estado activo debe manejarse **dinámicamente** mediante la función switch de cada vista.

## Hash URLs: toda navegacion debe generar URL

Cada vez que se agrega un sub-tab, filtro, o navegacion, debe llamar a `setHashParams()` para reflejar el estado en la URL.

### Pitfall: href="#" resetea el hash

`<a href="#">` hace que el browser procese `#` DESPUES del onclick, sobrescribiendo el hash que `history.replaceState` acaba de poner. **Siempre usar `href="javascript:void(0)"`** en todos los links del sidebar, sub-tabs, y filtros que actualizan el hash.

## Filter selects: Todos / Con proyecto / Sin proyecto

TODAS las vistas con filtro de proyecto usan el mismo select de 3 opciones. No per-project dropdowns.

## Cards minimalistas: solo titulo

En todas las listas (proyectos, goals, milestones, type views), las cards deben mostrar **solo el titulo**. Sin chips de tipo, sin contadores, sin status/deadline.

## Markdown renderer: mdToHtml()

Funcion inline en el HTML. Mejoras aplicadas:
1. **Escapar HTML** en `code` blocks y texto plano
2. **Bold/Italic**: `***bold+italic***`, `**bold**`, `*italic*`
3. **Listas**: unordered `ul`/`li` con `- `; ordered `ol`/`li` con `1. `
4. **Links**: `[text](url)` → `<a target="_blank" class="wl">`
5. **Wikilinks**: `[[Slug]]` o `[[Page|Alias]]` → `showPage()` o `<span class="bl">` (si no existe)
6. **Referencias**: `^[slug]` → superscript link a pagina
7. **Blockquotes**: `> texto` → `<blockquote>`

## Graph rendering (vis.js): legend debe ser sibling, no child

vis.js Network **reemplaza el innerHTML del contenedor** cuando se inicializa. La leyenda debe ser **hermano** de `graph-view`, no hijo.

## Empty state: toda seccion sin items debe mostrar mensaje

Cualquier tab o seccion que pueda estar vacia debe mostrar mensaje.

## Iconos: Heroicons SVG inline (no emojis, no font icons)

Usar helper `icon(name, size)` que inserta SVG `<path>` inline con los `d` de Heroicons. No emojis Unicode, no font-icons.

## Sidebar: href=javascript:void(0) + return false

**Regla:** todos los links del sidebar usan `href="javascript:void(0)"` y `onclick` termina con `;return false`.

## Post-migración modular SPA: casos comunes

| Síntoma | Causa probable | Fix |
|---------|---------------|-----|
| Solo se ve `Contenido` y `Graph` en project detail | Todos/Goals/Reminders tienen `page_slug` vacío en el backend | Verificar `create_todo`, `create_goal`, `create_reminder`, `journal_write`; revisar `references/backend-relations-shape.md` |
| Journal muestra markdown crudo | No se llama `window.mdToHtml()` en `views/journal.js` | Renderizar body con `window.mdToHtml(body)` |
| Sidebar sin iconos | `app.js` no importa `icon()` o CSS no permite SVG | Importar `icon` de `components/Icon.js`; CSS flex para `.nav-label` |
| Cards no son clickeables | Falta `data-pb-page` + event listener o inline onclick | Agregar dataset y listener delegado |
| Project graph solo muestra nodo central | `renderProjectGraph` no recibe `data.p` o no hay relaciones | Verificar que `data` incluye `p`, `goals`, `todos`, `rems` |
| Status tabs de Goals suman menos que total | Un goal tiene status `backlog` | Agregar tab "Backlog" |
| `startsWith is not a function` | En `brain_web.py` se escribió `path.startsWith()` (JS) en vez de `path.startswith()` (Python) | Corregir a `path.startswith("/views/")` |
| UI se queda en "Cargando..." | Error de importación ES module | Revisar browser console: `The requested module './views/X.js' does not provide an export named 'Y'`. Verificar también cache del browser. |
| Wikilinks case-insensitive no funcionan | Frontend/backend comparan slugs case-sensitive | Backend: `slug_by_lower` en `get_pages()`/`get_graph()`; Frontend: `resolveSlug(target) \|\| resolveSlug(target.toLowerCase())` |
| Backlinks no aparecen en wiki page | `brain.list_pages()` no expande `related_pages` | Asegurar `expand='domain,tags,related_pages'` en `list_pages()` |
| Navegación de cards renderiza vista debajo (stacking) | Vistas llaman `container.classList.add('active')` directo | Reemplazar por `setActiveView('view-xxx')` y exponer `window.setActiveView` en `app.js`. Ver `references/modular-spa-pitfalls.md`. |

## Síntoma: project detail tabs vacíos aunque sidebar global muestra datos

1. Verificar que el backend guarda relaciones:
   ```python
   from brain import Brain
   b = Brain('personal')
   goals = b.list_pages(page_type='goal')
   print(goals[0].get('related_pages'))  # debe contener ID del proyecto
   ```
2. Verificar que `brain_web.py` normaliza `expand.related_pages` (dict vs list). Ver `references/backend-relations-shape.md`.
3. Verificar con curl:
   ```bash
   curl -s 'http://localhost:8899/api/todos?context=personal' | python3 -m json.tool | grep page_slug
   ```
4. Si `page_slug` es vacío aunque `related_pages` tiene ID, el problema está en `brain_web.py`.
5. Si `related_pages` está vacío, el problema está en `brain.py` o en `seed.py`.

## Síntoma: clicks dentro de project detail renderizan vista debajo (stacking)

1. Ejecutar en console:
   ```js
   document.querySelectorAll('#main > div.active').length
   // Si es > 1, hay stacking
   ```
2. Buscar `classList.add('active')` directo en `views/`:
   ```bash
   grep -R "classList.add('active')" ~/.hermes/skills/productivity/pocketbrain/scripts/views/
   ```
3. Reemplazar cada coincidencia por `setActiveView('view-xxx')`.
4. Asegurar que `app.js` expone `window.setActiveView = setActiveView`.
5. Ver checklist completo en `references/project-detail-validation.md`.

## Síntoma: subagentes no terminan fixes críticos

Si un subagente reporta "identifiqué el problema" pero no aplicó cambios por límite de iteraciones:

1. Hacer el fix directamente si es pequeño (1-3 archivos, <20 líneas).
2. Validar con `node --check` / `py_compile` antes de reiniciar.
3. Usar subagentes SOLO para verificación, screenshots, o tareas paralelas grandes después de que el fix central ya esté aplicado.
4. Documentar el patrón en `references/project-detail-validation.md` para futuras sesiones.
