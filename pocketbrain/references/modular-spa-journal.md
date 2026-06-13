# Modular SPA: Journal view pitfalls

## Síntoma: journal muestra markdown crudo

Si `views/journal.js` escribe el body directamente en un `<p>` escapado, el usuario ve:

```
## Hoy - Avance en [[PocketBrain]]
- implemente command palette y FAB
- [[Bravo]]: bug de login arreglado
```

en lugar de headings renderizados y links clickeables.

## Causa

El body se pasa por `esc()` (HTML-escape) sin pasar por `window.mdToHtml()`:

```javascript
// ❌ Incorrecto
html += '<p style="font-size:13px">' + esc(j.body) + '</p>';
```

## Fix

Renderizar el body con el helper global de markdown:

```javascript
// ✅ Correcto
html += '<div class="md-content" style="font-size:13px">'
      + (window.mdToHtml ? window.mdToHtml(j.body || j.content || '') : esc(j.body || j.content || ''))
      + '</div>';
```

## Verificación

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
node --check views/journal.js
```

En browser, navegar a `#tab=journal` y confirmar que:
- `## Hoy` aparece como heading, no como texto literal.
- `[[PocketBrain]]` aparece como link clickeable a la página.
- Las listas `- item` se renderizan como `<ul>` / `<li>`.

## Nota

`window.mdToHtml` se expone en `app.js` al iniciar la aplicación. Si `views/journal.js` se carga como módulo ES, `window.mdToHtml` ya está disponible porque `app.js` lo define antes de renderizar cualquier vista.
