# PocketBrain — Repo Maintenance

Guidelines from Álvaro about how this repo is maintained alongside the skill runtime.

## What lives in the repo vs what does not

The repo `~/Repos/personal/hermes-skills` is a **public skills tap** for Hermes, NOT a workspace for agent plans.

| In repo | NOT in repo |
|---------|-------------|
| `SKILL.md`, `scripts/`, `references/`, `README.md` | `.hermes/plans/` (agent plans directory) |
| Screenshots in `pocketbrain/screenshots/` | Screenshots in repo root `screenshots/` |
| `.gitignore` ignoring `.hermes/` | `.hermes/` tracked by git |

The `.gitignore` at repo root must contain:
```
.here is
```

## Validación del README

Antes de commitear cambios al README, verificar:

1. **Funciones referenciadas**: cualquier llamada en los code blocks del README debe existir en el código real. Buscar el nombre en `scripts/brain.py`:
   ```bash
   grep -n 'def _pb\|def _pocketbrain_pb' pocketbrain/scripts/brain.py
   ```
   Si el README dice `setup_contexts(_pb())` pero el código solo define `_pocketbrain_pb()`, es un link roto.

2. **Puerto del servidor**: verificar que el puerto en el Quick Start coincide con el `--port` que realmente se usa. El SKILL.md y el README deben mostrar el mismo comando.

3. **Variables de entorno**: la sección de Dependencia/Setup en el README debe reflejar EXACTAMENTE lo que usa `brain.py`. Si `brain.py` lee `POCKETBRAIN_HOST`, el README no debe mostrar `POCKETBASE_HOST`.

4. **Screenshots**: confirmar que los paths relativos apuntan a archivos que existen y están en git:
   ```bash
   ls pocketbrain/screenshots/ | wc -l
   git ls-files pocketbrain/screenshots/ | wc -l
   # ambos deben coincidir
   ```

## Screenshots

Screenshots in `README.md` must reflect the **current live UI** (`localhost:8899`).
Naming: `NN-<view-name>.png` (e.g. `01-proyectos.png`, `02-todo.png`) so they sort in visual order.

How to refresh:
```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 brain_web.py --port 8899 --context personal
# Then use browser_navigate + browser_vision to each view
```

## README.md (root vs pocketbrain/)

- Root `README.md` stays terse. It links to `pocketbrain/README.md` for detail.
- `pocketbrain/README.md` has the full screenshots grid, script workflows, architecture table, and setup.
- Avoid duplicating architecture tables or screenshot tables in both files.

## Sync repo from skill runtime

The skill runtime (`~/.hermes/skills/productivity/pocketbrain/`) is the source of truth.
When the skill changes, copy to the repo before committing:

```bash
# Copy to repo
cp ~/.hermes/skills/productivity/pocketbrain/SKILL.md ~/Repos/personal/hermes-skills/pocketbrain/SKILL.md
cp ~/.hermes/skills/productivity/pocketbrain/scripts/*.py ~/Repos/personal/hermes-skills/pocketbrain/scripts/
cp ~/.hermes/skills/productivity/pocketbrain/scripts/*.html ~/Repos/personal/hermes-skills/pocketbrain/scripts/
cp ~/.hermes/skills/productivity/pocketbrain/references/*.md ~/Repos/personal/hermes-skills/pocketbrain/references/
```

Then refresh screenshots, update `pocketbrain/README.md`, commit, and push.

## No commits with `--gpg-sign`

Álvaro uses `--no-gpg-sign` because the GPG key `AE8992E7564B64D2` is not present in this environment. Always commit with `--no-gpg-sign`.
