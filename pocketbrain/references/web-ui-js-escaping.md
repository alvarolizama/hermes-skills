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

## Patrón complementario: `\'` como concatenación de strings JS

Hay un segundo patrón que NO es un bug de escapamiento — es intencional y confunde cuando se edita el breadcrumb en `showPage()`:

```javascript
h += '...texto...\'' + variable + '\'...mas texto...\'' + var2 + '\'...';
```

`\'` aquí significa: backslash + quote = **escaped quote**, que NO termina el string. El `'` es solo el carácter `'` dentro del contenido del string.

`'` (sin backslash) termina el string exterior. Se usa para concatenar variables JS:

```javascript
h += '...<a href=\"...\">\'' + page_type + '\'</a> \'' + title + '\'</div>';
```

| Secuencia en JS | Significado | Ejemplo en HTML generado |
|----------------|-------------|--------------------------|
| `\'` | Carácter `'` literal dentro del string | `onclick="showTab('...')"` |
| `'` (sin backslash) | Termina el string exterior | Permite `+variable+` concatenación |
| `\"` | Carácter `"` literal dentro del string | `href="..."` |

**Regla de edición:** cuando veas `\'` en el archivo, son comillas ESCAPADAS dentro del string. Cuando veas `'` SOLO (sin backslash antes), es el terminador del string exterior. **Nunca cambiar `\'` a `'` ni viceversa** sin entender el rol.

### Errores comunes al editar el breadcrumb

Al modificar el breadcrumb en `showPage()`, es fácil confundir los roles:

```javascript
// Original correcto — \' = escaped quote (dentro del string)
// ' (solo) = string terminator (permite +variable+)
h += '← Todos</a> · <a href=\"...\" onclick=\"showTab(\'type_\'+p.page_type)\" ...>'
    + '\'' + p.page_type + '\'</a> \'' + p.title + '\'</div>';

// Error común: usar \' donde debería ir ' (el string nunca termina)
// → el ; después del string queda DENTRO del string
// Síntoma: "Cargando...", showPage() no existe
```

**Para parchar desde Python:**
```python
# ✅ Correcto: Python double-quoted string
new = "\\'+p.page_type+\\'"   # output: \'+p.page_type+\'

# ❌ Incorrecto: Python single-quoted string  
new = '\\'+p.page_type+'\\'   # output: '+p.page_type+' (sin backslashes!)
```

```bash
python3 -c "import re; h=open('web_ui.html').read(); js=re.split(r'</script>', re.split(r'<script>', h)[1])[0]; open('/tmp/pb_check.js','w').write(js); print(len(js))"
node --check /tmp/pb_check.js
```

Si `node --check` falla, el error es casi siempre este patrón de comillas chocantes. La página se quedará en "Cargando..." sin renderizar el sidebar ni los datos.

## Síntoma de este bug

- El browser snapshot muestra: selector "Cargando...", textbox "Buscar...", sin sidebar ni tabs.
- No hay error visible en el HTML — el JS simplemente no ejecuta.
- La consola del browser muestra un `SyntaxError` genérico (`Uncaught SyntaxError: Unexpected identifier 'all'`) en la primera línea del JS inline.

## Cuando patch falla: edición con bytearray

El tool `patch` puede fallar con "escape-drift" en archivos con escapamiento anidado (JS dentro de HTML, comillas triples). Cuando pase, usar **bytearray slice-replace** en Python:

```python
with open(path, 'rb') as f:
    data = bytearray(f.read())

# Buscar texto exacto con data.find()
idx = data.find(b'texto exacto')
if idx > 0:
    new_bytes = b'texto de reemplazo'
    data[idx:idx+len(b'texto exacto')] = new_bytes

with open(path, 'wb') as f:
    f.write(data)
```

**Patrón de trabajo para web_ui.html:**
1. Usar `repr(data[idx-20:idx+80])` para ver los bytes exactos alrededor
2. `data.find(b'patron')` con los bytes exactos (escapar con `b'\\\\'` para un backslash literal)
3. Slice-replace de cualquier longitud
4. Validar inline JS con `node --check`
