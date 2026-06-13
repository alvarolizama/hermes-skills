# UI Consistency Patterns for PocketBrain Web

Class-level patterns for keeping the PocketBrain web UI visually and interactively consistent across all list views, tabs, kanban boards, and detail pages.

## Header pattern

Every list/detail view must have a `.view-header` with this structure:

```html
<div class="view-header">
  <div class="view-title-row">
    <h1>${icon(name, 20)}<span>Title</span></h1>
    <!-- filter select or action button goes here -->
  </div>
  <p class="view-subtitle">${count} items · extra metadata</p>
</div>
```

CSS in `web_ui.css` makes `h1` an inline flex so the SVG icon aligns with the label.

## Tab / status-filter pattern

Use the shared `Tabs` component from `components/Tabs.js`. Every tab item can carry an `icon` name; the component renders SVG + label + `.nav-count` badge.

```js
Tabs({
  items: [
    { id: 'all', label: 'Todos', icon: 'squares-2x2' },
    { id: 'active', label: 'Activos', icon: 'bolt' }
  ],
  active: currentId,
  counts: { all: 12, active: 3 }
});
```

## Filter select pattern

All list views use the same three options:

```html
<select class="filter-select">
  <option value="">Todos</option>
  <option value="project">Con proyecto</option>
  <option value="noproject">Sin proyecto</option>
</select>
```

Implementation differs by view (some filter by `page_slug`, others by body wikilinks), but the UX must be identical.

## Kanban pattern

Both the global Todo view and the project-detail Todo tab use the same CSS classes:

- `.kanban-board` — flex container
- `.kanban-column` — individual column
- `.kanban-column-header` — label + count
- `.kanban-column-body` — scrollable card container
- `.kanban-card` — task card
- `.kanban-actions` — move/status buttons
- `.kanban-move` — status-change button

Column headers should include a Heroicon:

| Column      | Icon           |
|-------------|----------------|
| backlog     | archive-box    |
| this week   | calendar       |
| today       | sun            |
| in progress | arrow-path     |
| done        | check-circle   |
| cancelled   | x-circle       |

## Card pattern

Cards are clickable, have consistent padding, hover state, and use `data-pb-page` for delegated navigation. Optional meta line below the title. No emoji.

## No emoji rule

Replace any emoji with Heroicons:

| Emoji | Replacement        |
|-------|--------------------|
| ✅    | check-circle       |
| ⚠     | exclamation-triangle |
| 📎    | paper-clip         |
| 📅    | calendar           |

## Breadcrumb navigation

Views that are not root-level should expose a breadcrumb so the user can go back. Use `href="javascript:void(0)"` and data attributes, never `href="#"`.

| View | Breadcrumb pattern | Target |
|------|--------------------|--------|
| Project detail | `← Proyectos / {title}` | `showTab('projects')` |
| Wiki page | `Wiki · {page_type_label} · {title}` | `showTab('wiki')`, `showTab('type_{page_type}')` |
| Type view (optional) | `← Wiki` or none | `showTab('wiki')` if added |

### Breadcrumb container requirement

Every `page_type` that can appear in the wiki breadcrumb must have a matching `<div id="view-type-{page_type}">` in `web_ui.html`. If the container is missing, `showTab('type_{page_type}')` will update the hash but leave the main area blank. Verified by checking `document.querySelectorAll('#main > div.active').length === 1` after the click.

Required containers:
- `view-type-project`
- `view-type-deliverable`
- `view-type-concept`
- `view-type-entity`
- `view-type-comparison`
- `view-type-query`
- `view-type-raw`
- `view-type-plan`
- `view-type-note`
- `view-type-idea`
- `view-type-file`

## Filter state and Store.setFilter

`Store.setFilter(view, value)` validates keys against `initialState.filters`. Type views use the `page_type` as the filter key (e.g. `concept`, `project`), which is not in the default filter map. Either pre-register all page_types in `initialState.filters` or make `setFilter` silently ignore unknown keys so the select still works for every type view.

## Verification checklist

After a UI consistency pass, open each view and confirm:

1. Header shows an icon next to the title.
2. Status/filter tabs show icons and counts.
3. Filter select is `Todos / Con proyecto / Sin proyecto`.
4. Cards are clickable and navigate to the right page.
5. No emoji anywhere.
6. Only one active view: `document.querySelectorAll('#main > div.active').length === 1` after every navigation.
7. Breadcrumbs navigate to an existing container (no blank main area).
8. `node --check` passes for all modified JS files.
9. `python3 -m py_compile brain.py brain_web.py` passes.

## Hash state

Every tab/filter change must call `setHashParams()` so the state is bookmarkable and survives reload. Add the new param to `restoreFromHash`/router logic.

## Common view icon mapping

| View         | Header icon              |
|--------------|--------------------------|
| Proyectos    | squares-2x2              |
| Goals        | flag                     |
| Milestones   | check-circle             |
| Todo         | clipboard-document-list  |
| Reminders    | bell                     |
| Journal      | book-open                |
| Archivos     | paper-clip               |
| Wiki         | bars-3                   |
| Graph        | share                    |
| Lint         | shield-check             |
| Conceptos    | light-bulb               |
| Entidades    | users                    |
| Comparaciones| chart-pie                |
| Consultas    | magnifying-glass         |
| Raw          | paper-clip               |
| Planes       | calendar-days            |
| Notas        | clock                    |
| Ideas        | sparkles                 |
| project      | squares-2x2              |
| deliverable  | document-text            |
