# PocketBrain — Adding a new page_type

Checklist para agregar un nuevo `page_type` a PocketBrain. Cada vez que agregas uno, debes tocar estos 6 lugares exactamente.

## The 6-Step Checklist

### Step 1: BRAIN_SCHEMA in `brain.py`

File: `pocketbrain/scripts/brain.py`

Add the new type to the `page_type` field's `values` array:

```python
# Line ~102
{"name": "page_type", "type": "select", "required": True,
 "values": ["entity", "concept", "comparison", "query", "raw", "project",
            "plan", "note", "idea",
            "todo", "goal", "milestone", "okr", "reminder", "journal"],
 "maxSelect": 1},
```

### Step 2: `suggest_page_type()` in `brain.py`

Add heuristic detection before the `entity` check. Rules:
- Keep in priority order: project > raw > comparison > query > plan > note > idea > entity > concept
- `concept` is the fallback default
- Keywords should match common Spanish and English terms

### Step 3: Graph colors in `web_ui.html`

Add color and label in BOTH graph functions:

**Global graph** (`renderGraph()`): update `GCOLORS` and `GTYPE_NAMES`
**Project graph** (`renderProjectGraph()`): update `ptLabels` and `ptColors`

### Step 4: SKILL.md

Add a row to the page_types table.

### Step 5: `references/schema.md`

Add the new type to the `page_type` field values list.

### Step 6: Runtime sync + server restart

```bash
cp ~/Repos/personal/hermes-skills/pocketbrain/scripts/brain.py ~/.hermes/skills/...
cp ~/Repos/personal/hermes-skills/pocketbrain/scripts/web_ui.html ~/.hermes/skills/...
cp ~/Repos/personal/hermes-skills/pocketbrain/SKILL.md ~/.hermes/skills/...
cp ~/Repos/personal/hermes-skills/pocketbrain/references/schema.md ~/.hermes/skills/...
kill -9 $(lsof -i :8899 | grep LISTEN | awk '{print $2}')
cd ~/.hermes/skills/... && python3 brain_web.py --port 8899 --context personal
```

## Color palette

| page_type | Color | Hex |
|-----------|-------|-----|
| entity | Green | `#4CAF50` |
| concept | Blue | `#2196F3` |
| comparison | Orange | `#FF9800` |
| query | Purple | `#9C27B0` |
| raw | Grey | `#607D8B` |
| project | Pink | `#E91E63` |
| plan | Brown | `#795548` |
| note | Cyan | `#00BCD4` |
| idea | Deep Orange | `#FF5722` |
| goal | Green | `#4CAF50` |
| milestone | Orange | `#FF9800` |
| todo | Purple | `#9C27B0` |
| reminder | Yellow | `#FFC107` |
| journal | Brown-teal | `#795548` |
| file | Blue-grey | `#607D8B` |
| deliverable | Teal | `#00BCD4` |

## Sidebar: adding vs reordering

**Adding a type to the sidebar** (`buildSidebar()` in `web_ui.html`):
- Add the `h+='<a ...>'` line in the desired position
- Add a unique icon from `_ICONS` (or add a new Heroicon path)
- Add `closeSidebar()` call is already in `showTab()` — no extra step needed
- **After editing, verify**: `grep -c "showTab.*'type_NEWTYPE'" web_ui.html` must return 1. Duplicate lines cause unbalanced braces and JS parsing failure

**Reordering sidebar items**:
- Replace the entire block of link lines in the right order
- Update the project tabs order to match
- Update `var map={...}` in `switchProjectTab()` to match new tab order
- **Critical: check for duplicate lines** after replacement. Use `grep -n "showTab"` to verify no duplicates exist. A single duplicate line = entire script fails to parse = page stuck on "Cargando..."
- Update the `views` map in `showCurrentView()` if adding new view types

## Removing a collection (reverse migration)

When moving data FROM a dedicated collection TO `brain_pages`:

1. Remove collection definition from `BRAIN_SCHEMA`
2. Remove from `CREATION_ORDER`
3. Remove from `SELF_REF_FIELDS` (if applicable)
4. Remove from `nuke_context()` order list
5. Update all method references (search: `'brain_collectionname'`)
6. Update all endpoint references in brain_web.py
7. Remove `goal` field from brain_files/brain_deliverables if they referenced it
8. Commit: "clean: removed legacy collection brain_X from schema and code"
