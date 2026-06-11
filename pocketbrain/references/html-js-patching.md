# Web UI HTML/JS Patching Strategy

## Problem

The `patch` tool fails with `Escape-drift detected` on `web_ui.html` because the file contains JS-heavy escaping:
- `\"` (escaped double quotes inside JS strings)
- `\\'` (escaped single quotes inside onclick handlers)
- `\\` (backslash escapes in regex patterns)

The `patch` tool tries to normalize these and fails because the file's escaping doesn't match what the agent serialized.

## Solution: Python Script Patches

Instead of `patch`, write a temporary Python script and execute it:

```python
# Write to /tmp/patch_xyz.py
with open(path, 'r') as f:
    content = f.read()

old = "the exact text to find (use repr() to debug)"
new = "the replacement text"

count = content.count(old)
assert count >= 1, f"Found {count} occurrences"

content = content.replace(old, new, 1)

with open(path, 'w') as f:
    f.write(content)
```

Key advantages:
- Exact byte-level matching (no escape normalization)
- `assert count >= 1` catches missing patterns immediately
- Can handle single or multiple replacements
- Works reliably with `\"`, `\\'`, regex patterns, unicode escapes

## Debugging Hard-to-Find Patterns

When `content.count(old)` returns 0:

1. Use `content.find(unique_substring)` to locate the region
2. Extract a chunk: `content[idx:idx+300]`
3. Print with `repr()` to see exact escaping

```python
idx = content.find("return tx.replace")
chunk = content[idx:idx+350]
print(repr(chunk))
```

## Save and Run

```bash
python3 /tmp/patch_xyz.py
```

Always delete the temp file after:
```bash
rm /tmp/patch_xyz.py
```

## ⚠️ Pitfall 1: Python template artifacts en JS generado

Cuando usas Python triple-quoted strings (`"""..."""`) para generar JS que contiene caracteres especiales, **NUNCA** uses `chr()` o `'''` dentro del string literal — el código Python se escribe literalmente en el JS de salida:

```python
# ❌ MAL: Python chr() se escribe literal en el JS
new_code = """var h='<h1>""" + chr(9989) + """ Lint</h1>';"""
# → JS: var h='<h1>''' + chr(9989) + ''' Lint</h1>';  ← SyntaxError!

# ✅ BIEN: Embed el character real como UTF-8
CHECK_MARK = "\u2705"
new_code = f"""var h='<h1>{CHECK_MARK} Lint</h1>';"""
# → JS: var h='<h1>✅ Lint</h1>';  ← OK
```

**Regla:** Si necesitas emojis o caracteres Unicode en el JS generado desde Python:
1. Asigna el char a una variable Python: `my_char = "\u2705"` o `my_char = "✅"`
2. Usa f-strings o `.format()` para interpolar
3. **No** uses concatenación con `chr()` ni `'''` dentro del string literal

**Para surrogate pairs** (emoji 🔄 = U+1F504):
```python
# ✅ BIEN: Python 3 maneja chars > 0xFFFF naturalmente
refresh_icon = "\U0001F504"  # 🔄
# Alternativa: usar el char literal directamente
refresh_icon = "🔄"
```

## ⚠️ Pitfall 2: `open(path, 'wb').write()` con surrogates trunca el archivo a 0 bytes

Si escribes un archivo en modo binario (`'wb'`) y el contenido tiene **lone surrogates** (ej. `\ud83d` sin su `\udd04` acompañante), Python lanza `UnicodeEncodeError` y el archivo se queda en **0 bytes** — corrupción total sin recuperación.

```python
# ❌ MAL: Surrogate pair mal formado → UnicodeEncodeError → archivo 0 bytes
content = "text \ud83d\udd04 more text"  # \ud83d\udd04 es 🔄 pero si escríbimos mal...
with open('web_ui.html', 'wb') as f:
    f.write(content.encode('utf-8'))  # UnicodeEncodeError if surrogates present

# ✅ BIEN: Usar UTF-8 nativo
content = "text 🔄 more text"  # El char real, no escapes
with open('web_ui.html', 'w', encoding='utf-8') as f:
    f.write(content)

# ✅ BIEN (modo binario con string limpio):
with open('web_ui.html', 'wb') as f:
    f.write(content.encode('utf-8'))  # Solo si content no tiene surrogates
```

**Verificación post-escritura:** Siempre revisar que el archivo tiene tamaño esperado:
```bash
wc -c web_ui.html
# Si muestra 0 → el archivo se corrompió, restaurar de git y re-aplicar
```

## ⚠️ Pitfall 3: Zombie server process sirve versión OLD

Después de parchear `web_ui.html` y reiniciar `brain_web.py`, el proceso viejo puede quedar vivo escuchando el puerto y sirviendo la versión sin el parche. `process(action='kill')` (vía API de Hermes) puede fallar silenciosamente.

**Siempre verificar que el server sirve el parche:**
```bash
# 1. Confirmar que el archivo en disco tiene el cambio
grep -n 'unique pattern from your patch' web_ui.html

# 2. Matar cualquier proceso zombie en el puerto
lsof -i :8899
kill -9 PID   # force kill, no confiar en kill normal

# 3. Reiniciar y verificar que el HTML servido tiene el parche
python3 brain_web.py --port 8899 &
curl -s http://localhost:8899/ | grep -n 'unique pattern from your patch'
```

Si el grep sobre el HTML servido no encuentra el patrón, el server está sirviendo código viejo — el proceso zombie sigue vivo.
