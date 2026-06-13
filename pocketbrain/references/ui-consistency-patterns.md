# UI Consistency Patterns for PocketBrain Web

Reference for keeping the PocketBrain web UI visually and behaviorally consistent across all views: projects, goals, milestones, todos, reminders, journal, files, type views, wiki, graph, lint.

## Header pattern (every list/detail view)

Every view uses the same `view-header` structure:

```html
<div class="view-header">
  <div class="view-title-row">
    <h1>${icon('heroicon-name', 20)}<span>Title</span></h1>
    <select class="filter-select"> ... </select>
  </div>
  <p class="view-subtitle">${count} items</p>
</div>
```

Rules:
- Title always has a Heroicon SVG to its left.
- Filter select (Todos / Con proyecto / Sin proyecto) is inside `view-title-row`, aligned right.
- Subtitle count goes below in `view-subtitle`.

## Icon per view

| View | Header icon |
|------|-------------|
| Proyectos | `squares-2x2` |
| Goals | `flag` |
| Milestones | `check-circle` |
| Todo | `clipboard-document-list` |
| Reminders | `bell` |
| Journal | `book-open` |
| Archivos | `paper-clip` |
| Wiki (index) | `bars-3` |
| Wiki page | `document-text` |
| Graph | `share` |
| Lint | `shield-check` |
| Conceptos | `light-bulb` |
| Entidades | `users` |
| Comparaciones | `chart-pie` |
| Consultas | `magnifying-glass` |
| Raw | `paper-clip` |
| Planes | `calendar-days` |
| Notas | `clock` |
| Ideas | `sparkles` |

## Tabs / status filters with icons

Use `components/Tabs.js` everywhere. Pass an `icon` per item:

```js
const items = [
  { id: 'all', label: 'Todos', icon: 'squares-2x2' },
  { id: 'active', label: 'Activos', icon: 'bolt' },
  { id: 'backlog', label: 'Backlog', icon: 'archive-box' },
  { id: 'completed', label: 'Terminados', icon: 'check-circle' },
  { id: 'cancelled', label: 'Cancelados', icon: 'x-circle' }
];
Tabs({ items, active, counts });
```

Common status icons:
- All / Todos → `squares-2x2`
- Active / Activos → `bolt`
- Backlog → `archive-box`
- Completed / Done / Terminados → `check-circle`
- Cancelled / Cancelados → `x-circle`
- Today / Hoy → `sun`
- This week / Esta semana → `calendar-days`
- Upcoming / Próximos → `arrow-right-circle`
- Overdue / Atrasados → `exclamation-circle`

## Kanban column icons

For both project-detail Todo tab and global Todo view:

| Column | Icon |
|--------|------|
| Backlog | `archive-box` |
| This week | `calendar` |
| Today | `sun` |
| In progress | `arrow-path` |
| Done | `check-circle` |
| Cancelled | `x-circle` |

Use the same CSS classes: `.kanban-board`, `.kanban-column`, `.kanban-column-header`, `.kanban-count`, `.kanban-card`, `.kanban-actions`, `.kanban-move`.

## Cards

Cards must be clickable (except when they contain explicit action buttons). Wrap them in `.cards-grid` and use consistent markup:

```html
<div class="cards-grid">
  <div class="card" data-pb-page="${slug}" style="cursor:pointer">
    <div style="display:flex;align-items:center;gap:8px">
      ${icon('heroicon-name', 16)}
      <h3>${title}</h3>
    </div>
    <div style="font-size:12px;color:var(--mute);margin-top:4px">${meta}</div>
  </div>
</div>
```

Rules:
- No inline `style="padding:12px;margin-bottom:8px"` on every card — rely on `.cards-grid` and `.card`.
- Add a small icon before the title when the card represents a typed entity.
- Meta line uses `font-size:12px;color:var(--mute)`.

## No emoji in UI

Replace any emoji with Heroicons:
- `✅` → `check-circle` icon
- `⚠️` → `exclamation-triangle` icon
- `←` → `arrow-left` icon
- `🗑️` / archive metaphors → `archive-box`

## Filter select uniformity

All list views use the same three options:

```html
<select class="filter-select">
  <option value="">Todos</option>
  <option value="project">Con proyecto</option>
  <option value="noproject">Sin proyecto</option>
</select>
```

Implementation note: views filter by different mechanisms (`page_slug` for goals/todos/reminders/files, `[[project-slug]]` in body for type views and projects), but the UI is identical.

## URL hash state

Every tab/filter selection should update the hash via `setHashParams()` so the state is bookmarkable:
- Goals/Milestones: `gstatus`
- Reminders: `rstatus`
- Todo: consider `tstatus`
- Journal: project filter + month
- Wiki index: `wtab`
- Wiki page: `wtab`
- Project detail: `ptab`

## Verification checklist after UI changes

1. `node --check components/*.js views/*.js`
2. `python3 -m py_compile brain.py brain_web.py`
3. Start `brain_web.py --context personal --port 8899`
4. Visit each `#tab=` and confirm header icon renders.
5. Confirm every tab/status filter renders its icon.
6. Confirm no stacking: `document.querySelectorAll('#main > div.active').length === 1` after every navigation.
7. Click cards and confirm navigation hash changes correctly.
8. Hard refresh browser after JS/CSS changes (cache max-age: 3600).

## Related references

- `references/frontend-icon-patterns.md` — Heroicons registry and helper
- `references/web-ui-patterns.md` — tabs, view stacking, hash state
- `references/ui-filter-pattern.md` — filter select behavior
- `references/sidebar-layout.md` — sidebar icon alignment
