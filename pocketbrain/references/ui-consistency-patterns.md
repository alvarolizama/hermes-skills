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

Every `page_type` that can appear in the wiki breadcrumb must have a matching `<div id="view-type-{page_type}">` in `web_ui.html`. If the container is missing, `showTab('type_{page_type}')` will update the hash but leave the main area blank (no error visible to the user). Verify with `document.querySelectorAll('#main > div.active').length === 1` after the click; if it is 0, the container is missing.

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

When adding a new `page_type`, add its container to `web_ui.html` before using it in a breadcrumb or sidebar link.

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

## Browser cache during UI iteration

`brain_web.py` serves static assets with `Cache-Control: max-age=3600`. After editing JS/CSS and restarting the server, a normal page load may still use the cached files, causing confusing results (empty snapshots, missing icons, stale behavior).

Patterns to avoid this:

- Append `?nocache=N` to test URLs: `http://localhost:8899/?nocache=12#tab=projects`. Bump `N` on each iteration.
- Or open DevTools and enable "Disable cache" while testing.
- Or force hard refresh (`Cmd+Shift+R` / `Ctrl+Shift+R`).
- Verify the server is serving the new code with `curl -s http://localhost:PORT/ | grep -n 'changed-string'`.

## Back-to-root breadcrumb pattern

Any view that is not the root Projects list should expose a breadcrumb line so the user can return without using the sidebar. The minimal pattern is `← Proyectos / {SectionName}`.

Implementation:

```html
<div class="project-breadcrumb" style="margin-bottom:8px">
  <a href="javascript:void(0)" data-pb-back-projects>
    ${icon('arrow-left', 12)}<span>Proyectos</span>
  </a>
  <span class="project-breadcrumb-sep">/</span>
  <span>{SectionName}</span>
</div>
```

And bind the link:

```js
const back = container.querySelector('[data-pb-back-projects]');
if (back) {
  back.addEventListener('click', e => {
    e.preventDefault();
    if (typeof window.showTab === 'function') window.showTab('projects');
  });
}
```

Apply this to: Goals, Milestones, Todo, Reminders, Journal, Files, all type views, Wiki, Graph, Lint.

## Project detail tab bar must wrap

Project detail has 12 tabs. If `.project-tabs` is configured as a single horizontal scrollable row (`overflow-x:auto` without `flex-wrap`), the rightmost tabs (Archivos, Pages, Graph) will be hidden outside the viewport on common screen sizes. Users will not see them and may report that the Graph tab does not exist.

Fix in `web_ui.css`:

```css
.project-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--hairline);
  margin-bottom: 16px;
  overflow-x: auto;
  margin-top: 12px;
  flex-wrap: wrap;   /* show all tabs */
  height: auto;
}
```

Verify with `document.querySelectorAll('.project-tabs a').length === 12` and that each tab label is visible.

## Project graph tab must render a real network

When the user selects the Graph tab inside a project, the main area must show a vis.js network with nodes and edges, not a blank container.

Common causes of a blank project graph:

1. **Wrong data keys.** `renderProjectGraph()` expects `goals`, `todos`, and `reminders`. If the caller passes `rems` or omits a key, the arrays are undefined and no nodes are created.
   - Fix: `const reminders = d.reminders || d.rems || [];`
2. **Graph tab not visible.** See "Project detail tab bar must wrap" above.
3. **Container missing or wrong size.** The container must be in the DOM before vis.Network initializes and must have a defined height.
   - `web_ui.css`: `.project-graph-view { width: 100%; height: 420px; ... }`
4. **Listener duplication in project detail.** If `renderProjectPlaceholder()` adds a new delegated `click` listener on every render without removing the old one, tab switches may fire multiple times and re-render inconsistently.
   - Fix: store the handler on the container, remove it before adding a new one:
     ```js
     if (container._projectClickHandler) {
       container.removeEventListener('click', container._projectClickHandler);
     }
     container._projectClickHandler = onProjectClick;
     container.addEventListener('click', container._projectClickHandler);
     ```

Verification expressions:

```js
// graph tab is present
!!document.querySelector('[data-pb-ptab="graph"]')

// graph rendered something
!!document.querySelector('#project-graph-view canvas, #project-graph-view svg')

// active views count is 1
document.querySelectorAll('#main > div.active').length === 1
```

## Type view summaries must render markdown

Cards in type views (`type_entity`, `type_concept`, `type_comparison`, `type_query`, `type_raw`, etc.) display the page summary below the title. Summaries may contain markdown (e.g., `**bold**`, `[[wikilinks]]`). Escaping the summary with `esc()` shows literal asterisks and brackets to the user.

Fix in `views/type.js`:

```js
const summaryHtml = p.summary
  ? (window.mdToHtml ? window.mdToHtml(p.summary) : mdToHtml(p.summary))
  : '';

html += `<div class="card ..." data-pb-page="${esc(p.slug)}">`
  + `<div ...><h3>${esc(p.title)}</h3></div>`
  + (summaryHtml ? `<div class="md-content" ...>${summaryHtml}</div>` : '')
  + `</div>`;
```

After rendering, bind markdown links if summaries may contain `[[wikilinks]]`:

```js
const grid = container.querySelector('.cards-grid');
if (grid && typeof bindMarkdownLinks === 'function') bindMarkdownLinks(grid);
```

Verify with:

```js
!document.querySelector('.cards-grid').innerText.includes('**')
```

## Hash walkthrough leaves exactly one active view

After every navigation, confirm the SPA has only one active view. Stacking happens silently when a view activation function forgets to deactivate siblings.

```js
document.querySelectorAll('#main > div.active').length === 1
```

Run this after: Projects → Project detail → each tab → card click → back to Projects → Wiki page → breadcrumb links → type views → Graph → Lint.

## Static checks before browser verification

Always run before testing in the browser:

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 -m py_compile brain.py brain_web.py
node --check app.js router.js store.js api.js markdown.js \
  components/Tabs.js components/Icon.js views/*.js
```

See `references/ui-validation-checklist.md` for a full post-change checklist.


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
