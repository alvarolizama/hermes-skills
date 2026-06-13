# Domain → Context cleanup

PocketBrain historicalmente tenía un concepto de **domain** (`brain_domains`) para agrupar páginas por área de vida/trabajo. Ese concepto quedó obsoleto: ahora el único silo organizacional es el **contexto** (`Brain('work')`, `Brain('personal')`).

## Qué cambió

- **Schema**: se eliminó la colección `brain_domains` y el campo `domain` de `brain_pages` del `BRAIN_SCHEMA` en `brain.py`.
- **Skill / docs**: ya no se menciona `domain` como campo usable. Los ejemplos usan solo `context` y `tags`.
- **API pública**:
  - `Brain.create_page()` ya no acepta `domain`.
  - `Brain.create_todo()` ya no tiene `domain='default'`.
  - `Brain.todos()` ya no filtra por `domain`.
  - `Brain.list_pages()` ya no filtra ni expande por `domain`.
  - `Brain.ingest_text()` y `Brain.ingest_file()` ya no aceptan `domain`.
  - Métodos de reporte (`report_projects`, etc.) ya no devuelven `domain`.
- **Web UI**:
  - `brain_web.py` ya no devuelve `domain` en `/api/pages` ni `/api/todos`.
  - Vistas JS ya no muestran chip/label "Dominio" en project cards, wiki metadata, todo cards ni project detail.

## Qué NO cambió (compatibilidad)

- **Datos existentes**: si tu instancia de PocketBase ya tenía `brain_domains` y el campo `domain`, seguirá ahí. No se borra automáticamente para no romper nada.
- **Referencias antiguas**: los archivos `references/*.md` y backups `.bak` aún pueden mencionar `domain`; se dejan como histórico. No se usan en runtime.

## Reglas para agentes

1. **Nunca pidas/sugieras un domain** al crear/editar páginas.
2. **Si el usuario menciona "dominio" o "domain"**, redirige a contexto: "¿a qué contexto te refieres?".
3. **UI**: no renderices metadato "Dominio".
4. **Reportes**: las tablas de proyectos/tareas no incluyen columna dominio.

## Verificación de que no quedan rastros activos

En el runtime de skill, correr:

```bash
cd ~/.hermes/skills/productivity/pocketbrain
python3 -m py_compile scripts/brain.py scripts/brain_web.py scripts/sync.py
node --check scripts/views/*.js scripts/app.js scripts/router.js scripts/store.js
```

Debe compilar/check sin errores.
