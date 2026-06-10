# Arquitectura de variables de entorno

## Separación de responsabilidades

Cada skill es dueño de sus propias credenciales:

| Skill | Variables en `.env` | Quién las lee |
|-------|--------------------|---------------|
| `pocketbase` | `POCKETBASE_HOST`, `POCKETBASE_EMAIL`, `POCKETBASE_PASSWORD` | Nadie — `pb.py` no lee env vars |
| `pocketbrain` | `POCKETBRAIN_HOST`, `POCKETBRAIN_EMAIL`, `POCKETBRAIN_PASSWORD` | `brain.py` → `_pocketbrain_pb()` |

## Flujo de conexión

```
~/.hermes/.env
  ├── POCKETBRAIN_HOST=http://zima.vpn.cloud:18090
  ├── POCKETBRAIN_EMAIL=soy@alvarolizama.com
  └── POCKETBRAIN_PASSWORD=***

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
    """Crea un PB autenticado usando POCKETBRAIN_* del .env."""
    env = _load_pocketbrain_env()
    host = env.get('POCKETBRAIN_HOST', 'http://localhost:8090')
    email = env.get('POCKETBRAIN_EMAIL', '')
    password = env.get('POCKETBRAIN_PASSWORD', '')
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

pb = quick_pb(env['POCKETBRAIN_HOST'], env['POCKETBRAIN_EMAIL'], env['POCKETBRAIN_PASSWORD'])
```

## Por qué existen POCKETBASE_* y POCKETBRAIN_*

- `POCKETBASE_*`: legado, mantenido por si otros scripts/clients los usan.
- `POCKETBRAIN_*`: las que usa el skill pocketbrain. Apuntan a la misma instancia (mismos valores).
- Separarlos permite en el futuro apuntar a instancias distintas si se necesita.
