# Wiki Page Layout Pattern — Two-Column Design

Session: 2026-06-10 — Implementación del sidebar derecho en wiki page detail.

## Contexto

Anteriormente, la wiki page detail (`showPage()` en `web_ui.html`) mostraba todo el contenido en una sola columna. El usuario pidió:
1. **Sidebar derecho** con relaciones (goals, tareas, reminders, journal, backlinks) listados con iconos de color.
2. **Metadata** (creado/actualizado/estado/etc) en una tarjeta debajo de relaciones.
3. **Log de actividad** debajo del contenido markdown.

## Layout CSS

```css
/* Contenedor principal: flex, contenido + sidebar */
.wiki-layout-page {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

/* Columna izquierda: contenido, crece para llenar */
.wiki-left {
  flex: 1;
  min-width: 0;  /* evita overflow de texto largo */
}

/* Sidebar derecho: ancho fijo 240px, no encoge */
.wiki-right {
  width: 240px;
  min-width: 240px;
  flex-shrink: 0;
}

/* Tarjeta del sidebar */
.wiki-relations-card {
  background: var(--soft);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

/* Título del panel */
.wiki-relations-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: .5px;
}

/* Item de relación: icono + label alineados */
.wiki-relation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

/* Icono de 28x28px con color de fondo */
.wiki-rel-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

/* Sección de logs debajo del contenido */
.wiki-log {
  margin-top: 32px;
  border-top: 1px solid var(--hairline);
  padding-top: 16px;
  font-size: 13px;
}
.wiki-log h2 {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 12px;
}
.wiki-log div {
  padding: 6px 0;
  border-bottom: 1px solid var(--hairline);
  color: var(--body);
}

/* Responsive: sidebar apila debajo en mobile */
@media(max-width:768px){
  .wiki-layout-page { flex-direction: column; }
  .wiki-right { width: 100%; min-width: 0; }
}
```

## Generación de HTML en showPage()

El patron es **flexbox wrap** con dos `<div>` hermanos: `.wiki-left` y `.wiki-right`.

```javascript
function showPage(slug) {
  window._wikiSlug = slug;
  // ... filtrar arrays: pgoals, ptodos, prems, pjour, bl ...
  
function showPage(slug) {
  window._wikiSlug = slug;
  // ... filtrar arrays: pgoals, ptodos, prems, pjour, bl ...
  
  // === TABS (ARIBA DE TODO) ===
  var h = '<div class="project-tabs"><a class="active" href=\\#" onclick="switchPageTab(\\'content\\',\\''+slug+'\\'); return false;">Contenido ('+(p.body?1:0)+')</a>';
  if(bl.length) h += '<a href=\\#" onclick="switchPageTab(\\'backlinks\\',\\''+slug+'\\'); return false;">Backlinks ('+bl.length+')</a>';
  var relCount = pgoals.length + ptodos.length + prems.length + pjour.length;
  if(relCount) h += '<a href=\\#" onclick="switchPageTab(\\'related\\',\\''+slug+'\\'); return false;">Relacionado ('+relCount+')</a>';
  h += '</div>';

  // Breadcrumb + título (sin pills de meta debajo)
  h += '<div style="font-size:12px;color:var(--mute);margin-bottom:8px"><a href=\\#" onclick="showIndex()" style="color:var(--ink)">← Wiki</a> · '+p.page_type+'</div>';
  h += '<h1>'+p.title+'</h1>';
  
  // Layout two-column
  h += '<div class="wiki-layout-page">';
  
  // === COLUMNA IZQUIERDA ===
  h += '<div class="wiki-left">';
  h += '<div id="page-tab-content"></div>';   // renderizado por switchPageTab
  
  // Log de actividad
  var pageLogs = LOGS.filter(function(l){return l.page===p.id;}).slice(0,10);
  h += '<div class="wiki-log"><h2>Actividad reciente</h2>';
  if(pageLogs.length) {
    pageLogs.forEach(function(l){
      h += '<div><strong>'+l.created+'</strong> · '+l.operation+(l.details?': '+l.details:'')+'</div>';
    });
  } else {
    h += '<p style="color:var(--mute)">Sin actividad reciente.</p>';
  }
  h += '</div></div>'; // end wiki-left + wiki-log
  
  // === SIDEBAR DERECHO ===
  h += '<div class="wiki-right">';
  
  // Tarjeta Relaciones (conteos con iconos color)
  h += '<div class="wiki-relations-card">';
  h += '<div class="wiki-relations-title">Relaciones</div>';
  h += '<div class="wiki-relation-row">';
  if(pgoals.length) h += '<div class="wiki-relation-item">'+
    '<span class="wiki-rel-icon" style="background:#E8F5E9;color:#4CAF50">G</span>'+
    '<span class="wiki-rel-label">'+pgoals.length+' goals</span></div>';
  // ... mismo patrón para tareas (T/púrpura), reminders (R/amarillo), 
  //     journal (J/azul), backlinks (B/gris)
  h += '</div></div>';
  
  // Tarjeta Metadata: TODO en un solo lugar (tipo, confianza, conteos, fechas, estado, etc.)
  // Los conteos ya NO se ponen debajo del <h1> en pills .meta
  h += '<div class="wiki-relations-card">';
  h += '<div class="wiki-relations-title">Metadata</div>';
  h += '<div class="wiki-relation-row">';
  // Campos descriptivos (siempre si existen):
  h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Tipo</span><span class="wiki-rel-value">'+p.page_type+'</span></div>';
  if(p.confidence) h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Confianza</span><span class="wiki-rel-value">'+p.confidence+'</span></div>';
  if(p.domain)     h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Dominio</span><span class="wiki-rel-value">'+p.domain+'</span></div>';
  // Conteos funcionales (complementan a Relaciones; siempre mostrar, incluso 0):
  h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Goals</span><span class="wiki-rel-value">'+pgoals.length+'</span></div>';
  h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Tareas</span><span class="wiki-rel-value">'+ptodos.length+'</span></div>';
  h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Backlinks</span><span class="wiki-rel-value">'+bl.length+'</span></div>';
  // Fechas y estado:
  if(p.created)    h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Creado</span><span class="wiki-rel-value">'+p.created+'</span></div>';
  if(p.updated)    h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Actualizado</span><span class="wiki-rel-value">'+p.updated+'</span></div>';
  if(p.status)     h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Estado</span><span class="wiki-rel-value">'+p.status+'</span></div>';
  if(p.tags && p.tags.length) h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Tags</span><span class="wiki-rel-value">'+p.tags.join(', ')+'</span></div>';
  if(p.comment)    h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Nota</span><span class="wiki-rel-value">'+p.comment+'</span></div>';
  if(p.started_date)    h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Iniciado</span><span class="wiki-rel-value">'+p.started_date+'</span></div>';
  if(p.completed_date)  h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Completado</span><span class="wiki-rel-value">'+p.completed_date+'</span></div>';
  if(p.cancelled_date)  h += '<div class="wiki-relation-item"><span class="wiki-rel-label">Cancelado</span><span class="wiki-rel-value">'+p.cancelled_date+'</span></div>';
  h += '</div></div></div></div>'; // end wiki-right + wiki-layout-page
  
  document.getElementById('view-wiki').innerHTML = h;
  // ... switchPageTab('content', slug)
}
```

## Iconos de color para relaciones

| Tipo | Letra | Fondo | Texto |
|------|-------|-------|-------|
| Goals | G | `#E8F5E9` (verde claro) | `#4CAF50` |
| Tareas | T | `#F3E8F5` (púrpura claro) | `#9C27B0` |
| Reminders | R | `#FFF8E1` (amarillo claro) | `#FFC107` |
| Journal | J | `#E3F0FF` (azul claro) | `#2196F3` |
| Backlinks | B | `#F5F5F0` (gris claro) | `#737373` |

## Pitfalls

### Metadata vacía — created/updated no llegan del backend

`pb.list()` del SDK de PocketBase no siempre devuelve `created`/`updated` por default. Si `get_pages()` del backend incluye estos campos en la respuesta pero vienen como strings vacías `""`, el panel Metadata se renderiza vacío.

**Verificación:** `curl http://localhost:8899/api/pages | python3 -c "... verificar p['created'] != ''"

**Fix:** Revisar si `pb.list()` necesita `fields='*,created,updated'` o si el SDK ya los incluye. Verificar en el endpoint directo de PocketBase (no via `get_pages()` wrapper).

### Polling resetea la wiki page a índice

`loadAll()` cada 30s → `showCurrentView()` → `showIndex()` (si `_currentTab === 'wiki'`). El usuario pierde la página que estaba leyendo.

**Fix:** `window._wikiSlug` + restore en `showCurrentView()`. Ver `references/web-ui-patterns.md` sección "SPA state preservation during polling".

### Href en tabs generados por JS

Cada `<a>` en `project-tabs` debe tener `href="#"` y `onclick="...; return false;"`. Sin `href="#"`, el browser interpreta el click como navegación, recarga la SPA y la app se queda en blanco.

**Atención especial:** al generar HTML dentro de strings JS single-quoted, el `"href=\#""` puede malformarse. Usar `href=\#"` (dos backslash + comilla doble) para que el parser HTML interprete correctamente `href="#"`.

```javascript
// Correcto (en string JS single-quoted)
h += '<a href=\\#" onclick="...\">Texto</a>';
// Resultado en DOM: <a href="#" onclick="...">Texto</a>
```

## Roadmap: lista de relaciones con títulos reales (próximo)

El sidebar derecho actual muestra solo **conteos** (`4 goals`, `6 tareas`, etc.). Lo que falta:

1. **Listar items reales**: bajo el conteo, una lista de `<a href>linkable</a>` con títulos.
2. **Nueva tarjeta "Wikilinks"**: los links salientes del markdown (`[[slug]]` en el body).
3. **Campos de schema faltantes** en la API (`summary`, `source_url`, `contested`, `archived`).
4. **Links clickeables** desde sidebar → navegación SPA sin reload.

Estructura propuesta:

```
RELACIONES                (tarjeta)
Goals (4)
├─ Presupuesto total < 4k USD  ← link -> showPage(goal.page_slug)
├─ Visitar 5 templos clave
Tareas (6)
├─ Pagar vuelos Japón
├─ Comprar JR Pass
Reminders (7)
├─ Cumpleaños de Carlos
Wikilinks (3)             ← NUEVO
├─ Tokio
├─ Kyoto
└─ Osaka
Backlinks (2)
├─ Zig vs Rust
└─ Mi stack tech

METADATA                  (tarjeta)
Tipo: concept
Dominio: personal
Confianza: high
...
```

### Items linkables

Cada goal/tarea/reminder/backlink debe ser un `<a>` con `onclick` que navega a ese item en la SPA:

```javascript
// Goal link -> mostrar el goal (vía showPage si tiene page, o switchProjectTab('goals', slug))
h += '<a href=\\#" onclick="showPage(\'' + g.page_slug + '\'); return false;">' + g.title + '</a>';

// Backlink: abre la otra wiki page
h += '<a href=\\#" onclick="showPage(\'' + b.slug + '\'); return false;">' + b.title + '</a>';

// Wikilinks out: html extraído del body (new)
var outgoing = extractWikiLinks(p.body);
outgoing.forEach(function(w){ 
  h += '<a href=\\#" onclick="showPage(\'' + w + '\'); return false;">' + (pmap[w]?.title || w) + '</a>';
});
```

### Atención: alinear con `page` field contract

El backend `get_goals()` devuelve `page_slug` (ya no `page` como ID). El frontend usa `g.page_slug` para filtrar y para links. Mantener consistencia: si agregamos links a goals desde el wiki sidebar, verificar que `GOALS[i].page_slug` existe.
