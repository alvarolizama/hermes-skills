# PocketBrain Web UI Redesign — Implementation Plan

> **Goal:** Rediseñar el sidebar y las vistas del web UI para que muestren solo proyectos activos, filtros por proyecto, reminders ordenados por urgencia, journal por mes, y wiki directo.

**Architecture:** Todo el frontend vive en `brain_web.py` (HTML+CSS+JS inline + endpoints API). El backend es `brain.py`. Ambos en `~/.hermes/skills/productivity/pocketbrain/scripts/`.

---

## Task 1: Agregar campos de status a brain_pages (schema)

**Objetivo:** Los proyectos (page_type=project) necesitan `status`, `completed_date`, `cancelled_date`, `retrospective`.

**Files:**
- Modify: `brain.py` — `BRAIN_SCHEMA["brain_pages"]["fields"]`

**Step 1:** Agregar campos al schema en `brain.py` dentro de `brain_pages.fields`:

```python
{"name": "status", "type": "select", "values": ["active", "completed", "cancelled"], "maxSelect": 1},
{"name": "completed_date", "type": "date"},
{"name": "cancelled_date", "type": "date"},
{"name": "retrospective", "type": "text"},
```

**Step 2:** Parchar la colección en PocketBase con PATCH (los campos nuevos se agregan a las existentes):

```python
pb.update_collection('brain_pages', {'fields': current_fields + new_fields})
```

**Verificación:** `pb.get_collection('brain_pages')` debe mostrar los 4 nuevos campos.

---

## Task 2: Métodos `complete_project()` y `cancel_project()` en Brain

**Objetivo:** Poder marcar proyectos como completados/cancelados con fecha y retrospectiva.

**Files:**
- Modify: `brain.py` — agregar métodos a la clase `Brain`

**Step 1:** Agregar `complete_project(slug, retrospective='')`:

```python
def complete_project(self, slug: str, retrospective: str = '') -> dict:
    page = self.get_page(slug)
    if not page: raise ValueError(f"Proyecto '{slug}' no encontrado")
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.000Z')
    return self.pb.update('brain_pages', page['id'], {
        'status': 'completed',
        'completed_date': now,
        'retrospective': retrospective or page.get('retrospective', ''),
    })
```

**Step 2:** Agregar `cancel_project(slug, retrospective='')`:

```python
def cancel_project(self, slug: str, retrospective: str = '') -> dict:
    page = self.get_page(slug)
    if not page: raise ValueError(f"Proyecto '{slug}' no encontrado")
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.000Z')
    return self.pb.update('brain_pages', page['id'], {
        'status': 'cancelled',
        'cancelled_date': now,
        'retrospective': retrospective or page.get('retrospective', ''),
    })
```

**Verificación:** Crear un proyecto, marcarlo como completed, verificar que `status='completed'` y `completed_date` no esté vacío.

---

## Task 3: Método `get_reminders()` ordenado por urgencia

**Objetivo:** Devolver reminders ordenados: atrasados → hoy → esta semana → resto (más próximo a más lejano).

**Files:**
- Modify: `brain.py` — agregar `get_reminders()` a `Brain`

**Step 1:** Implementar:

```python
def get_reminders(self, project_slug: str = None) -> list:
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    # Get all incomplete reminders for this context
    reminders = self.pb.all('brain_reminders', 
        filter=f"(brain='{self._context_id}' && done=false)",
        sort='date', perPage=500)
    
    # Score: overdue=0, today=1, this_week=2, future=3
    from datetime import datetime as dt
    now = dt.now(timezone.utc)
    today_dt = dt.strptime(today, '%Y-%m-%d')
    week_end = today_dt.replace(day=today_dt.day + (6 - today_dt.weekday()))
    
    def score(r):
        d = r.get('date', '')
        if not d: return 999
        rd = dt.strptime(d[:10], '%Y-%m-%d')
        if rd < today_dt: return 0       # overdue
        if rd == today_dt: return 1       # today
        if rd <= week_end: return 2       # this week
        return 3 + (rd - today_dt).days   # future
    
    reminders.sort(key=score)
    if project_slug:
        reminders = [r for r in reminders if r.get('page_slug') == project_slug]
    return reminders
```

**Verificación:** Crear reminders con fechas variadas, llamar `brain.get_reminders()`, verificar orden.

---

## Task 4: Método `get_journal()` por mes

**Objetivo:** Devolver entradas de journal filtrables por año/mes.

**Files:**
- Modify: `brain.py` — agregar `get_journal()` a `Brain`

**Step 1:** Implementar:

```python
def get_journal(self, year: int = None, month: int = None, project_slug: str = None) -> list:
    filters = [f"(brain='{self._context_id}')"]
    
    if year and month:
        from_str = f"{year:04d}-{month:02d}-01 00:00:00.000Z"
        if month == 12:
            to_str = f"{year+1:04d}-01-01 00:00:00.000Z"
        else:
            to_str = f"{year:04d}-{month+1:02d}-01 00:00:00.000Z"
        filters.append(f"(date>='{from_str}' && date<'{to_str}')")
    elif year:
        filters.append(f"(date>='{year:04d}-01-01 00:00:00.000Z' && date<'{year+1:04d}-01-01 00:00:00.000Z')")
    
    if project_slug:
        filters.append(f"(page='{project_slug}')")
    
    filter_str = '(' + ' && '.join(filters) + ')' if len(filters) > 1 else filters[0]
    entries = self.pb.all('brain_journal', filter=filter_str, sort='-date', perPage=200)
    return entries
```

**Verificación:** Crear entradas de journal en diferentes meses, filtrar por mes, verificar resultados.

---

## Task 5: Método `get_active_projects()`

**Objetivo:** Devolver solo proyectos activos (page_type=project, status=active o sin status).

**Files:**
- Modify: `brain.py` — agregar a `Brain`

**Step 1:**

```python
def get_active_projects(self) -> list:
    pages = self.pb.all('brain_pages',
        filter=f"(brain='{self._context_id}' && page_type='project' && (status='active' || status='' || status=null))",
        sort='title', perPage=200)
    return pages
```

---

## Task 6: Nuevos endpoints API en brain_web.py

**Objetivo:** Exponer los nuevos métodos como endpoints REST.

**Files:**
- Modify: `brain_web.py`

**Step 1:** Modificar `get_pages()` para incluir `status`, `completed_date`, `cancelled_date`, `retrospective`.

**Step 2:** Agregar endpoint `/api/projects/active` → `get_active_projects()`.

**Step 3:** Agregar endpoint `/api/reminders?brain=personal&project=slug` con orden por urgencia.

**Step 4:** Agregar endpoint `/api/journal?brain=personal&year=2026&month=6`.

**Step 5:** Modificar `/api/pages` para que acepte `?project=true` y devuelva solo proyectos activos.

---

## Task 7: Rediseñar sidebar (solo proyectos activos, sin sub-menús)

**Objetivo:** Sidebar limpio: context selector + search + proyectos activos + navegación plana (sin sub-menús expandibles).

**Files:**
- Modify: `brain_web.py` — función `buildSidebar()` en JS

**Nuevo sidebar:**
```
PocketBrain
[personal ▼]
[Buscar...]

── PROYECTOS ──
  ▶ Proyecto Alpha
  ▶ Proyecto Beta

☐ TODO
◈ GOALS  
📓 JOURNAL
⏰ REMINDERS
📄 WIKI
◉ GRAPH
```

**Reglas:**
- Solo `page_type=project` con `status=active` (o null)
- Clic en un proyecto → activa la vista Projects filtrada a ese proyecto
- TODO/GOALS/JOURNAL/REMINDERS/WIKI/GRAPH → navegación directa, sin sub-menús

---

## Task 8: Rediseñar vista TODO con filtro dropdown

**Objetivo:** Dropdown de filtro a la derecha: "Todas", "Sin proyecto", y lista de proyectos activos.

**Files:**
- Modify: `brain_web.py` — `renderTodosView()`

**Layout:**
```
┌─────────────────────────────────────────┐
│ ☐ TODO          [Todas las tareas ▼]    │
│ 5 tareas                                 │
├─────────────────────────────────────────┤
│ BACKLOG │ THIS WEEK │ TODAY │ IN PROGRESS│
│ [card]  │           │       │            │
└─────────────────────────────────────────┘
```

**Filtro:** "Todas las tareas" | "Sin proyecto" | "Proyecto Alpha" | "Proyecto Beta" | ...

---

## Task 9: Rediseñar vista GOALS con filtro dropdown

**Objetivo:** Igual que TODO, dropdown para filtrar por proyecto.

**Files:**
- Modify: `brain_web.py` — `renderGoalsView()`

---

## Task 10: Rediseñar vista REMINDERS con orden de urgencia

**Objetivo:** Orden: atrasados → hoy → esta semana → resto. Dropdown de filtro.

**Files:**
- Modify: `brain_web.py` — `renderRemindersView()`

**Layout:**
```
┌──────────────────────────────────────────┐
│ ⏰ REMINDERS    [Todos ▼]                │
│ 3 recordatorios                           │
├──────────────────────────────────────────┤
│ ⚠ ATRASADOS                              │
│ ┌──────────────────────────────────────┐ │
│ │ Reunion ayer   2026-06-08 · 10:00   │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ 📅 HOY                                    │
│ ┌──────────────────────────────────────┐ │
│ │ Standup        2026-06-09 · 09:00   │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ 📅 ESTA SEMANA                            │
│ ┌──────────────────────────────────────┐ │
│ │ Code review    2026-06-12           │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ 📅 PROXIMOS                               │
│ ┌──────────────────────────────────────┐ │
│ │ Lanzamiento    2026-07-01           │ │
│ └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

---

## Task 11: Rediseñar vista WIKI (índice directo)

**Objetivo:** Sin sub-menú, abre el índice agrupado por page_type.

**Files:**
- Modify: `brain_web.py` — `renderWikiView()`

---

## Task 12: Rediseñar vista JOURNAL con filtro año/mes

**Objetivo:** Muestra entradas del mes actual, dropdowns año/mes a la derecha.

**Files:**
- Modify: `brain_web.py` — `renderJournalView()`

**Layout:**
```
┌──────────────────────────────────────────┐
│ 📓 JOURNAL         [2026 ▼] [Junio ▼]    │
│ 3 entradas                                │
├──────────────────────────────────────────┤
│ 2026-06-09 · mood: great                  │
│ ## Hoy                                    │
│ Avancé en el proyecto alpha...            │
│ ─────────────────────────────────────    │
│ 2026-06-07 · mood: meh                    │
│ ## Lunes                                  │
│ Día de planeación...                      │
└──────────────────────────────────────────┘
```

---

## Task 13: CSS — limpiar y unificar

**Objetivo:** Eliminar estilos de sub-menús viejos, unificar dropdowns y filtros.

**Files:**
- Modify: `brain_web.py` — bloque `<style>`

**Cambios:**
- Eliminar `.nav-sub`, `.nav-sub.open`, `.nav-section` (sub-menús)
- Agregar `.filter-bar` para el dropdown de filtro en cada vista
- Agregar `.reminder-section` para las secciones de reminders (atrasados/hoy/semana/proximos)

---

## Task 14: Screenshots finales

Tomar screenshots limpios de cada vista con el browser tool:
1. Projects (con al menos 1 proyecto activo)
2. TODO kanban (con filtro aplicado)
3. GOALS (con goals y progress bars)
4. REMINDERS (con secciones atrasados/hoy/semana)
5. JOURNAL (con entradas del mes)
6. GRAPH

---

## Files tocados

| File | Changes |
|------|---------|
| `brain.py` | Schema + 4 métodos nuevos + `get_reminders()` + `get_journal()` + `get_active_projects()` |
| `brain_web.py` | Endpoints + HTML/CSS/JS completo |
| `screenshots/*.png` | Actualizar todos |

## Orden de implementación

1. Tasks 1-2: Schema y métodos backend
2. Tasks 3-5: Métodos de consulta (reminders, journal, projects)
3. Task 6: Endpoints API
4. Tasks 7-13: Frontend (sidebar + vistas)
5. Task 14: Screenshots finales
