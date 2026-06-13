# Sidebar Layout — PocketBrain Web UI

Guía para el sidebar de navegación de PocketBrain: alineación icono-label-count y orden de items.

## Layout de cada item

Cada `<a class="nav-link">` debe ser un flex container:

```css
.nav-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 20px;
}

.nav-link .nav-label {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.nav-link .nav-label svg {
  display: block;
  flex-shrink: 0;
}

.nav-link .nav-label > span {
  line-height: 20px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-link .nav-count {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 9999px;
  min-width: 20px;
  text-align: center;
  flex-shrink: 0;
  margin-left: 6px;
}
```

Puntos clave:
- `align-items:center` + `line-height` compartido entre SVG y texto.
- `gap:8px` entre icono y label. No usar `margin-left` inline.
- El contador badge usa `margin-left:6px` y `flex-shrink:0` para no colapsar.
- El label puede truncar con ellipsis si el sidebar es estrecho.

## Orden de items

Orden aprobado por Álvaro:

1. Proyectos
2. Goals
3. Milestones
4. Ideas
5. Planes
6. Todo
7. Reminders
8. Notas
9. Journal
10. Archivos
11. Conceptos
12. Entidades
13. Comparaciones
14. Consultas
15. Raw
16. Wiki
17. Graph
18. Lint

**Nota**: `Entregables` ya no va en el sidebar. Se usan solo `Archivos`.

## HTML generado

```html
<a href="javascript:void(0)" class="nav-link" onclick="showTab('projects');return false;" data-search="projects">
  <span class="nav-label" style="display:flex;align-items:center;gap:8px">
    <svg>...</svg>
    <span>Proyectos</span>
  </span>
  <span class="nav-count">3</span>
</a>
```

Siempre terminar el `onclick` con `;return false;` para evitar que `href="javascript:void(0)"` cambie el scroll/hash en mobile.

## Pitfall: icono desalineado

Si el SVG parece más alto/bajo que el texto, usualmente es porque el span interno no comparte el mismo `line-height` o el SVG tiene `display:inline` por defecto. Forzar `display:block` en el SVG y `line-height:20px` en el texto lo arregla.
