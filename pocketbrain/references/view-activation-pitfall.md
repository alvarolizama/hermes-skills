# showIndex / View Activation Pitfall

## Síntoma

Clickear el link "Wiki" en el sidebar no hace nada visible. La función `showIndex()` existe (`typeof showIndex === 'function'`), los datos están cargados, pero la vista no cambia.

## Causa

`showIndex()` renderiza el HTML en `view-wiki` pero **no activa** la vista:

```javascript
function showIndex(){
  // ... build HTML ...
  document.getElementById('view-wiki').innerHTML = h;
  // ← FALTA: activar view-wiki, desactivar otras vistas, cerrar sidebar
}
```

Comparar con `showPage()` que SÍ lo hace:

```javascript
function showPage(slug){
  document.querySelectorAll('#main>div').forEach(function(d){d.classList.remove('active');});
  closeSidebar();
  document.getElementById('view-wiki').classList.add('active');
  // ... luego renderiza el contenido
}
```

## Fix

Agregar las 3 líneas de activación al inicio de `showIndex()`:

```javascript
function showIndex(){
  document.querySelectorAll('#main>div').forEach(function(d){d.classList.remove('active');});
  closeSidebar();
  document.getElementById('view-wiki').classList.add('active');
  // ... resto del código ...
}
```

## Regla

**Toda función que renderiza contenido en una vista DEBE:**
1. `querySelectorAll('#main>div').forEach(fn)` — desactivar todas las vistas
2. `closeSidebar()` — cerrar sidebar en mobile
3. `getElementById('view-xxx').classList.add('active')` — activar la vista correcta

Esto aplica a: `showPage()`, `showIndex()`, `renderProjectsView()`, `renderGoalsView()`, `renderTypeView()`, `renderTodosView()`, `renderRemindersView()`, `renderJournalView()`, y cualquier función nueva que se agregue.
