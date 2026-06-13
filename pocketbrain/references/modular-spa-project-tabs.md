# Modular SPA: Project detail tabs

## Tabs condicionales por datos reales

La vista de proyecto debe mostrar tabs solo cuando hay datos que mostrar. No hardcodear tabs vacíos.

| Tab | Condición | Fuente de datos |
|-----|-----------|-----------------|
| Contenido | siempre | `project.body` |
| Goals | `goals.filter(g => g.type !== 'milestone').length > 0` | goals relacionados al proyecto |
| Milestones | `goals.filter(g => g.type === 'milestone').length > 0` | milestones relacionados al proyecto |
| Ideas | `relatedIdeaSlugs.length > 0` | páginas `page_type='idea'` que mencionan al proyecto |
| Planes | `relatedPlanSlugs.length > 0` | páginas `page_type='plan'` que mencionan al proyecto |
| Todo | `todos.filter(t => t.page_slug === slug).length > 0` | todos con `page_slug === project.slug` |
| Recordatorios | `reminders.filter(r => r.page_slug === slug).length > 0` | reminders con `page_slug === project.slug` |
| Notas | `relatedNoteSlugs.length > 0` | páginas `page_type='note'` que mencionan al proyecto |
| Journal | `journal.filter(j => j.page_slug === slug).length > 0` | journal con `page_slug === project.slug` |
| Entregables | `deliverables.filter(d => d.page_slug === slug).length > 0` | deliverables con `page_slug === project.slug` |
| Archivos | `files.filter(f => f.page_slug === slug).length > 0` | files con `page_slug === project.slug` |
| Graph | siempre | vis.js con goals, todos, reminders |

## Detectar Ideas/Planes/Notas relacionadas

El frontend puede detectar páginas que mencionan al proyecto mediante wikilinks en su body:

```javascript
const re = new RegExp('\\[\\[' + slug + '\\]\\]|\\[\\[' + slug + '\\|', 'i');
Store.state.pages.forEach(pg => {
  if (pg.page_type === 'project' || pg.slug === slug) return;
  if (pg.body && re.test(pg.body)) {
    const t = pg.page_type || 'concept';
    if (t === 'plan') ptypes.plan.push(pg.slug);
    else if (t === 'idea') ptypes.idea.push(pg.slug);
    else if (t === 'note') ptypes.note.push(pg.slug);
  }
});
```

**Requisito backend:** `brain.list_pages()` debe expandir `related_pages` para que las relaciones manuales via `[[wikilinks]]` en el body se devuelvan al frontend. Verificar:

```python
params = {
    'filter': "&&".join(filters),
    'perPage': per_page,
    'expand': 'domain,tags,related_pages',
}
```

## Síntoma: solo se ven Contenido y Graph

Si el project detail solo muestra **Contenido** y **Graph**, las causas probables son:

1. **Todos/goals/reminders no tienen `page_slug` asignado.** Verificar en el backend con:
   ```bash
   curl -s http://localhost:8899/api/todos | python3 -c "import json,sys; d=json.load(sys.stdin); print([(t['title'], t['page_slug']) for t in d])"
   ```
   Si `page_slug` está vacío para todos, el problema es la creación (no se pasó `related_slugs`/`project_slug`) o el backend no expandió `related_pages`.

2. **`brain.list_pages()` no expande `related_pages`.** Si `get_pages()` no incluye `expand='related_pages'`, las páginas tipo idea/plan/note no devuelven su relación al proyecto y el frontend no puede detectarlas por wikilinks.

3. **Case-sensitive matching.** Si el usuario escribió `[[PocketBrain]]` pero el slug es `pocketbrain`, la regex no detectará la relación. Normalizar a minúsculas:
   ```javascript
   const re = new RegExp('\\[\\[' + slug.toLowerCase() + '\\]\\]|\\[\\[' + slug.toLowerCase() + '\\|', 'i');
   ```

## Cards clickeables

Todas las cards de Ideas/Planes/Notas deben navegar a la página wiki:

```javascript
function renderLinkedCards(slugs) {
  const pages = Store.mapPages();
  return slugs.map(slug => {
    const p = pages[slug];
    return `<div class="card" style="cursor:pointer" data-pb-page="${esc(slug)}">
      <h3>${esc(p ? p.title : slug)}</h3>
    </div>`;
  }).join('');
}
```

Y agregar event listener delegado:

```javascript
container.querySelectorAll('[data-pb-page]').forEach(el => {
  el.addEventListener('click', () => {
    const slug = el.dataset.pbPage;
    if (slug && typeof window.showPage === 'function') window.showPage(slug);
  });
});
```

## Verificación visual

1. Abrir `#tab=projects&project=pocketbrain`.
2. Confirmar que aparecen tabs relevantes según los datos.
3. Clickear cada tab y verificar que no hay contenido vacío sin mensaje.
4. Clickear **Graph** y confirmar que vis.js renderiza el nodo del proyecto y, si hay relaciones, nodos conectados.

## Empty states

Todo tab que pueda estar vacío debe mostrar un mensaje, no quedar en blanco:

```javascript
if (!items.length) {
  content.innerHTML = '<p style="color:var(--mute)">No hay ' + tabName + '.</p>';
}
```
