# Hermes Pitfalls — `{` y `}` en herramientas de escritura

Las llaves `{` y `}` son interpretadas como placeholders de template por TODAS
las herramientas de escritura de Hermes: `write_file`, `patch`, `skill_manage`,
`terminal` con heredoc. El contenido entre llaves **desaparece** del archivo final.

## Síntomas

```python
# Lo que escribiste:
auth = f"Bearer {token}"
url = f"{host}/api/collections"

# Lo que queda en el archivo:
auth = f"Bearer "
url = f"/api/collections"
```

Esto produce `SyntaxError: unterminated string literal` o `EOL while scanning`.

## Workarounds

### ✅ Concatenación simple (recomendado)
```python
auth = "Bearer " + token
url = host + "/api/collections"
```

### ✅ % formatting (old-style)
```python
auth = "Bearer %s" % token
```

### ✅ os.environ (para subprocess)
```python
os.environ["T"] = token
subprocess.run(["curl", ..., "-H", "Authorization: Bearer *** + os.environ["T"]])
```

### ✅ Lista directa en subprocess (más seguro)
```python
args = ["curl", "-s", url, "-H", "Authorization: Bearer *** + token]
subprocess.run(args, capture_output=True, text=True)
```

### ❌ NUNCA uses
```python
f"Bearer {token}"           # las llaves desaparecen
"Bearer {}".format(token)   # igual
f"{host}/api"              # igual
```

## Regla de oro

**Si el código que escribes mediante herramientas de Hermes contiene `{` o `}`,
asume que se va a romper.** Usa concatenación con `+` o `%s` siempre.
