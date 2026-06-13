# Schema Audit — Valida integridad del pocketbrain

Procedimiento para auditar que el schema de colecciones sea consistente entre:
1. **BRAIN_SCHEMA** (lo que `setup_contexts()` crea)
2. **schema.md** (lo que la documentación dice)
3. **Código vivo** (lo que los métodos realmente escriben/leen)
4. **brain_web.py** (lo que los endpoints sirven)

## Cuándo correrlo

- Después de una migración de colecciones (ej. unificación a brain_pages)
- Cuando sospechas que hay colecciones huérfanas o muertas
- Antes de agregar un nuevo page_type o método
- Cuando `setup_contexts()` falla porque referencia colecciones que no coinciden

## Procedimiento

### 1. Leer BRAIN_SCHEMA y CREATION_ORDER

```python
from brain import BRAIN_SCHEMA, CREATION_ORDER
print("BRAIN_SCHEMA keys:", list(BRAIN_SCHEMA.keys()))
print("CREATION_ORDER:", CREATION_ORDER)
```

Verificar que:
- `BRAIN_SCHEMA` tiene exactamente las colecciones que `setup_contexts()` debe crear
- `CREATION_ORDER` contiene los mismos nombres (el orden respeta dependencias FK)
- Los `collectionId` en campos `relation` apuntan a colecciones que existen en BRAIN_SCHEMA
- `contexts` es la primera (sin dependencias)
- `brain_pages` se crea antes que `brain_page_versions` y `brain_log` (que dependen de ella)

### 2. Comparar vs schema.md

```python
# schema.md describe las colecciones que el skill documenta
# Busca colecciones en schema.md que no están en BRAIN_SCHEMA:
documented_but_not_created = set_of_documented - set(BRAIN_SCHEMA.keys())
created_but_not_documented = set(BRAIN_SCHEMA.keys()) - set_of_documented
```

Las colecciones documentadas pero no creadas pueden ser:
- **Legacy** (se unificaron, ej. brain_todos → brain_pages con page_type='todo')
- **Muertas** (ya nadie las usa, hay que limpiar la doc)
- **Nunca existieron** (la documentación se adelantó al código)

### 3. Revisar qué colecciones usa cada script

```bash
# Buscar todas las referencias a colecciones en scripts/ (excluyendo BRAIN_SCHEMA)
grep -rn "'brain_\|'contexts'" ~/.hermes/skills/productivity/pocketbrain/scripts/*.py \
  | grep -v 'BRAIN_SCHEMA\|#\|\.pyc' | grep -o "'[a-z_]*'" | sort -u
```

Comparar contra BRAIN_SCHEMA. Las que no están en BRAIN_SCHEMA son:
- **Stale references** (la colección ya no existe, hay que migrar el código)
- **Colecciones externas** (podrían ser de otro skill, pero improbable)

### 4. Verificar consistencia lectura/escritura

Para cada endpoint en `brain_web.py`, verificar:
- ¿De qué colección lee?
- ¿Los métodos que escriben datos similares usan la misma colección?

Patrón de bug detectado en v2.21:
```
brain_deliverables (escritura en create_deliverable) ≠ brain_pages (lectura en /api/deps)
brain_files (escritura en attach_file) ≠ brain_pages (lectura en /api/files)
```

### 5. Ejecutar setup_contexts() para verificar que crea sin error

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 -c "
from brain import _pocketbrain_pb, setup_contexts
pb = _pocketbrain_pb()
result = setup_contexts(pb)
for name, status in result.items():
    print(f'{name}: {status[\"status\"]}')
"
```

### 6. Validar sintaxis de todos los scripts

```bash
python3 -c "import brain; print('brain.py OK')"
python3 -c "import sync; print('sync.py OK')"
python3 -m py_compile brain_web.py && echo "brain_web.py OK"
```

## Checklist final

- [ ] `BRAIN_SCHEMA` y `CREATION_ORDER` coinciden (mismos N nombres)
- [ ] `schema.md` describe solo colecciones que existen
- [ ] Cero referencias a colecciones legacy en `scripts/*.py` (ver paso 3)
- [ ] Todos los endpoints de `brain_web.py` leen de colecciones que existen
- [ ] Todos los métodos de `Brain` escriben a colecciones que existen
- [ ] `page_type` values en BRAIN_SCHEMA cubren todos los usados por brain_web.py
- [ ] `setup_contexts()` se ejecuta sin error
- [ ] Todos los scripts compilan sin error de sintaxis
- [ ] Dependencias externas documentadas (pocketbase skill, curl, env vars)
