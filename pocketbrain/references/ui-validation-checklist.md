# PocketBrain UI Validation Checklist

Use this after any frontend change in `brain_web.py` / `web_ui.html` / `scripts/`.

## 1. Syntax / static checks

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 -m py_compile brain.py brain_web.py
node --check app.js router.js store.js api.js markdown.js components/Tabs.js components/Icon.js \
  views/projects.js views/todos.js views/reminders.js views/journal.js views/files.js \
  views/type.js views/goals.js views/wiki.js views/graph.js views/lint.js \
  views/milestones.js views/project-detail.js
```

## 2. Server health

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8899/
# expect 200
```

## 3. Browser hash walkthrough

Visit each URL and verify `#main > div.active` length is exactly 1.

- `#tab=projects` — projects list renders, H1 has icon, cards visible.
- `#project=<slug>&ptab=content` — breadcrumb ← Proyectos / Title, metrics grid, content markdown.
- `#project=<slug>&ptab=goals` — tabs wrap, counts correct, cards navigate to page.
- `#project=<slug>&ptab=todo` — kanban columns, move buttons work.
- `#project=<slug>&ptab=graph` — **network graph renders with nodes + edges**, legend visible.
- `#project=<slug>&ptab=pages` — related pages list.
- `#tab=goals`, `#tab=milestones` — tabs have icons, cards clickable.
- `#tab=todos` — global kanban renders.
- `#tab=reminders` — tabs Hoy/Esta semana/etc work.
- `#tab=journal` — month filter works.
- `#tab=files` — file cards render.
- `#tab=type_entity`, `#tab=type_concept`, `#tab=type_comparison`, `#tab=type_query`, `#tab=type_raw` — summaries render markdown, not escaped text or giant headings.
- `#tab=wiki` — index tabs with icons, cards navigate.
- `#tab=wiki&page=<slug>&wtab=content` — breadcrumb Wiki / Type / Title works, type link navigates.
- `#tab=type_project` — must have container in `web_ui.html`.
- `#tab=graph` — global graph renders.
- `#tab=lint` — lint results render.

### Mobile layout check

Resize the viewport to 375-768 px and verify:

1. Header title is at the top, not pushed aside by the breadcrumb.
2. Breadcrumb appears below the title, not beside it.
3. Filter select is below the breadcrumb and reachable.
4. Tab bar wraps; the rightmost tabs are visible without horizontal scrolling.
5. Project detail metrics grid uses fewer columns (e.g., `grid-template-columns: repeat(auto-fill, minmax(120px, 1fr))`).

Use DevTools device emulation or run in the console:

```js
window.innerWidth = 375;
window.innerHeight = 812;
```

Then re-check `#tab=milestones` and `#project=<slug>&ptab=graph`.

## 4. Common regressions to check

| Symptom | Likely cause | Quick check |
|---------|--------------|-------------|
| Tab bar clips / Graph tab not visible | `.project-tabs` has `overflow-x:auto` without `flex-wrap:wrap` | `.project-tabs { flex-wrap: wrap; height: auto; }` |
| Clicking project card does nothing | `renderProjectPlaceholder` not called or `showProject` signature mismatch | `typeof window.showProject === 'function'` |
| Project detail tabs unresponsive or multi-fire | `click` listener added on every render without cleanup | remove previous handler before adding new one |
| Project graph tab blank | `renderProjectGraph` expects `d.rems` but `collectProjectData` returns `d.reminders` | use fallbacks: `const reminders = d.reminders \|\| d.rems \|\| []` |
| Type view summaries show raw `**markdown**` or giant headings | summary passed through `esc()` or body heading leaked into card | strip markdown or render with `.card .md-content` CSS clamp |
| Wiki breadcrumb type link blanks main area | missing `<div id="view-type-<type>">` in `web_ui.html` | verify all `page_type` values have containers |
| `Store.setFilter` throws for type views | `initialState.filters` lacks keys for page_types | make `setFilter` ignore unknown keys silently |
| Changes not visible after server restart | browser cache `max-age:3600` | use `?nocache=N` or hard refresh |
| Mobile header looks broken (breadcrumb beside title) | `.view-header` not stacked on mobile | add media query flex column with breadcrumb order 2, title order 1 |

## 5. Verification expressions

```javascript
// active views count
document.querySelectorAll('#main > div.active').length === 1

// project graph rendered
!!document.querySelector('#project-graph-view canvas, #project-graph-view svg')

// type view markdown rendered (no literal asterisks in card text)
!document.querySelector('.cards-grid').innerText.includes('**')

// tab bar wraps and shows Graph
const tabs = document.querySelector('.project-tabs');
tabs.scrollWidth <= tabs.clientWidth || getComputedStyle(tabs).flexWrap === 'wrap'
```
