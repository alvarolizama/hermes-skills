# PocketBrain — Paradigma LLM Wiki

Cómo usar PocketBrain siguiendo el patrón de Karpathy's LLM Wiki: ingesta de fuentes, creación de conocimiento con trazabilidad, calidad de la información, y mantenimiento.

---

## Flujo de trabajo completo

```
Fuente (URL/PDF/texto)
    │
    ▼
1. INGEST → brain.create_page(page_type='raw', source_url, source_sha256)
    │
    ▼
2. EXTRAER → identificar entidades, conceptos, comparaciones
    │
    ▼
3. CREAR/ACTUALIZAR → brain.create_page() con page_type='entity'|'concept'|'comparison'
    │  → body con [[wikilinks]] a otras páginas
    │  → confidence='high'|'medium'|'low'
    │  → provenance markers ^[slug-de-pagina-raw]
    │
    ▼
4. MANTENER → brain.lint() + brain.archive_old() + brain.detect_drift()
```

---

## 1. Ingesta de fuentes raw

Cuando encuentres un artículo, paper o documento relevante:

```python
# 1a. Texto directo (artículo web, nota)
brain.ingest_text(
    text="## Transformer Architecture\n\n...",
    title="Attention Is All You Need - Resumen",
    source_url="https://arxiv.org/abs/1706.03762",
    page_type='raw',        # marca como fuente original
    domain="investigacion",
    tags=["transformer", "deep-learning"]
)
# → SHA256 se calcula automáticamente
```

```python
# 1b. Archivo (PDF, TXT)
brain.ingest_file(
    filepath="/tmp/paper.pdf",
    title="Paper RLHF 2024",
    source_url="https://arxiv.org/abs/2401.00001",
    domain="learning",
    tags=["rlhf", "alignment"]
)
# → SHA256 del archivo se calcula automáticamente
```

**Regla:** Cada fuente raw es inmutable. No se edita después de ingerida. Si la fuente cambia, se ingesta de nuevo y `detect_drift()` lo detectará.

---

## 2. Creación de páginas de conocimiento

De cada fuente extraes entidades, conceptos y comparaciones:

### Entity (persona, organización, producto, modelo)

```python
brain.create_page(
    title="GPT-4o",
    body="## Overview\nGPT-4o es un modelo multimodal...\n\n## Capacidades\n- Visión\n- Audio\n\n## Referencias\n^[mi-articulo-gpt4]\n",
    page_type='entity',
    confidence='high',        # bien soportado por múltiples fuentes
    domain="investigacion",
    tags=["modelo", "openai"]
)
```

### Concept (tema, técnica, idea)

```python
brain.create_page(
    title="Attention Mechanism",
    body="## Definición\nEl mecanismo de atención...\n\n## Variantes\n- [[Self-attention]]\n- [[Cross-attention]]\n\n^[mi-paper-transformer]\n",
    page_type='concept',
    confidence='medium',       # bien conocido pero hay debates abiertos
    domain="investigacion",
    tags=["deep-learning", "arquitectura"]
)
```

### Comparison (comparativa side-by-side)

```python
brain.create_page(
    title="GPT-4o vs Claude 3.5 Sonnet",
    body="| Dimensión | GPT-4o | Claude 3.5 |\n|---|---|---|\n| Razonamiento | ... | ... |\n| Velocidad | ... | ... |",
    page_type='comparison',
    confidence='medium',
    domain="investigacion",
    tags=["comparativa", "modelos"]
)
```

### Provenance markers `^[slug]`

Usa `^[slug-de-la-pagina-raw]` al final de párrafos cuyas afirmaciones vienen de una fuente específica:

```
Según el paper original, la arquitectura Transformer...
^[attention-is-all-you-need]
```

El markdown renderer lo convierte en un link de cita en superscript. Si el slug no existe, se muestra `[?]` en rojo.

---

## 3. Calidad de la información

### Confidence

| Valor | Cuándo usarlo |
|-------|---------------|
| `high` | Múltiples fuentes confiables coinciden |
| `medium` | Bien documentado pero hay debates/incertidumbre |
| `low` | Fuente única, opinión, especulación |

```python
# Actualizar confidence después de nueva evidencia
brain.update_page('gpt-4o', confidence='high')
```

### Contested (contradicciones)

Cuando dos fuentes dicen cosas opuestas:

```python
brain.update_page(
    'rendimiento-modelos',
    contested=True,
    contradictions='benchmark-resultados-2024'
)
```

En la UI se marca con borde rojo y ⚠ Sí en el sidebar.

### Frontmatter validation

```python
# Verificar que todas las páginas tienen campos requeridos
brain.validate_frontmatter()
# → Devuelve páginas que faltan campos obligatorios según su page_type
```

| page_type | Campos requeridos |
|-----------|-------------------|
| `entity` | title, body, summary, domain |
| `concept` | title, body, summary |
| `comparison` | title, body, domain |
| `raw` | title, source_url, source_sha256 |
| `project` | title, body, domain |
| `query` | title, body |

---

## 4. Mantenimiento

### Lint completo

```python
report = brain.lint()
# Devuelve:
# - orphans: páginas sin inbound [[wikilinks]]
# - broken_links: [[links]] que apuntan a páginas que no existen
# - low_confidence: páginas con confidence='low'
# - contested_pages: páginas marcadas como contested
# - invalid_tags: tags no autorizados por la taxonomía
# - oversized: páginas > 200 líneas
# - drift: páginas raw cuyo SHA256 cambió
# - frontmatter_issues: páginas que faltan campos requeridos
```

En la web UI: click en **✅ Lint** en el sidebar, luego "Refrescar".

### Detección de drift

```python
# Detectar si páginas raw fueron modificadas después de la ingesta
brain.detect_drift(limit=50)
# → Compara SHA256 almacenado vs body actual
# → Útil cuando re-ingestas una URL y quieres saber si cambió
```

### Archive automático

```python
# Vista previa de páginas candidatas a archivar
brain.archive_old(days=90, dry_run=True)

# Archivar realmente
brain.archive_old(days=90, dry_run=False)
```

### Rotación de log

```python
# Verificar tamaño del log y archivar si excede 500 entradas
brain.rotate_log(max_entries=500)
# → Crea una página raw con el snapshot del log y trunca brain_log
```

---

## 5. Consulta

```python
# Buscar en todas las páginas
brain.search("transformer attention")
# → Resultados rankeados por relevancia

# Obtener índice completo agrupado por tipo
brain.index()
# → {entity: [...], concept: [...], comparison: [...], query: [...], raw: [...]}

# Listar últimas operaciones
brain.recent_logs(limit=20)
```

En la web UI: usa el índice (click en **Wiki** en sidebar) con tabs por tipo y confidence badges.

---

## 6. Vinculación con proyectos

PocketBrain permite ligar páginas de conocimiento a proyectos:

```python
# Crear página como parte de un proyecto
brain.create_page(
    title="Arquitectura del MVP",
    body="## Decisiones técnicas\n...",
    page_type='concept',
    domain="projects",
    tags=["arquitectura", "mvp"]
)

# Crear goals, tareas y recordatorios ligados a la página
brain.create_goal("Implementar cola de mensajes", type="milestone",
                  project_slug="arquitectura-del-mvp", deadline="2026-08-01")
brain.create_todo("Diseñar schema de la cola", domain="projects",
                  page_slug="arquitectura-del-mvp")
brain.create_reminder("Revisión de arquitectura", date="2026-07-15",
                      time="10:00", page_slug="arquitectura-del-mvp")
```

Esto es lo que **no existe** en el LLM Wiki original — la integración knowledge + execution.

---

## Referencia de métodos

| Método | Para |
|--------|------|
| `ingest_text(text, title, source_url, ...)` | Ingerir fuente raw desde texto |
| `ingest_file(filepath, title, source_url, ...)` | Ingerir fuente raw desde archivo |
| `create_page(title, body, page_type, confidence, ...)` | Crear página de conocimiento |
| `update_page(slug, confidence, contested, ...)` | Actualizar calidad/calidad |
| `append_to_page(slug, text, heading)` | Agregar contenido sin reemplazar |
| `archive_page(slug)` | Archivar página (soft delete) |
| `search(query)` | Buscar en todas las páginas |
| `index()` | Obtener índice por tipo |
| `lint()` | Auditoría completa del cerebro |
| `detect_drift()` | SHA256 diff en páginas raw |
| `validate_frontmatter()` | Campos requeridos por page_type |
| `archive_old(days, dry_run)` | Archivar páginas sin actualizar |
| `rotate_log(max_entries)` | Rotar brain_log |
| `get_page(slug)` | Obtener página por slug |
| `get_history(slug)` | Historial de versiones |
