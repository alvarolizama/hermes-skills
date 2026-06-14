# Arquitectura de variables de entorno

## Separación de responsabilidades

Cada skill es dueño de sus propias credenciales:

| Skill | Variables en `.env` | Quién las lee |
|-------|--------------------|---------------|
| `pocketbase` | `POCKETBASE_HOST`, `POCKETBASE_EMAIL`, `POCKETBASE_PASSWORD` | Nadie — `pb.py` no lee env vars |
| `pocketbrain` | `POCKETHOST_HOST`, `POCKETHOST_EMAIL`, `POCKETHOST_PASSWORD`, `POCKETBRAIN_CONTEXT` | `brain.py` → `_pocketbrain_pb()` y `Brain(context_name='')` |

> **Naming final acordado con el usuario:** las credenciales de conexión usan el prefijo `POCKETHOST_`. El contexto default del agente conserva su nombre original `POCKETBRAIN_CONTEXT`. No renombrar a `POCKETHOST_CONTEXT`.

## Flujo de conexión

```
~/.hermes/.env
  ├── POCKETHOST_HOST=http://zima.vpn.cloud:18090
  ├── POCKETHOST_EMAIL=soy@alvarolizama.com
  └── POCKETHOST_PASSWORD=***

        ↓ _pocketbrain_pb() lee y pasa a quick_pb()

  quick_pb(host, email, password)
        ↓
  PB(host, email, password)  ← pb.py no toca os.environ
        ↓
  pb.auth() → token JWT
```

## pb.py: módulo sin dependencia de entorno

```python
# CORRECTO — params explícitos
pb = quick_pb('http://localhost:8090', 'admin@example.com', 'secret')

# INCORRECTO — pb.py ya no lee env vars
pb = quick_pb()  # ValueError: PB() requiere 'host'
```

## brain.py: _pocketbrain_pb()

```python
def _pocketbrain_pb():
    """Crea un PB autenticado usando POCKETHOST_* del .env."""
    env = _load_pocketbrain_env()
    host = env.get('POCKETHOST_HOST', 'http://localhost:8090')
    email = env.get('POCKETHOST_EMAIL', '')
    password = env.get('POCKETHOST_PASSWORD', '')
    return quick_pb(host, email, password)
```

## brain_web.py, sync.py, graph.py

Estos scripts cargan el `.env` directamente y pasan las credenciales a `quick_pb()`:

```python
env = {}
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

pb = quick_pb(env['POCKETHOST_HOST'], env['POCKETHOST_EMAIL'], env['POCKETHOST_PASSWORD'])
```

## Por qué existen POCKETBASE_* y POCKETBRAIN_*

- `POCKETBASE_*`: legado, mantenido por si otros scripts/clients los usan.
- `POCKETBRAIN_*`: las que usa el skill pocketbrain. Apuntan a la misma instancia (mismos valores).
- Separarlos permite en el futuro apuntar a instancias distintas si se necesita.
