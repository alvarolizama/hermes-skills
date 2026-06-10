# Browser Debugging para web_ui.html

## Verificar DOM sin screenshots

Cuando el UI parece correcto pero falta un footer, metadata, o sección, evitar ciclos de `browser_vision` + scroll. En vez, usar `browser_console` con JavaScript para query de DOM directamente desde el browser:

```javascript
// Verificar si un elemento existe
var main = document.getElementById('view-wiki');
JSON.stringify({
  hasFooter: main.innerHTML.includes('Relaciones'),
  hasMeta: main.innerHTML.includes('Creado'),
  htmlLength: main.innerHTML.length
});

// Verificar estructura de tabs
var tabs = document.querySelectorAll('.project-tabs a');
JSON.stringify(Array.from(tabs).map(a => ({
  text: a.textContent, 
  onclick: a.getAttribute('onclick')
})));

// Verificar datos de una variable global
JSON.stringify({
  logsLength: LOGS.length,
  pageHasId: PAGES[0]?.id ? true : false
});
```

**Ventajas:**
- No depende de la resolución ni scroll visible
- Puede verificar innerHTML completo incluso si está fuera del viewport
- Puede acceder a variables JS globales (PAGES, GOALS, TODOS, LOGS) que no aparecen en el DOM snapshot

## Detectar U+2019 (') en archivos de código

Si `node --check` falla en una línea aparentemente correcta, buscar el caracter Unicode `U+2019` (Right Single Quotation Mark) que se ve idéntico a la apóstrofo ASCII `U+0027`:

```python
with open('web_ui.html', 'rb') as f:
    data = f.read()
    if b'\xe2\x80\x99' in data:
        print('Found at', data.index(b'\xe2\x80\x99'))
```

**Síntoma:** `SyntaxError: Invalid or unexpected token` en una línea sin comillas aparentes. El error reporta un carácter invisible o un token que no debería estar ahí.

**Prevention:** No escribir apóstrofos en strings de `new_string` del patch si puede evitarse. Preferir dobles comillas o concatenación de strings para evitar introducir caracteres Unicode.
