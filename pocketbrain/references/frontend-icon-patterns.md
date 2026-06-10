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
| Graph | chart-pie | `chart-pie` | Sidebar, legend |
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

## Verificación

```bash
grep -n 'function icon(' ~/.hermes/skills/productivity/pocketbrain/scripts/web_ui.html
```

Debe devolver línea con el helper. Después de deploy, usar `browser_vision` para verificar que los iconos aparecen y no hay fallback vacío.
