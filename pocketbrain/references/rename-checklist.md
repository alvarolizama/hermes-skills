# Mass Rename Checklist

Antes de cualquier rename masivo (ej. `brains` → `contexts`, `brain_name` → `context_name`):

1. **Grep por string exacto** — incluir comillas, puntos, guiones bajo: `'brain_name'`, `\.brain_name`, `"brain"`
2. **Verificar assignments RHS**: `self.foo = bar_name` — la variable RHS NO se renombre por search/replace
3. **Verificar string constants**: `create('brains', ...)`, `filter="brains"` — los nombres de colección en PB
4. **Verificar attribute access**: `brain.brain_name` donde `brain` es la variable local — la variable local no cambia, pero el atributo sí
5. **Verificar local variables**: `brain = ...` dentro de métodos — pueden quedar con nombre viejo

Post-rename: ejecutar el script y seguir traceback hasta 0 errores. No confiar en grep.
