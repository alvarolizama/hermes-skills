# Patrón: Iconos SVG inline en el frontend (Heroicons)

Cuando la UI de `web_ui.html` usa emojis o Unicode ambiguos (ej. `☐`, `◈`, `⏰`), el renderizado varía por sistema operativo y fuente. La solución es usar **Heroicons v2 outline (24x24)** como SVG inline, evitando dependencias de fuentes y garantizando consistencia visual.

---

## Flujo típico

### 1. Descargar los SVGs necesarios

```bash
mkdir -p /tmp/heroicons && cd /tmp/heroicons
for f in squares-2x2 clipboard-document-list flag bell book-open paper-clip cube document-text chart-pie bars-3 arrow-left exclamation-triangle calendar-days check-circle magnifying-glass clock; do
  curl -sL "https://raw.githubusercontent.com/tailwindlabs/heroicons/master/optimized/24/outline/${f}.svg" -o "${f}.svg"
done
ls -la   # verificar 16 archivos y tamaños >200 bytes (no páginas 404)
```

**Path correcto:** `master/optimized/24/outline/` (no `refs/heads/main/24/outline` ni `src/24/outline`). Si los archivos pesan 14 bytes, son páginas 404 guardadas con texto `"404: Not Found"`. Verificar con `head -1 archivo.svg`.

---

### 2. Extraer los paths con Python

```python
import os, re, xml.etree.ElementTree as ET
paths = {}
for f in os.listdir('/tmp/heroicons'):
    if f.endswith('.svg'):
        root = ET.parse('/tmp/heroicons/' + f).getroot()
        path = root.find('.//{http://www.w3.org/2000/svg}path')
        if path is not None:
            paths[f.replace('.svg','')] = path.get('d','')
        else:
            # fallback: raw regex si namespace no aplica
            with open('/tmp/heroicons/' + f) as fh:
                m = re.search(r'd="([^"]+)"', fh.read())
                if m:
                    paths[f.replace('.svg','')] = m.group(1)
for k, v in sorted(paths.items()):
    print(f"  '{k}': '{v}',")
```

Copiar el output al bloque `_ICONS`.

---

### 3. Inyectar el helper en el script JS

Insertar al inicio (después de las variables globales, antes de `function api`):

```javascript
var _ICONS = {
  'squares-2x2': 'M3.75 3.75a.75.75... 0 0 1.5 0V3.75z...',
  'clipboard-document-list': '...',
  'flag': '...',
  // ... todos los paths
};
function icon(name, size) {
  size = size || 20;
  return '<svg xmlns="http://www.w3.org/2000/svg" width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="' + (_ICONS[name] || '') + '"/></svg>';
}
```

---

### 4. Reemplazar emojis en toda la UI generada

- **Sidebar nav items:** `icon('flag',16) + ' Goals'`
- **Hamburger button:** SVG inline en el HTML body del botón (no `'+` en HTML estático)
- **Secciones de reminders:** `icon('exclamation-triangle',18) + ' Atrasados'`
- **Kanban headers:** mapa `_kanbanIcons` por status a icon

Nunca mezclar concatenaciones JS (`'+icon(...)+'`) dentro del HTML body estático. El hamburger debe tener el SVG crudo directamente en el HTML, o generarse vía JS si el botón se inserta dinámicamente.

---

## Iconos mapeados por vista

| Vista | Icono | `name` | Uso |
|---|---|---|---|
| Projects | squares-2x2 | `squares-2x2` | Sidebar, header |
| Todo | clipboard-document-list | `clipboard-document-list` | Sidebar, kanban |
| Goals | flag | `flag` | Sidebar, chips |
| Reminders | bell | `bell` | Sidebar, overdue |
| Journal | book-open | `book-open` | Sidebar, entries |
| Files | paper-clip | `paper-clip` | Sidebar, cards |
| Deliverables | cube | `cube` | Sidebar, cards |
| Wiki | document-text | `document-text` | Sidebar, pages |
| Graph | circle | `circle` | Sidebar, legend |
| Atrasados | exclamation-triangle | `exclamation-triangle` | Section header |
| Hoy/esta semana | calendar-days | `calendar-days` | Section header |
| Completados | check-circle | `check-circle` | Section, kanban done |
| Próximos | clock | `clock` | Section header |
| Back | arrow-left | `arrow-left` | Breadcrumbs |
| Hamburger | bars-3 | `bars-3` | Mobile toggle (SVG directo) |
| Kanban backlog | clipboard-document-list | `clipboard-document-list` | Column header |
| Kanban in progress | flag | `flag` | Column header |
| Kanban done | check-circle | `check-circle` | Column header |
| Kanban cancelled | x-circle (o x-mark) | `x-circle` | Column header |
| Search | magnifying-glass | `magnifying-glass` | Input (optional) |

---

## Pitfall: sidebar items con icono hardcodeado en vez de `icon()`

Cuando se agrega un nuevo item al sidebar (o se refactoriza uno existente), es fácil dejar el icono como **texto Unicode hardcodeado** (ej. `◉ Graph`) o como texto plano sin SVG, rompiendo la consistencia visual con el resto del menú que usa `icon('name',16)`.

**Síntoma:** Un item del sidebar aparece sin icono (solo texto) o con un símbolo Unicode que no tiene el mismo estilo/tamaño que los SVG de Heroicons.

**Fix:**
1. Si el icono no existe en `_ICONS`, agregar el path al dict con el nombre de Heroicons (ej: `circle: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z'`).
2. En `buildSidebar()`, usar `icon('circle',16)` en lugar del símbolo Unicode:
   ```javascript
   // Correcto
   h += '<a href="#" class="nav-link" onclick="showTab(\'graph\')">' + icon('circle',16) + '<span>Graph</span><span class="nav-count">' + nc + '</span></a>';
   
   // Incorrecto (rompe consistencia visual)
   h += '<a href="#" class="nav-link" onclick="showTab(\'graph\')">◉ Graph<span class="nav-count">' + nc + '</span></a>';
   ```
3. Verificar que todos los items del sidebar usan el mismo patrón: `icon('name',16) + '<span>Texto</span>...'`.

### Modular SPA: importar icon helper

En un frontend modular, el helper de iconos debe vivir en `components/Icon.js` y exportar `icon(name, size)`:

```javascript
// components/Icon.js
const ICONS = { 'squares-2x2': '...', ... };
export function icon(name, size = 20) { ... }
export default icon;
```

Y en `app.js`:

```javascript
import { icon } from './components/Icon.js';

const item = (id, label, count, search, iconName) => {
  const svg = iconName ? icon(iconName, 16) : '';
  return `<a href="javascript:void(0)" class="nav-link" onclick="showTab('${id}')" data-search="${search || label.toLowerCase()}">`
       + `<span class="nav-label">${svg}<span style="margin-left:8px">${label}</span></span>`
       + `<span class="nav-count">${count}</span></a>`;
};
```

### CSS para iconos en sidebar

```css
#nav a.nav-link .nav-label{display:flex;align-items:center;flex:1}
#nav a.nav-link .nav-label svg{flex-shrink:0;margin-right:8px}
#nav a.nav-link .nav-count{font-size:10px;color:var(--body);background:var(--hairline);padding:1px 6px;border-radius:9999px;min-width:20px;text-align:center;flex-shrink:0}
```

## Verificación

```bash
# En frontend modular: verificar que Icon.js exporta icon()
grep -n 'export function icon' ~/.hermes/skills/productivity/pocketbrain/scripts/components/Icon.js
```

Debe devolver línea con el helper. Después de deploy, usar `browser_vision` para verificar que los iconos aparecen y no hay fallback vacío.

```bash
# Verificar que NINGUN sidebar item usa un símbolo Unicode hardcodeado
grep -oP '◉|☐|⏰|📁|📅|📚|📓|🎯' ~/.hermes/skills/productivity/pocketbrain/scripts/web_ui.html
# El resultado debe estar vacío (todos los iconos deben ser SVG inline)
```
