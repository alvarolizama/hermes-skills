# PocketBrain Web — PocketPages Migration

Proyecto independiente en `~/Repos/personal/pocketbrain-web/` que reescribe la web UI de PocketBrain usando PocketPages (EJS server-rendered en PocketBase) en vez del SPA inline de `web_ui.html` + `brain_web.py`.

## Arquitectura

```
pocketbrain-web/
├── pb_hooks/
│   ├── pocketpages.pb.js         ← Bootstrap: require('pocketpages/dist/hooks.pb')
│   └── pages/
│       ├── +layout.ejs           ← Layout global (sidebar + scripts + menu toggle)
│       ├── +middleware.js        ← Carga ctxId, counts, query; retorna objeto
│       ├── index.ejs             ← Dashboard / resumen
│       ├── projects.ejs          ← Lista de proyectos
│       ├── goals.ejs             ← Goals + Milestones + OKRs con tabs
│       ├── todos.ejs             ← Kanban board con drag & drop
│       ├── reminders.ejs         ← Reminders con tabs de fecha
│       ├── journal.ejs           ← Journal agrupado por día
│       ├── wiki.ejs              ← Wiki index + page detail
│       ├── graph.ejs             ← Knowledge graph (vis.js)
│       ├── lint.ejs              ← Lint report
│       ├── type.ejs              ← Type views genérico
│       ├── api/
│       │   ├── create.ejs        ← POST /api/create
│       │   └── move-todo.ejs     ← POST /api/move-todo (kanban drag)
│       ├── views/
│       │   ├── sidebar.ejs
│       │   ├── breadcrumb.ejs
│       │   ├── fab.ejs
│       │   ├── quick-create-modal.ejs
│       │   ├── command-palette.ejs
│       │   └── toasts.ejs
│       └── public/
│           ├── pocketbrain.css   ← Design system completo
│           ├── pocketbrain.js    ← Client JS (FAB, Cmd+K, shortcuts, dark mode)
│           └── vis-network.min.js ← Copiado del skill
```

## Setup y run

PocketPages **NO** expone un CLI ejecutable (`bunx pocketpages serve` falla). Es solo un plugin de JSVM de PocketBase. Necesitas el binario de PocketBase:

```bash
cd ~/Repos/personal/pocketbrain-web
bun install
./bin/pocketbase serve --dev --hooksDir=./pb_hooks --http=127.0.0.1:8090 --dir=./pb_data
```

Para producción, copiar `pb_hooks/` al servidor donde corre PocketBase (zima.vpn.cloud) y reiniciar.

## Contrato PocketPages: middleware, templates y API

### Middleware (`+middleware.js`)

PocketPages llama al middleware con un objeto `api` que incluye `ctx`, `params`, `log`, `asset`, `url`, `data`, etc. **Los datos retornados se inyectan en la variable `data` de los templates**, no en `context`.

```javascript
module.exports = ({ ctx, log }) => {
  const query = ctx.queryParams() || {}
  // ... cargar ctxId, contexts, counts ...
  return { ctxId, ctxName, contexts, counts, query }
}
```

### Templates EJS

Accede a lo retornado por el middleware con `data`:

```ejs
<% const { ctxId, counts, query } = data %>
```

`context` existe como variable, pero contiene el contexto interno de PocketPages (`ctx`, `params`, `log`, `asset`, `url`, `data`). **No uses `context.ctxId` salvo que el middleware lo haya puesto explícitamente en `context` (no lo hagas).**

### API routes (endpoints POST)

Usa `ctx.body()` para leer el body y `ctx.json()` para responder. No existen `request.body` ni `response.status` en el scope de PocketPages.

```ejs
<%
const { ctxId } = data
const raw = ctx.body() || '{}'
const body = JSON.parse(typeof raw === 'string' ? raw : raw.toString())

if (!body.title) {
  return ctx.json(400, { error: 'title required' })
}

const record = $app.dao().createRecord('brain_pages', {
  brain: ctxId,
  slug: slugify(body.title),
  title: body.title,
  page_type: body.page_type,
  // ...
})

return ctx.json(200, { id: record.getId(), slug: record.getString('slug') })
%>
```

## Errores reales encontrados al portar

### 1. Query params: usar `ctx.queryParams()`, no `url(ctx.request().url)`

**Mal:**
```javascript
module.exports = ({ ctx, asset, url }) => {
  const u = url(ctx.request().url)
  const query = u.query || {}
}
```

**Bien:**
```javascript
module.exports = ({ ctx }) => {
  const query = ctx.queryParams() || {}
}
```

### 2. Los datos del middleware van en `data`, no en `context`

**Mal (en templates):**
```ejs
<% const { ctxId } = context %>
```

**Bien:**
```ejs
<% const { ctxId } = data %>
```

### 3. API endpoints: `ctx.body()` y `ctx.json()`

**Mal:**
```ejs
const body = JSON.parse(request.body || '{}')
response.status = 400
return { error: '...' }
```

**Bien:**
```ejs
const raw = ctx.body() || '{}'
const body = JSON.parse(typeof raw === 'string' ? raw : raw.toString())
if (!body.title) {
  return ctx.json(400, { error: 'title required' })
}
```

### 4. Campo discriminador es `page_type`, no `type`

**Mal:**
```ejs
goals = all.filter((g) => pageTypes.includes(g.getString('type')))
```

**Bien:**
```ejs
const typeFilterExpr = pageTypes.map((t) => `page_type='${t}'`).join(' || ')
const all = $app.dao().findRecordsByFilter('brain_pages',
  `brain='${ctxId}' && (${typeFilterExpr}) && archived=false`, '', 200)
```

### 5. `domain` y `tags` son relations (IDs), no strings

**Mal:**
```ejs
<div><strong>Dominio:</strong> <%= page.getString('domain') %></div>
<div><strong>Tags:</strong> <%= page.getString('tags') %></div>
```

**Bien:** cargar brain_domains y brain_tags y resolver IDs:
```ejs
<%
const domainMap = {}
$app.dao().findRecordsByFilter('brain_domains', `brain='${ctxId}'`, 'name', 200)
  .forEach((d) => { domainMap[d.getId()] = d.getString('name') })
const tagMap = {}
$app.dao().findRecordsByFilter('brain_tags', `brain='${ctxId}'`, 'name', 200)
  .forEach((t) => { tagMap[t.getId()] = t.getString('name') })
%>
<div><strong>Dominio:</strong> <%= domainMap[page.getString('domain')] || '—' %></div>
<div><strong>Tags:</strong> <%= (page.get('tags') || []).map(id => tagMap[id] || id).join(', ') || '—' %></div>
```

### 6. Kanban drag & drop requiere atributos correctos

**Mal:**
```ejs
<div class="kanban-col">
  <div class="kanban-card" data-id="<%= t.getId() %>">...</div>
</div>
```

**Bien:**
```ejs
<div class="kanban-col" data-status="<%= s %>" ondragover="event.preventDefault()">
  <div class="kanban-card" draggable="true" data-id="<%= t.getId() %>">...</div>
</div>
```

Y en el cliente el `drop` lee `col.dataset.status`.

### 7. `findFirstRecordByData` puede no existir; usar `findFirstRecordByFilter`

**Mal:**
```ejs
page = $app.dao().findFirstRecordByData('brain_pages', 'slug', pageSlug)
```

**Bien:**
```ejs
page = $app.dao().findFirstRecordByFilter('brain_pages',
  `brain='${ctxId}' && slug='${pageSlug}' && archived=false`)
```

### 8. No usar emojis en la UI

Reemplazar iconos emoji (🧠, 📄, ✅, 🔔) por Heroicons SVG. El logo, sidebar, FAB y modales deben usar SVG vía helper `icon(name)`.

### 9. `include` en layout no necesita `await`

**Mal:**
```ejs
<%- await include('views/sidebar') %>
```

**Bien:**
```ejs
<%- include('views/sidebar') %>
```

## UX Features (vs web_ui.html)

| Feature | web_ui.html | PocketPages |
|---------|-------------|-------------|
| Dashboard con conteos | ❌ | ✅ index.ejs |
| FAB "+" flotante | ❌ | ✅ Crear rápido |
| Command Palette (Cmd+K) | ❌ | ✅ Búsqueda instantánea |
| Keyboard shortcuts | ❌ | ✅ g p, g t, g w, etc. |
| Kanban drag & drop | ❌ | ✅ drag & drop + API move-todo |
| Dark mode toggle | ❌ | ✅ Persiste en localStorage |
| Toast notifications | Parcial | ✅ Success/error/info |
| Breadcrumb en todas vistas | Solo wiki | ✅ Todas las vistas |
| Mobile responsive | Parcial | ✅ Sidebar off-canvas |

## Diferencias clave

| | web_ui.html | PocketPages |
|---|---|---|
| Render | Client-side SPA | Server-side EJS |
| Data | Fetch API json | `$app.dao()` directo |
| Server | `brain_web.py` (Python) | PocketBase hooks (JS) |
| Auth | JWT manual | Cookie nativa de PB |
| Routing | Hash-based (#tab=wiki) | File-based (/wiki.ejs) |

## Deploy

Copiar `pb_hooks/` al directorio de PocketBase en producción:

```bash
rsync -avz pb_hooks/ zima:/path/to/pocketbase/pb_hooks/
# Reiniciar pocketbase
```

## Notas

- El skill PocketBrain original (`brain_web.py` + `web_ui.html`) sigue funcionando. Esto es una alternativa, no un reemplazo.
- PocketPages ejecuta dentro del proceso de PocketBase. Necesitas deployar los hooks al mismo host donde corre PocketBase.
- El binario de PocketBase ya está en `~/Repos/personal/pocketbrain-web/bin/pocketbase`.
