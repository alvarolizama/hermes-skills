# PocketBrain — Collection Unification Pattern

Como migrar colecciones separadas (brain_todos, brain_goals, etc.) a brain_pages usando page_type como discriminante.

## El patron

| Coleccion legacy | page_type | Metodo |
|-----------------|-----------|--------|
| brain_todos | todo | create_todo() -> create_page(page_type='todo') |
| brain_goals | goal, milestone | create_goal(type=...) -> create_page(page_type=type) |
| brain_reminders | reminder | create_reminder() -> create_page(page_type='reminder') |
| brain_journal | journal | journal_write() -> create_page(page_type='journal') |
| brain_files | file | create_page(page_type='file', filepath=...) |
| brain_deliverables | deliverable | create_page(page_type='deliverable', filepath=...) |

## Sidebar: agregar un nuevo tipo al menu

Cada tipo necesita 4 cosas en web_ui.html:

1. buildSidebar(): link con onclick="showTab('type_NUEVO')" y conteo desde PAGES
2. HTML container: <div id="view-type-NUEVO" class="view"></div> en #main
3. views map en showCurrentView(): 'type_NUEVO':'view-type-NUEVO'
4. Handler else if(_currentTab && _currentTab.startsWith('type_')) (generico, ya existe)

Si olvidas #3, la vista queda en blanco al hacer click.
