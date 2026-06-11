# PocketBrain vs LLM Wiki (Karpathy Pattern)

Mapeo completo de capacidades entre PocketBrain y el patrón [LLM Wiki de Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Arquitectura (3 Layers)

| Layer | LLM Wiki | PocketBrain | Estado |
|-------|----------|-------------|--------|
| **Layer 1 — Raw sources** | `raw/` con artículos, papers, transcripts. Frontmatter: `source_url`, `ingested`, `sha256` | `brain_pages` con `page_type='raw'` + campos `source_url`, `source_sha256`. `ingest_text()` y `ingest_file()` lo manejan automáticamente | ✅ Implementado |
| **Layer 2 — Wiki pages** | Archivos markdown en `entities/`, `concepts/`, `comparisons/`, `queries/` | `brain_pages` con `page_type='entity'|'concept'|'comparison'|'query'|'project'|'raw'`. `[[wikilinks]]` nativos | ✅ Implementado |
| **Layer 3 — Schema** | `SCHEMA.md` + `index.md` + `log.md` | `schema_config` en colección `contexts` + `brain_log` para trazabilidad + `index()` method | ⚠️ Schema existe como JSON, no como documento markdown |

## Calidad de la información

| Feature | LLM Wiki | PocketBrain | Estado |
|---------|----------|-------------|--------|
| **Confidence** | `confidence: high\|medium\|low` en frontmatter | ✅ `brain_pages.confidence` (select field) + badges en UI | ✅ |
| **Contested** | `contested: true` en frontmatter | ✅ `brain_pages.contested` (bool) + `⚠ Sí` en sidebar metadata | ✅ |
| **Contradictions** | `contradictions: [page-slug]` | ✅ `brain_pages.contradictions` (text) + se muestra en sidebar | ✅ |
| **Provenance markers** | `^[raw/articles/source.md]` en párrafos | ✅ Markdown renderer convierte `^[slug]` en superscript citations | ✅ |
| **Source SHA256** | `sha256:` en raw frontmatter | ✅ `brain_pages.source_sha256` — se calcula automáticamente en `ingest_text()`/`ingest_file()` | ✅ |
| **Source drift detection** | Re-calcular SHA256 y comparar | ✅ `detect_drift()` en lint | ✅ v2.14.0 |
| **Confidence badges en UI** | N/A (archivos markdown) | ✅ Badges verde/amarillo/rojo en índice wiki | ✅ v2.14.0 |

## Operaciones Core

| Operación | LLM Wiki | PocketBrain | Estado |
|-----------|----------|-------------|--------|
| **Ingest raw source** | `raw/` + frontmatter + sha256 | ✅ `ingest_text()`, `ingest_file()` con SHA256 automático | ✅ |
| **Search** | `search_files` en markdown | ✅ `search()` con ranking case-insensitive, filtros por tipo/tag/dominio | ✅ |
| **Query → file answer** | Crear página en `queries/` | ✅ `create_page()` con `page_type='query'` | ✅ |
| **Lint** | 11 checks: orphans, broken links, frontmatter, stale, contradictions, quality, source drift, page size, tags, log rotation | ✅ `lint()` con orphans, broken links, low confidence, contested, oversized, invalid tags, drift, frontmatter validation | ✅ v2.14.0 |
| **Index** | `index.md` generado manualmente | ✅ `index()` method + vista de Índice en web UI con tabs por tipo | ✅ |
| **Archive old** | Mover a `_archive/` | ✅ `archive_old(days=90, dry_run=True)` | ✅ v2.14.0 |
| **Log rotation** | Renombrar `log.md` a `log-YYYY.md` | ✅ `rotate_log(max_entries=500)` — archiva en página raw | ✅ v2.14.0 |

## Características exclusivas de PocketBrain

| Feature | Descripción |
|---------|-------------|
| **Multi-contexto** | KBs independientes (personal, projects, bravo, learning, health) |
| **Web UI completa** | Sidebar, tabs, kanban, graph vis.js, responsive mobile |
| **Goals/Milestones/OKRs** | Gestión estructurada de metas con estado (planned→active→done→cancelled) |
| **Kanban de tareas** | backlog → this week → today → in progress → done → cancelled |
| **Recordatorios** | Con fecha/hora, filtros por hoy/semana/futuro |
| **Journal** | Entrada por día con mood y tags |
| **File attachments** | Subida de archivos por página |
| **Page versioning** | Historial de cambios via `brain_page_versions` |
| **Trazabilidad** | `brain_log` registra quién (agente) y para quién (usuario) |
| **Proyectos** | Pages con type project + goals + todos + reminders + deliverables + graph |
| **Sync a markdown** | Export a archivos markdown via `sync.py` |
| **Grafo de conocimiento** | Visualización de nodos y relaciones via vis.js |

## Características de LLM Wiki no cubiertas

| Feature | Por qué no aplica |
|---------|-------------------|
| **Obsidian vault** | PocketBrain es PocketBase, no archivos markdown. Pero `sync.py` exporta a markdown compatible |
| **SCHEMA.md como documento** | El schema vive como JSON en la colección `contexts`. Se puede ver con `brain.get_schema()` |
| **Tag taxonomy enforcement estricto** | `lint()` ya lo valida contra la taxonomía en schema_config |

## Resumen

PocketBrain cubre **~95% del patrón LLM Wiki** a nivel funcional, y lo **supera** en capacidades operacionales (todos, goals, reminders, journal, graph, trazabilidad). Lo que LLM Wiki tiene como archivos markdown, PocketBrain lo tiene como registros en PocketBase con una UI web encima.

La diferencia fundamental: LLM Wiki es **knowledge-only** con rigor científico; PocketBrain es **knowledge + operations** con ejecución de proyectos.
