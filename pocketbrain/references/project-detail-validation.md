# Project Detail — Validación y Pitfalls

Guía para completar y verificar la vista de detalle de proyecto en PocketBrain Web UI.

## Requisitos mínimos de project detail

La vista debe mostrar SIEMPRE estas tabs con conteo, incluso si está en 0:

1. Contenido
2. Goals
3. Milestones
4. Ideas
5. Planes
6. Todo
7. Reminders
8. Notas
9. Journal
10. Archivos
11. Graph

Cada tab con 0 items debe mostrar un empty state claro, no ocultarse.

## Cómo detectar datos reales

Si las tabs muestran 0 pero el sidebar global muestra números mayores, el problema usualmente está en `brain_web.py` no extrayendo `page_slug` correctamente de `expand.related_pages`.

Verificar con curl:

```bash
curl -s 'http://localhost:8899/api/goals?context=personal' | python3 -m json.tool | grep page_slug
```

Si `page_slug` es `""` para goals/todos/reminders/journal que deberían tener proyecto, revisar `backend-relations-shape.md`.

## Cómo verificar navegación sin stacking

En DevTools console:

```js
document.querySelectorAll('#main > div.active').length
// Debe ser 1 después de cualquier navegación
```

Si es > 1, alguna vista agrega `.active` directamente en vez de usar `setActiveView()`.

Búsqueda rápida en el código:

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
grep -R "classList.add('active')" views/
```

Toda coincidencia debe ser reemplazada por `setActiveView('view-xxx')`.

## Verificación de cards clickeables

Toda card en project detail debe tener:
- `style="cursor:pointer"`
- `data-pb-page="slug"` (o atributo equivalente)
- listener que llame `window.showPage(slug)` y actualice el hash

Comprobar en console:

```js
document.querySelectorAll('#project-tab-content [data-pb-page]').length
```

## Checklist de cierre

- [ ] Todas las 11 tabs visibles con counts
- [ ] Contenido renderiza markdown con wikilinks clickeables
- [ ] Click en goal navega al slug del goal
- [ ] Click en todo navega al slug del todo
- [ ] Click en reminder navega al slug del reminder
- [ ] Click en journal navega al slug del journal
- [ ] Click en archivo navega al slug del archivo
- [ ] Wikilinks dentro del markdown navegan sin stacking
- [ ] Backlinks en wiki page navegan sin stacking
- [ ] `document.querySelectorAll('#main > div.active').length === 1` siempre
