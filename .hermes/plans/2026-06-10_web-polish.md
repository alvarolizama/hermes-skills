# PocketBrain Web UI — Final Polish Plan

> **For Hermes:** Execute each task sequentially, verify with `node --check`, restart server, test with curl.

**Goal:** Dejar la web UI de PocketBrain 100% funcional con tabs en vista de proyecto, kanban responsive, y datos vinculados correctamente.

**Architecture:** `brain_web.py` (Python server + endpoints) sirve `web_ui.html` (HTML+CSS+JS inline). Datos en PocketBase (`zima.vpn.cloud:18090`), 5 contexts con ~103 registros.

**Tech Stack:** Python 3.11, PocketBase REST API, vanilla JS, vis.js CDN.

---

## Task 1: Verificar JS syntax después de los cambios de tabs

**Objective:** Confirmar que `web_ui.html` no tiene errores de sintaxis.

**Step 1:** Extraer y validar:
```bash
python3 -c "
import re
html = open('web_ui.html').read()
m = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if m:
    with open('/tmp/pb_js.js','w') as f: f.write(m.group(1))
" && node --check /tmp/pb_js.js && echo "JS OK" || echo "JS FAIL"
```

**Fix:** Si falla, identificar línea y corregir escapes de comillas o paréntesis.

---

## Task 2: Arreglar kanban CSS — full width, mobile stacking

**Objective:** Kanban ocupa todo el ancho sin scroll bars forzados. En mobile se apilan columnas.

**File:** `web_ui.html`

**Step 1:** Reemplazar CSS del kanban:
```css
/* Desktop */
.kanban{display:flex;gap:12px;padding-bottom:20px;flex-wrap:wrap}
.kanban-col{flex:1 1 160px;min-width:140px;background:var(--soft);border-radius:12px;padding:12px}

/* Mobile — apilar columnas */
@media(max-width:768px){
  .kanban{flex-direction:column;gap:8px}
  .kanban-col{min-width:auto;flex:1 1 auto}
}
```

**Verificación:** Abrir con tareas en múltiples columnas, verificar que no hay scroll horizontal forzado. Reducir ventana a 400px y verificar columnas apiladas.

---

## Task 3: Expandir renderProjectView con tabs

**Objective:** Vista de proyecto usa tabs (Resumen | Goals | Kanban | Recordatorios | Journal) ocupando ancho completo.

**File:** `web_ui.html`

**Step 1:** Agregar CSS de tabs:
```css
.project-tabs{display:flex;gap:0;border-bottom:2px solid var(--hairline);margin-bottom:24px;overflow-x:auto}
.project-tabs a{display:inline-block;padding:10px 18px;font-size:13px;color:var(--mute);text-decoration:none;border-bottom:2px solid transparent;margin-bottom:-2px;white-space:nowrap;cursor:pointer}
.project-tabs a.active{color:var(--ink);border-bottom-color:var(--ink);font-weight:600}
```

**Step 2:** Rewrite `renderProjectView(slug)`:
- Header con breadcrumb "← Proyectos" + título
- Meta chips: status + conteo goals/tareas/reminders/journal
- Tab bar con 5 tabs
- `switchProjectTab(tab, slug)` carga contenido en `#project-tab-content`
- Datos cacheados en `window._projectData`

**Step 3:** Implementar `switchProjectTab(tab, slug)`:
- `overview`: resumen + fechas
- `goals`: cards con chip type, status, deadline, progress bar
- `kanban`: columnas kanban con tareas vinculadas
- `reminders`: lista ordenada por fecha
- `journal`: últimas 20 entradas ordenadas por fecha descendente

---

## Task 4: Vincular datos en PocketBase

**Objective:** Todos los goals, todos, reminders tengan `page` vinculado a su proyecto.

**Step 1:** Script de vinculación:
```python
from brain import _pocketbrain_pb
pb = _pocketbrain_pb()
for ctx_name in ['personal', 'projects', 'bravo']:
    ctx = pb.list('contexts', filter=f"(name='{ctx_name}')")[0]
    pages = {p['slug']: p['id'] for p in pb.list('brain_pages', filter=f"(brain='{ctx['id']}')", perPage=50)}
    proj_slugs = [s for s, p in zip(pages.keys(), pb.list('brain_pages', ...)) if ... page_type == 'project']
    # Para cada proyecto, buscar goals/todos/reminders por keywords y vincular
```

**Verificación:**
```python
for g in pb.list('brain_goals', perPage=50):
    assert g.get('page'), f"Goal sin vincular: {g['title']}"
```

---

## Task 5: Reiniciar servidor y verificar todo

**Objective:** Servidor limpio con todos los cambios.

**Step 1:** Kill y restart:
```bash
lsof -ti:8899 | xargs kill -9 2>/dev/null
cd scripts && python3 brain_web.py --brain personal --port 8899 &
```

**Step 2:** Verificar APIs:
```bash
for ep in brains pages goals todos reminders journal graph; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8899/api/$ep?brain=personal")
  echo "$ep: $code"
done
```

**Step 3:** Verificar datos vinculados:
```bash
curl -s "http://localhost:8899/api/goals?brain=personal" | python3 -c "import json,sys; gs=json.load(sys.stdin); print(f'{len(gs)} goals, {sum(1 for g in gs if g.get(\"page\"))} linked')"
```

---

## Task 6: Screenshots finales

**Objective:** Capturar screenshots limpios para el README.

**Método:** Usar `browser_vision` tool con servidor corriendo en `localhost:8899`. Navegar cada vista y capturar:

| Vista | Acción |
|-------|--------|
| Projects | `showTab('projects')` → screenshot |
| Kanban | `showTab('todos')` → screenshot |
| Goals | `showTab('goals')` → screenshot |
| Journal | `showTab('journal')` → screenshot |
| Reminders | `showTab('reminders')` → screenshot |
| Graph | `showTab('graph')` → esperar 2s → screenshot |
| Project detail | `showProject('viaje-a-japon-2026')` → screenshot |

Guardar en `screenshots/` del repo.

---

## Task 7: Sync al repo y commit

**Objective:** Copiar cambios al repo `hermes-skills` y push.

```bash
cp brain_web.py web_ui.html /Users/alvaro/Repos/personal/hermes-skills/pocketbrain/scripts/
cp brain.py /Users/alvaro/Repos/personal/hermes-skills/pocketbrain/scripts/
cd /Users/alvaro/Repos/personal/hermes-skills
git add -A && git commit --no-gpg-sign -m "v2.1.0: tabs en proyecto, kanban responsive, sidebar simplificado"
git push
```

---

## Files tocados

| File | Changes |
|------|---------|
| `web_ui.html` | Kanban CSS, tabs CSS, `renderProjectView` + `switchProjectTab` |
| `brain_web.py` | Cache per-context (`_brain_cache[BN]`) |
| `brain.py` | Sin cambios adicionales |
