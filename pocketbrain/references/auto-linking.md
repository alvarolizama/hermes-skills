# PocketBrain — Auto-linking, page_type y backlinks

Cómo funciona el sistema automático de relaciones entre páginas en PocketBrain.

---

## Auto-link via `[[wikilinks]]`

Cuando creas una página con `create_page()`, el body se escanea automáticamente en busca de `[[wikilinks]]`. Cada slug encontrado se resuelve contra las páginas existentes y se guarda en el campo `related_pages` de la nueva página.

```python
# Al crear esta página:
brain.create_page(
    title="Arquitectura Transformer",
    body="El mecanismo de [[attention]] es clave en [[deep-learning]].\nComparado con [[rnn]], el transformer es más eficiente.",
    page_type='concept'
)
# → related_pages se llena automáticamente con los IDs de
#   'attention', 'deep-learning', 'rnn' (si existen)
```

**Soporta alias:** `[[slug|Texto visible]]` → resuelve por `slug`, muestra "Texto visible".

**Slugs que no existen:** se ignoran silenciosamente (no rompen la creación). `lint()` los reporta como `broken_links`.

---

## Auto-backlinks

Cuando la página A linkea a la página B via `[[slug-de-b]]`, la página B recibe automáticamente un backlink en su campo `related_pages`.

```
Página A: "[[gpt-4o]] es un modelo..."
         │
         ▼
Página B (gpt-4o):
  related_pages: [id-de-pagina-A, ...]  ← se agregó solo
```

Esto significa que la graph de conocimiento y las relaciones son **bidireccionales** sin esfuerzo manual.

---

## Auto-suggest de `page_type`

Si no especificas `page_type` al llamar `create_page()`, se infiere automáticamente:

| Heurística | page_type | Ejemplo |
|------------|-----------|---------|
| Título contiene "proyecto", "mvp", "roadmap", "sprint" | `project` | "MVP Lanzamiento 2026" |
| Body empieza con URL o título empieza con "ingest" | `raw` | "Ingest artículo attention" |
| Título contiene " vs " o body tiene tabla | `comparison` | "GPT-4o vs Claude 3.5" |
| Título termina con "?" o empieza con "qué"/"what" | `query` | "¿Qué es transformer?" |
| Título corto (≤3 palabras) sin verbos de acción | `entity` | "GPT-4o", "Rust" |
| Todo lo demás | `concept` | "Arquitectura de cache distribuido" |

```python
# Sin page_type explícito → auto-suggest
brain.create_page(title="GPT-4o", body="...")
# → page_type='entity' (inferido)

# Con page_type explícito → respeta el valor
brain.create_page(title="GPT-4o", body="...", page_type='concept')
# → page_type='concept' (forzado)
```

La función `suggest_page_type(title, body)` está disponible como helper standalone.

---

## `related_slugs` explícito

Además del auto-link desde `[[wikilinks]]`, puedes pasar slugs manualmente:

```python
brain.create_page(
    title="Resumen trimestral",
    body="...",
    page_type='query',
    related_slugs=['proyecto-q1', 'proyecto-q2', 'metricas-2026']
)
# → related_pages incluye los slugs resueltos + los wikilinks del body
```

En `update_page()` también funciona:

```python
brain.update_page('resumen-trimestral', related_slugs=['nuevo-proyecto'])
```

---

## `build_backlinks()` — Reconstrucción total

Si ya tienes páginas sin backlinks (creadas antes de v2.15), puedes reconstruirlos:

```python
# Reconstruir todas las relaciones
brain.build_backlinks()
# → {scanned: 50, backlinks_added: 120}

# Reconstruir para una página específica
brain.build_backlinks(slug='gpt-4o')
```

Esto escanea el body de cada página, extrae `[[wikilinks]]`, y actualiza `related_pages` en las páginas linkeadas.

---

## Flujo recomendado para el agente

```python
# 1. Ingerir fuente raw
brain.ingest_text(text=article, title="Paper X", source_url="...")

# 2. Crear páginas de conocimiento (sin page_type explícito)
brain.create_page(
    title="GPT-4o",
    body="## Overview\n[[OpenAI]] lanzó [[GPT-4o]] en mayo de 2024.\n\n## Capacidades\n- Visión\n- Audio\n\n## Comparación\nVs [[Claude 3.5 Sonnet]], GPT-4o es más rápido.\n\n^[mi-articulo-gpt4]",
    confidence='high',
    domain="investigacion",
    tags=["modelo", "multimodal"]
)
# → page_type='entity' (inferido)
# → related_pages: [openai, claude-3-5-sonnet]
# → auto-backlinks: openai.related_pages incluye esta página

# 3. Links rotos se detectan con lint()
report = brain.lint()
print(report['broken_links'])  # slugs que no existen aún
```

---

## Detección de links rotos

```python
report = brain.lint()
```

El reporte de `lint()` incluye:

| Campo | Qué detecta |
|-------|-------------|
| `broken_links` | `[[wikilinks]]` que apuntan a slugs que no existen en ninguna página |
| `orphans` | Páginas que no reciben `[[wikilinks]]` de ninguna otra página |

Corregir links rotos:

```python
# Opción 1: Crear la página faltante
brain.create_page(title="Attention", body="...")
# → el broken link ahora resuelve

# Opción 2: Actualizar el body si el slug es incorrecto
brain.update_page('mi-pagina', body=body_corregido)
```
