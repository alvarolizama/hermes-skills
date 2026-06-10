ww76mtkpqss4j7q` y `p.slug` = `viaje-a-japon-2026`, la comparación siempre falla y el contador muestra **0 goals**.

## Solución en Backend

```python
def get_goals():
    goals = brain.pb.all("brain_goals", filter="(brain='" + brain._context_id + "')", expand="page")
    return [{"id": g["id"], "title": g.get("title",""), "type": g.get("type","goal"),
        "status": g.get("status","planned"), "progress": g.get("progress", 0) or 0,
        "deadline": (g.get("deadline","") or "")[:10], "description": g.get("description","") or "",
        "page": g.get("page","") or "", "page_slug": (g.get("expand",{}).get("page", {}) or {}).get("slug","") or "",
        "parent": g.get("parent","") or ""} for g in goals]
```

## Cambios en Frontend (web_ui.html)

Actualizar todos los lugares donde se filtra goals por proyecto:

```javascript
// 1. Lista de goals con filtro por proyecto (Views.goals)
else if(_goalFilter) filtered = GOALS.filter(function(g){
    return g.page_slug === _goalFilter;
});

// 2. Tarjetas de proyecto (Views.projects)
active.forEach(function(p){
    var pgoals = GOALS.filter(function(g){return g.page_slug === p.slug;}).length;
});

// 3. Detalle de proyecto (Views.project)
var pgoals = GOALS.filter(function(g){return g.page_slug === slug;});

// 4. Detalle de página wiki (wiki_showPage)
var pgoals = GOALS.filter(function(g){return g.page_slug === slug;});
```

## Verificación

- Abrir el browser en `http://localhost:8080/`
- Ir a **Proyectos**
- Las tarjetas deben mostrar contadores reales: `5 goals · 6 tareas` (no `0 goals · 0 tareas`)
- Ir a **Goals** y usar el dropdown para filtrar por proyecto
- Deben aparecer solo los goals de ese proyecto

## Lección

PocketBase expand es necesario para obtener atributos de relación. Sin `expand`, las relaciones devuelven solo ID. El frontend necesita los slugs legibles para filtrar. Mantener ambos (`page` para el backend, `page_slug` para el frontend) es el patrón correcto.