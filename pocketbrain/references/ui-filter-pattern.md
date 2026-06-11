# UI: Project filter via [[wikilinks]] o page_slug

Pattern for filtering views by project association in `web_ui.html`.

## The 3-option filter (Todos / Con proyecto / Sin proyecto)

Cada vista tiene un filtro con:

- **Todos** — sin filtro (default)
- **Con proyecto** — items asociados a un proyecto
- **Sin proyecto** — items sin proyecto asociado

## Type views: body wikilinks (Entidades, Conceptos, etc.)

Revisa el body de cada página en busca de `[[proyecto-slug]]`:

```javascript
// En la función renderTypeView(type):
var projS = {};
PAGES.filter(function(p){return p.page_type==='project';})
     .forEach(function(pr){projS[pr.slug]=pr.title;});

// Filtrar páginas que linkean a algún proyecto via [[wikilinks]]
var pages = allPages;
if(filt==='project')
  pages = allPages.filter(function(p){
    return p.body && Object.keys(projS).some(function(ps){
      return p.body.indexOf('[['+ps+']]')>=0 || p.body.indexOf('[['+ps+'|')>=0;
    });
  });
else if(filt==='noproject')
  pages = allPages.filter(function(p){
    return !p.body || !Object.keys(projS).some(function(ps){
      return p.body.indexOf('[['+ps+']]')>=0 || p.body.indexOf('[['+ps+'|')>=0;
    });
  });
```

## Todo/Reminders/Goals/Journal/Files/Deliverables: page_slug directo

Revisa el campo `page_slug` (relación directa):

| Opción | Value | Filter logic |
|--------|-------|-------------|
| Todos | `""` | Sin filtro |
| Con proyecto | `"project"` | `!!item.page_slug` (tiene página asociada) |
| Sin proyecto | `"noproject"` | `!item.page_slug` (no tiene página asociada) |

```javascript
// Select HTML (mismo patrón para TODAS las vistas)
'<select onchange="setXxxFilter(this.value)" ...>'
+'<option value="" ...>Todos</option>'
+'<option value="project" ...>Con proyecto</option>'
+'<option value="noproject" ...>Sin proyecto</option>'
+'</select>'

// Filter logic
if(_xxxFilter==='project')
  filtered = DATA.filter(function(item){return !!item.page_slug;});
else if(_xxxFilter==='noproject')
  filtered = DATA.filter(function(item){return !item.page_slug;});
```

## Pitfall: else-if atrapa valores reservados

⚠️ **NUNCA uses `else if(variable)` genérico cuando una opción es una keyword string.** Si el filter value `"project"` existe y haces:

```javascript
if(_filter==='noproject') filtered = ...;
else if(_filter) filtered = ...;  // ¡ATRAPA 'project'!
```

La línea `else if(_filter)` evalúa `"project"` como truthy y ejecuta el filtro genérico (ej. `page_slug === 'project'` — nunca da match). **Siempre usa `===` explícito:**

```javascript
if(_filter==='project') filtered = ...;       // Con proyecto
else if(_filter==='noproject') filtered = ...; // Sin proyecto
// Si hay filtros por slug específico, agregarlos DESPUÉS:
// else if(_filter) filtered = ...; // filtro por slug
```

## Layout correcto: H1 + select en view-header, tabs debajo

Todas las vistas siguen esta estructura vertical:

```html
<div class="view-header"><h1>Título</h1><select>...filtro...</select></div>
<div class="project-tabs" style="margin:12px 0">...tabs de estado...</div>
<!-- contenido -->
```

| Vista | En view-header (junto al H1) | Debajo con margin |
|-------|------------------------------|-------------------|
| Todo | Select (Todos/Con proyecto/Sin proyecto) | _(ninguno)_ |
| Goals | Select (Todos/Con proyecto/Sin proyecto) | Status tabs margin:12px 0 |
| Milestones | Select (Todos/Con proyecto/Sin proyecto) | Status tabs margin:12px 0 |
| Reminders | Select (Todos/Con proyecto/Sin proyecto) | Status tabs margin:12px 0 |
| Type views | Select (Todos/Con proyecto/Sin proyecto) | _(ninguno)_ |
| Journal | Select proyecto + Month/Year picker | _(ninguno)_ |
| Files | Select (Todos/Con proyecto/Sin proyecto) | _(ninguno)_ |
| Deliverables | Select (Todos/Con proyecto/Sin proyecto) | _(ninguno)_ |

**Regla:** el filter select va DENTRO del view-header, a la derecha del H1. Los status tabs (cuando existen, como en Goals/Reminders) van debajo con `margin:12px 0`. NUNCA pongas status tabs inline con el H1.

## Goals/Milestones: render target

Goals y Milestones usan `renderGoalsView(typeFilter)`. Cuando `typeFilter='milestone'`, renderiza en `view-milestones` en vez de `view-goals`:

```javascript
var cid = typeFilter==='milestone' ? 'view-milestones' : 'view-goals';
document.getElementById(cid).innerHTML = h;
```

## Síntesis: qué filtro usa cada vista

| Vista | Mecanismo | Filter value | Función |
|-------|-----------|-------------|---------|
| Type views (entity, concept, etc.) | Body contiene `[[slug]]` | `"project"` / `"noproject"` | `renderTypeView()` |
| Goals, Milestones | `page_slug` directo | `"project"` / `"noproject"` | `renderGoalsView()` |
| Todo | `page_slug` directo | `"project"` / `"noproject"` | `renderTodosView()` |
| Reminders | `page_slug` directo | `"project"` / `"noproject"` | `renderRemindersView()` |
| Journal | `page_slug` directo | `"project"` / `"noproject"` | `renderJournalView()` |
| Files | `page_slug` directo | `"project"` / `"noproject"` | `renderFilesView()` |
| Deliverables | `page_slug` directo | `"project"` / `"noproject"` | `renderDeliverablesView()` |

**Regla general:** si agregas un nuevo filter con opción `"project"`, asegúrate de que el handler `if/else` la maneje con `=== 'project'` y no caiga en un `else if(filterVar)` genérico.

## Cómo agregar un nuevo type view

1. **Sidebar link** en `buildSidebar()`:
   ```javascript
   h+='<a href="#" class="nav-link" onclick="showTab(\'type_NUEVO\');return false" data-search="nuevo">...';
   ```

2. **View container** en el HTML:
   ```html
   <div id="view-type-NUEVO" class="view"></div>
   ```

3. **Views map** en `showCurrentView()`:
   ```javascript
   type_NUEVO:'view-type-NUEVO',
   ```

4. **Labels/icons** en `renderTypeView()`:
   ```javascript
   var labels = {... 'nuevo':'Nuevos'};
   ```

5. **Graph colors** en `renderGraph()`:
   ```javascript
   var GCOLORS = {... 'nuevo':'#HEXCODE'};
   var GTYPE_NAMES = {... 'nuevo':'Nuevos'};
   ```
