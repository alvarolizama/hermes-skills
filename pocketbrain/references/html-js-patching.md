# HTML+JS Patching Strategy — web_ui.html

`web_ui.html` es un archivo único de ~50KB con HTML, CSS y JS inline. Modificarlo es una operación común pero frágil: los parches de `patch` con `old_string`/`new_string` pueden fallar por escaping de comillas, múltiples reemplazos similares, o truncamiento si el archivo es muy grande.

## Patrón: Python script para reemplazos masivos

Cuando hay **más de 3 cambios** simultáneos (ej. refactor de tabs, cambio de iconos, mejora de markdown, CSS nuevo), es más robusto usar `execute_code` (Python) con `open()` en lugar de múltiples `patch` individuales:

```python
import os
from html import escape
path = os.path.expanduser('~/.hermes/skills/productivity/pocketbrain/scripts/web_ui.html')
with open(path) as f: h = f.read()

# 1. Reemplazo exacto de string (verificar presencia primero)
old = '...'
new = '...'
assert old in h, f'Match not found: {old[:60]}...'
h = h.replace(old, new, 1)

# 2. Reemplazo CSS block (buscar old_string exacto)
old_css = '.card{...}'
new_css = '.card{...}\n.md-content h2{...}'
assert old_css in h
h = h.replace(old_css, new_css)

with open(path, 'w') as f: f.write(h)
print(f'Done: {len(h)} bytes')
```

## Reglas
1. **Nunca parchear a ciegas** — siempre `assert old in h` o `assert h.count(old)==1` para evitar reemplazar el match incorrecto.
2. **Backup antes de tocar** — `cp web_ui.html web_ui.html.bak` (el repo git también sirve como backup).
3. **Verificar después** — `wc -c` y `node --check` inmediatamente después de cualquier escritura.
4. **Restaurar de backup si algo se rompe** — si `node --check` falla, restaurar desde el backup y re-emprender con una estrategia más granular.

## Pitfall: comillas simples dentro de strings JS que generan HTML

Cuando el JS genera HTML con un string literal delimitado por comillas simples (`h+='<div ...>'`), cualquier comilla simple dentro del HTML generado — como atributos `onclick="setX('val')"` o asignaciones `_var='value'` — **rompe el string literal JS** y crashea todo el parser. El resultado es app en blanco con "Cargando..." infinito, y `node --check` reporta `SyntaxError: Unexpected identifier 'val'`.

**Ejemplo que truena:**
```javascript
// ROTO — las comillas simples en 'all' terminan el string JS
h+='<div onclick="setProjGoalStatus(’all’)...">';
// CORRECTO — escapadas como \' 
h+='<div onclick="setProjGoalStatus(\\'all\\')...">';
```

**Fix automático (Python):**
```python
import re

def esc_status(m):
    return m.group(1) + "(" + "\\'" + m.group(2) + "\\')"

def esc_assign(m):
    return m.group(1) + "\\'" + m.group(2) + "\\'"

content = re.sub(r"(set[A-Za-z]+Status)\'([^']+)'\)", esc_status, content)
content = re.sub(r"(;[A-Za-z_]+=)(\'[^']+')\b", esc_assign, content)
```

**Regla:** todo generador de HTML dentro de strings JS debe usar comillas dobles para atributos HTML y las comillas simples internas que vayan a JS deben escaparse. Correr `python3 scripts/validate_ui.py` (ver scripts) antes de cada deploy detecta y corrige esto automáticamente.

**Script disponible:** `scripts/validate_ui.py` en este repositorio. `validate_ui.py --fix` aplica la regex de arriba y luego corre `node --check`. Si el script no existe, usar `execute_code` con el código inline.

## Pitfall: write_file trunca archivos grandes

`write_file` puede truncar silenciosamente archivos >9KB. Si `wc -c` muestra un tamaño inesperado, reescribir con `execute_code` (Python) que no tiene el límite de Hermes, o usar `patch` si el cambio es pequeño. Nunca usar `write_file` como bloc de notas temporal para `web_ui.html` — sobreescribe todo el JS/CSS/HTML sin advertencia.
