# vis.js Graph Pitfalls

PocketBrain usa [vis-network](https://visjs.github.io/vis-network/docs/network/) para renderizar grafos de conocimiento (global y por proyecto).

## ⚠️ vis.js DESTRUYE el innerHTML del contenedor

Al inicializar `new vis.Network(container, ...)`, vis.js **reemplaza completamente** el `innerHTML` del contenedor con sus propios elementos DOM (canvas, overlays, etc.).

**Esto destruye cualquier elemento hijo que hayas puesto dentro del contenedor**, incluyendo leyendas, tooltips, o divs auxiliares.

### ❌ No funciona: leyenda dentro del contenedor

```javascript
// MAL: la leyenda se pierde cuando vis.Network() reemplaza innerHTML
h+='<div id="graph-view" style="position:relative">';
h+='  <div id="graph-legend" style="position:absolute;bottom:12px;right:12px">...</div>'; // ← DESTRUIDO
h+='</div>';
container.innerHTML = h;
new vis.Network(document.getElementById('graph-view'), ...); // ← borra la leyenda
```

### ✅ Correcto: leyenda como HERMANA del contenedor

```javascript
// BIEN: la leyenda es hermana, no hija del contenedor
h+='<div style="position:relative">';                          // wrapper con position:relative
h+='  <div id="graph-view" style="width:100%;height:400px">...</div>';  // vis.js container
h+='  <div id="graph-legend" style="position:absolute;bottom:12px;right:12px">...</div>'; // hermana
h+='</div>';
container.innerHTML = h;
new vis.Network(document.getElementById('graph-view'), ...);   // solo afecta graph-view
// #graph-legend intacta
```

### Regla de oro

**Cualquier elemento UI superpuesto a un grafo vis.js debe ser HERMANO del contenedor, no hijo.** La leyenda, tooltips o controles deben vivir fuera del div que se pasa a `new vis.Network()`.

### Posicionamiento de la leyenda

Las leyendas se posicionan con `position:absolute` sobre el canvas del grafo:

```css
#graph-legend {
  position: absolute;
  bottom: 20px;      /* separación del borde inferior */
  right: 12px;       /* separación del borde derecho */
  background: var(--canvas);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 11px;
  z-index: 10;       /* encima del canvas */
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
```

El ancestro con `position:relative` debe ser el wrapper exterior, no el contenedor de vis.js.

### Verificación

```javascript
// Verificar que la leyenda existe después de renderizar el grafo
var legend = document.getElementById('graph-legend');
if (!legend) console.error('vis.js destruyó la leyenda!');
// Corregir: asegurar que la leyenda es hermana del contenedor, no hija.
```

## Grafos: global vs proyecto

| Aspecto | Grafo global (◉ Graph) | Grafo de proyecto (tab Graph) |
|---------|----------------------|-------------------------------|
| Contenedor | `#graph-view` en HTML estático | `#project-graph-view` creado dinámicamente en `switchProjectTab` |
| Leyenda | `#graph-legend` en HTML estático (CSS en `<style>`) | `#project-graph-legend` creado inline en `switchProjectTab` |
| Posicionamiento | CSS fijo en `<style>` | inline style en JS |
| Colores | `GCOLORS` en `renderGraph()` | `colors` en `renderProjectGraph()` |
| Tipos en leyenda | Todos los page_types del backend | Goals, Tareas, Reminders, Proyecto + page_type de wikilinks del body |

## Colores de nodos por tipo

```javascript
// Grafo global (renderGraph)
var GCOLORS = {
  entity:'#4CAF50', concept:'#2196F3', comparison:'#FF9800',
  query:'#9C27B0', raw:'#607D8B', project:'#E91E63', plan:'#795548',
  goal:'#4CAF50', milestone:'#FF9800', okr:'#E91E63',
  todo:'#9C27B0', deliverable:'#00BCD4', reminder:'#FFC107'
};

// Grafo de proyecto (renderProjectGraph)
var colors = {
  goal:'#4CAF50', milestone:'#FF9800', okr:'#E91E63',
  todo:'#9C27B0', concept:'#2196F3', entity:'#4CAF50',
  project:'#E91E63', reminder:'#FFC107',
  deliverable:'#00BCD4', file:'#607D8B', journal:'#795548'
};
```
