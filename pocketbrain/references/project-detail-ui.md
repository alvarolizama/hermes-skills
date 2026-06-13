# Vista de detalle de proyecto — UI completa

> Guía para implementar/mantener la vista de detalle de proyecto en `scripts/views/project-detail.js`.

## Layout

1. **Breadcrumb**: `← Proyectos / Nombre del proyecto`.
2. **Header**: `<h1>` con título del proyecto.
3. **Dashboard de métricas**: grid de tarjetas con counts.
4. **Tabs del proyecto**: Contenido (default), Goals, Milestones, Ideas, Planes, Todo, Notas, Reminders, Journal, Archivos, Pages, Graph.
5. **Contenido del tab activo** en `#project-tab-content`.

## Tabs obligatorias

| Tab | Fuente de datos | Acción principal |
|-----|-----------------|------------------|
| Contenido | `project.body` renderizado con `mdToHtml` | Mostrar metadata + backlinks |
| Goals | `Store.state.goals` filtrados por `page_slug` | Cards navegables |
| Milestones | goals con `type === 'milestone'` | Cards navegables |
| Ideas | `Store.state.pages` con `page_type === 'idea'` relacionadas | Cards navegables |
| Planes | `Store.state.pages` con `page_type === 'plan'` relacionadas | Cards navegables |
| Todo | `Store.state.todos` filtrados por proyecto | Kanban con mover status |
| Notas | `Store.state.pages` con `page_type === 'note'` relacionadas | Cards navegables |
| Reminders | `Store.state.reminders` filtrados por proyecto | Lista |
| Journal | `Store.state.journal` filtrados por proyecto | Lista |
| Archivos | `Store.state.files` filtrados por proyecto | Lista |
| Pages | todas las páginas relacionadas (page_slug o body con `[[slug]]`) | Cards navegables |
| Graph | subgrafo del proyecto usando `renderProjectGraph` | Grafo local |

## Relación proyecto ↔ ítems

- `page_slug` es el campo clave en los endpoints de `brain_web.py`.
- Para ideas/planes/notas/pages, también se considera si el body contiene `[[slug-del-proyecto]]`.

## Kanban

- Columnas fijas: `backlog`, `this week`, `today`, `in progress`, `done`, `cancelled`.
- Cada tarjeta de tarea muestra botones para moverse a otra columna.
- Al mover, se hace `PATCH /api/todos/{id}/status/{status}` y se actualiza el store local.

## Navegación sin stacking

- `renderProjectPlaceholder` debe llamar `setActiveView('view-projects')`.
- Click en cards usa `window.showPage(slug)`, que setea `#tab=wiki&page=slug`.
- Verificar siempre con `document.querySelectorAll('#main > div.active').length === 1`.

## Estilos CSS

Clases clave en `web_ui.css`:
- `.project-breadcrumb`
- `.project-metrics`
- `.metric-card`
- `.project-tabs`
- `.project-item-card`
- `.kanban-board`, `.kanban-column`, `.kanban-card`, `.kanban-move`
- `.project-graph-view`
