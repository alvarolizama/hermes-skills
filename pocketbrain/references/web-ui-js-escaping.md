# JS Syntax Escaping — web_ui.html

Referencia rápida para el bug más común y destructivo en `web_ui.html`: comillas simples que rompen strings JS cuando generan HTML dinámicamente.

## El patrón

`web_ui.html` contiene JS inline que genera HTML por concatenación de strings:

```js
h = '<div>...';
h += '<a onclick="func(\'x\')">...</a>'; // bien, escapado
h += '<a onclick="setStatus('all')">...</a>'; // MAL, rompe el string JS
```

El problema: el string JS está delimitado por comillas simples (`var h = '...';`). Si dentro del contenido hay un caracter `'`, el parser JS lo interpreta como el cierre del string, y todo lo que sigue se vuelve código JS inválido.

## Casos reales encontrados

### 1. Funciones de filtro en onclick

generadas en tabs de filtrado por status (Goals, Reminders, etc.):

```js
// BUG: 'all' es comilla simple dentro del string JS delimitado por comillas simples
h += '<a onclick="event.preventDefault();setProjGoalStatus('all');return false;">Todos</a>';

// FIX: escapar con backslash
h += '<a onclick="event.preventDefault();setProjGoalStatus(\'all\');return false;">Todos</a>';
```

### 2. Asignaciones de variables en onclick

Variables de estado temporales asignadas inline:

```js
// BUG: _var='value' es comilla simple dentro del string JS
h += '<a onclick="event.preventDefault();_varStatus=\'today\';renderView();return false;">Hoy</a>';

// FIX: escapar ambas comillas
h += '<a onclick="event.preventDefault();_varStatus=\'today\';renderView();return false;">Hoy</a>';
```

### 3. Comparaciones en ternarios

```js
// OK: el operador === compara strings con comillas simples, pero las comillas están dentro del código JS, no dentro del string HTML delimitador
(gsf === 'all' ? 'active' : '')
```

Este caso es **safe** porque las comillas `'` de `===` y `?` están en el lado derecho del `=` JS, no dentro del string HTML que contiene el `'` delimitador.

## Regla de oro

**En cualquier línea que genere HTML con `h += '...'`, buscar el patrón de comillas simples y escaparlas.**

La regex que detecta los problemas:

```python
# Escapar asignaciones: _var='value'; -> _var=\'value\'; en strings JS
re.sub(r"(;\w+=)('[^']+')", lambda m: m.group(1) + "\\'" + m.group(2)[1:-1] + "\\';", text)

# Escapar funciones setXxx('value') -> setXxx(\'value\')
re.sub(r"(set[A-Za-z]+Status)\(('[^']+)'\)", lambda m: m.group(1) + "(\\'" + m.group(2)[1:-1] + "\\')", text)
```

## Validación

**`node --check` es el método de validación obligatorio.** Extraer solo el JS del HTML y correr:

```bash
python3 -c "import re; h=open('web_ui.html').read(); js=re.split(r'</script>', re.split(r'<script>', h)[1])[0]; open('/tmp/pb_check.js','w').write(js); print(len(js))"
node --check /tmp/pb_check.js
```

Si `node --check` falla, el error es casi siempre este patrón de comillas chocantes. La página se quedará en "Cargando..." sin renderizar el sidebar ni los datos.

## Síntoma de este bug

- El browser snapshot muestra: selector "Cargando...", textbox "Buscar...", sin sidebar ni tabs.
- No hay error visible en el HTML — el JS simplemente no ejecuta.
- La consola del browser muestra un `SyntaxError` genérico (`Uncaught SyntaxError: Unexpected identifier 'all'`) en la primera línea del JS inline.
