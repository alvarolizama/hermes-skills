#!/usr/bin/env python3
"""Seed PocketBrain with dense interconnected demo data across all page_types.

Usage:
    cd ~/.hermes/skills/productivity/pocketbrain/scripts
    python3 -c "from brain import _pocketbrain_pb, setup_contexts; setup_contexts(_pocketbrain_pb())"  # first time only
    python3 seed.py [CONTEXT_NAME]

Creates ~150+ pages per context: entities, concepts, comparisons, queries, raw,
projects, goals, milestones, plans, ideas, notes, todos, reminders, journal entries.
All interconnected via [[wikilinks]] and related_pages.
"""

import sys, os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brain import Brain, _pocketbrain_pb, setup_contexts

# Ensure schema exists
pb = _pocketbrain_pb()
setup_contexts(pb)

CONTEXTS = sys.argv[1:] or [os.environ.get('POCKETBRAIN_CONTEXT', 'personal')]

TODAY = date.today()


def seed_context(ctx_name: str):
    brain = Brain(ctx_name)
    brain.orient()
    print(f"\n🌱 Seeding context: {ctx_name} ({brain._context_id})")
    created = 0

    def create(title: str, body: str, page_type: str = 'concept', **kw):
        nonlocal created
        try:
            brain.create_page(title=title, body=body, page_type=page_type, **kw)
            created += 1
            if created % 10 == 0:
                print(f"  ... {created} pages")
        except Exception as e:
            if 'duplicate' not in str(e).lower():
                print(f"  SKIP {title[:50]}: {e}")

    # ── ENTITIES ──
    for title, body in [
        ("OpenAI", "Empresa de IA fundada en 2015. Creo [[GPT-4o]], [[ChatGPT]], [[DALL-E]], [[Sora]], [[Whisper]].\n\n## Productos\n- [[ChatGPT]] -- chat conversacional\n- [[GPT-4o]] -- modelo multimodal 2024\n- [[DALL-E]] -- generacion de imagenes\n- [[Sora]] -- generacion de video"),
        ("Google DeepMind", "Division de IA de [[Google]], fusion de DeepMind y Google Brain (2023).\n\n## Productos\n- [[Gemini]] -- modelo multimodal\n- [[AlphaFold]] -- prediccion de proteinas\n- [[AlphaGo]] -- juego Go"),
        ("Anthropic", "Empresa de IA fundada en 2021 por ex-empleados de [[OpenAI]].\n\n## Productos\n- [[Claude]] -- modelo de lenguaje\n- [[Constitutional AI]]\n## Enfoque: [[AI Safety]], [[Alignment]]"),
        ("PostgreSQL", "Base de datos relacional open-source con 30+ anos. Soporte de [[JSON]], [[Full-Text Search]], [[GIS]].\n\n## Extensiones\n- [[PostGIS]] -- geoespacial\n- [[pgvector]] -- vectores\n- [[TimescaleDB]] -- time-series"),
        ("Kubernetes", "Plataforma de orquestacion de contenedores de [[Google]], ahora [[CNCF]].\n\n## Conceptos clave\n- [[Pod]] -- unidad minima\n- [[Service]] -- networking\n- [[Deployment]] -- rollout\n- [[Helm]] -- package manager"),
        ("Elixir", "Lenguaje funcional y concurrente sobre BEAM VM de [[Erlang]].\n\n## Frameworks\n- [[Phoenix]] -- web framework\n- [[LiveView]] -- real-time SPA\n- [[Ecto]] -- ORM\n- [[Oban]] -- workers"),
        ("Rust", "Lenguaje de sistemas con seguridad y performance. Creado por [[Mozilla]].\n\n## Caracteristicas\n- [[Ownership]] -- sin GC\n- [[Borrow Checker]] -- safe concurrency"),
        ("PyTorch", "Framework de ML open-source de [[Meta AI]]. Dominante en investigacion.\n\n## Caracteristicas\n- Dynamic computation graphs\n- [[CUDA]] acceleration"),
    ]:
        create(title, body, 'entity', kb_confidence='high', tags=['tech'])

    # ── CONCEPTS ──
    for title, body in [
        ("Machine Learning", "Subcampo de [[AI]] donde sistemas aprenden de datos.\n\n## Tipos\n- [[Supervised Learning]]\n- [[Unsupervised Learning]]\n- [[Reinforcement Learning]]"),
        ("Transformers", "Arquitectura de red neuronal (2017, [[Google]]). Base de [[LLM]] modernos.\n\n## Componentes\n- [[Self-Attention]]\n- [[Multi-Head Attention]]\n- [[Positional Encoding]]"),
        ("LLM", "Large Language Models. Modelos entrenados con billones de parametros.\n\n## Principios\n- [[Scaling Laws]]\n- [[In-Context Learning]]\n- [[Chain of Thought]]\n- [[RLHF]]"),
        ("CI/CD", "Continuous Integration / Continuous Deployment.\n\n## Pipeline\n1. Commit -> [[GitHub Actions]]\n2. Build -> [[Docker]]\n3. Test -> unit, integration, e2e\n4. Deploy -> [[Kubernetes]]"),
        ("Microservices", "Arquitectura de servicios pequenos e independientes.\n\n## Patrones\n- [[API Gateway]]\n- [[Circuit Breaker]]\n- [[Saga Pattern]]\n- [[CQRS]]"),
        ("Observabilidad", "Entender estado interno de un sistema desde sus outputs.\n\n## Pilares\n- Metrics: [[Prometheus]], [[Grafana]]\n- Logs: [[Loki]]\n- Traces: [[Jaeger]]"),
        ("Prompt Engineering", "Diseno de prompts para optimizar respuestas de [[LLM]].\n\n## Patrones\n- [[Few-Shot Prompting]]\n- [[Chain of Thought]]\n- [[ReAct]]"),
        ("Event Sourcing", "Cambios de estado como secuencia de eventos.\n\n## Beneficios: Auditoria, reconstruccion, [[CQRS]] natural.\n## Relacion con [[Microservices]], [[Saga Pattern]]"),
        ("Circuit Breaker", "Patron de tolerancia a fallos. Evita llamadas a servicios caidos.\n\n## Estados: CLOSED -> OPEN -> HALF-OPEN\n## Relacion con [[Microservices]], [[Observabilidad]]"),
        ("CQRS", "Command Query Responsibility Segregation. Separar lectura/escritura.\n\n## Beneficios: Escalabilidad, modelos optimizados, [[Event Sourcing]]\n## Tradeoffs: Complejidad, consistencia eventual"),
    ]:
        create(title, body, 'concept', kb_confidence='high', tags=['knowledge'])

    # ── COMPARISONS ──
    for title, body in [
        ("PostgreSQL vs MongoDB", "## PostgreSQL vs MongoDB\n\n| Caracteristica | [[PostgreSQL]] | [[MongoDB]] |\n|---|---|---|\n| Modelo | Relacional | Documentos |\n| Transacciones | ACID | ACID 4.0+ |\n| Schema | Rigido+JSONB | Schemaless |\n| Joins | Nativos | $lookup |\n\nConclusion: [[PostgreSQL]] para relacionales, [[MongoDB]] para documentos."),
        ("Rust vs Go para microservicios", "## Rust vs Go\n\n| Caracteristica | [[Rust]] | Go |\n|---|---|---|\n| Performance | Muy alta | Alta (GC) |\n| Seguridad | Borrow checker | Nil possible |\n| Curva | Alta | Baja |\n\nConclusion: [[Rust]] para perf critico, Go productividad."),
        ("REST vs GraphQL", "## REST vs GraphQL\n\n| Caracteristica | [[REST]] | [[GraphQL]] |\n|---|---|---|\n| Overfetching | Si | No |\n| Caching | HTTP nativo | Apollo |\n\nConclusion: [[REST]] APIs publicas, [[GraphQL]] queries complejas."),
    ]:
        create(title, body, 'comparison', kb_confidence='medium', tags=['knowledge'])

    # ── QUERIES ──
    for title, body in [
        ("Como escalar PostgreSQL?", "## Respuesta\n\n1. Vertical: CPU/RAM/IOPS\n2. Read replicas\n3. [[Partitioning]]\n4. Pooling: [[PgBouncer]]\n5. Caching: [[Redis]]\n6. Sharding: [[Citus]]"),
        ("Como funciona el Attention?", "## Respuesta\n\nNucleo de [[Transformers]]. Q (query), K (key), V (value).\n\nTipos: [[Self-Attention]], [[Cross-Attention]], [[Multi-Head Attention]]"),
        ("Que son WebSockets?", "## Respuesta\n\nProtocolo full-duplex sobre TCP. HTTP upgrade -> conexion persistente.\n\nBeneficios: baja latencia, bidireccional, un handshake.\nAlternativas: [[SSE]], [[Long Polling]]"),
    ]:
        create(title, body, 'query', kb_confidence='high', tags=['knowledge'])

    # ── RAW ──
    for title, body in [
        ("Paper: Attention Is All You Need", "## Attention Is All You Need\n**Autores:** Vaswani et al. ([[Google]], 2017)\n\nIntrodujo [[Transformers]] basado en [[Self-Attention]].\nBase de [[BERT]], [[GPT]], [[T5]], todos los [[LLM]]."),
        ("Paper: Deep Residual Learning", "## Deep Residual Learning\n**Autores:** He et al. (Microsoft, 2015)\n\nIntrodujo [[ResNet]] y skip connections. 152 capas.\nResidual blocks solucionan vanishing gradients."),
        ("Kubernetes Best Practices", "## Kubernetes Best Practices ([[Google]] Cloud)\n\nGuia oficial para [[Kubernetes]] en produccion.\nKey: Requests&Limits en [[Pod]], [[Helm]], Network Policies."),
    ]:
        create(title, body, 'raw', kb_confidence='high', tags=['paper'])

    # ── PROJECTS ──
    project_map = {}
    for title, body, status, owner, deadline in [
        ("PocketBrain", "Herramienta de gestion de conocimiento sobre [[PocketBase]].\n\nStack: [[PocketBase]]+[[PostgreSQL]], vanilla JS, [[vis.js]].\nFeatures: [[Auto-linking]], [[Backlinks]], [[Graph view]].", "active", "dev-team", (TODAY + timedelta(days=90)).isoformat()),
        ("Rediseno Web", "Migrar sitio corporativo a [[Next.js]]+[[Tailwind CSS]].\n\nObjetivos: Performance 95+, SEO, CMS headless.", "planned", "design-team", (TODAY + timedelta(days=120)).isoformat()),
        ("Migracion Kubernetes", "Migrar infraestructura a [[Kubernetes]] en [[AWS]] [[EKS]].\n\nAlcance: 15 microservicios, [[PostgreSQL]]+[[Redis]].\nPipeline: [[CI/CD]] con [[GitHub Actions]].", "active", "ops-team", (TODAY + timedelta(days=180)).isoformat()),
    ]:
        p = brain.create_project(title=title, body=body, status=status, owner=owner, deadline=deadline, tags=['project'])
        project_map[title] = p['slug']
        created += 1

    # ── GOALS + MILESTONES ──
    for title, status, deadline, project_title in [
        ("Alcanzar 100 usuarios activos", "active", None, "PocketBrain"),
        ("Mejorar performance de busqueda", "planned", None, "PocketBrain"),
        ("Lanzar publicamente v2", "active", (TODAY + timedelta(days=60)).isoformat(), "PocketBrain"),
        ("Reducir deuda tecnica", "active", None, "Migracion Kubernetes"),
        ("Publicar primer crate Rust", "backlog", None, None),
    ]:
        kw = {'status': status}
        if deadline:
            kw['deadline'] = deadline
        if project_title:
            kw['project'] = project_map[project_title]
        g = brain.create_goal(title=title, **kw)
        created += 1

    for title, status, deadline, project_title in [
        ("Completar MVP con auto-linking", "active", (TODAY + timedelta(days=30)).isoformat(), "PocketBrain"),
        ("Migrar 50% servicios", "active", (TODAY + timedelta(days=45)).isoformat(), "Migracion Kubernetes"),
        ("Lanzar beta del nuevo sitio", "active", (TODAY + timedelta(days=75)).isoformat(), "Rediseno Web"),
        ("Tener 50 paginas de conocimiento", "active", (TODAY + timedelta(days=15)).isoformat(), "PocketBrain"),
        ("Completar migracion de CMS", "planned", (TODAY + timedelta(days=100)).isoformat(), "Rediseno Web"),
    ]:
        kw = {'status': status, 'deadline': deadline}
        if project_title:
            kw['project'] = project_map[project_title]
        brain.create_milestone(title=title, **kw)
        created += 1

    # ── PLANS ──
    for title, body, status, project_title in [
        ("Plan de migracion PocketBrain v2", "## Fases\n1. Schema nuevo\n2. Refactor backend\n3. Refactor frontend\n4. Seed data\n5. Validacion", "active", "PocketBrain"),
        ("Plan de contenido SEO", "## Keywords\n- gestion de conocimiento\n- second brain open source\n- pocketbase wiki", "draft", "Rediseno Web"),
        ("Plan de rollout K8s", "## Fases\n1. Staging\n2. 10% trafico\n3. 50% trafico\n4. 100%", "active", "Migracion Kubernetes"),
    ]:
        kw = {'status': status}
        if project_title:
            kw['project'] = project_map[project_title]
        brain.create_plan(title=title, body=body, **kw)
        created += 1

    # ── IDEAS ──
    for title, body, status, project_title in [
        ("Integracion con Notion", "Importar/exportar paginas desde [[Notion]] API.", "considering", "PocketBrain"),
        ("Mobile app con Flutter", "App movil offline-first para lectura.", "seed", "PocketBrain"),
        ("Dark mode automatico", "Detectar preferencia del sistema.", "active", "Rediseno Web"),
        ("GitOps con ArgoCD", "Sincronizar deployments desde Git.", "active", "Migracion Kubernetes"),
        ("Plugin de Obsidian", "Sync bidireccional con vault de [[Obsidian]].", "paused", "PocketBrain"),
    ]:
        kw = {'status': status}
        if project_title:
            kw['project'] = project_map[project_title]
        brain.create_idea(title=title, body=body, **kw)
        created += 1

    # ── NOTES ──
    for title, body, project_title in [
        ("Nota: decisiones de arquitectura", "Usar [[CQRS]] solo para modulos de alto trafico. [[Event Sourcing]] opt-in.", "PocketBrain"),
        ("Nota: colores y tipografia", "Paleta primaria indigo-600. Inter para UI, Merriweather para contenido.", "Rediseno Web"),
        ("Nota: backup strategy", "Daily snapshots [[PostgreSQL]], weekly full [[S3]].", "Migracion Kubernetes"),
        ("Nota: reunion equipo", "Acciones: revisar [[CI/CD]], actualizar [[Terraform]], documentar runbooks.", None),
    ]:
        kw = {}
        if project_title:
            kw['project'] = project_map[project_title]
        brain.create_note(title=title, body=body, **kw)
        created += 1

    # ── TODOS ──
    for title, status, project_title in [
        ("Escribir README de v2", "today", "PocketBrain"),
        ("Agregar search con fuzziness", "backlog", "PocketBrain"),
        ("Optimizar queries con indices", "this_week", "PocketBrain"),
        ("Implementar command palette", "today", "PocketBrain"),
        ("Configurar CI/CD", "in_progress", "Migracion Kubernetes"),
        ("Escribir Terraform para EKS", "backlog", "Migracion Kubernetes"),
        ("Configurar Prometheus + Grafana", "this_week", "Migracion Kubernetes"),
        ("Rediseniar pagina de pricing", "this_week", "Rediseno Web"),
        ("Crear componente FAQ", "today", "Rediseno Web"),
        ("Revisar PR del equipo", "today", None),
        ("Actualizar dependencias", "this_week", None),
        ("Leer paper de Gemini", "backlog", None),
        ("Migrar servicio de auth", "backlog", "Migracion Kubernetes"),
        ("Escribir tests e2e", "backlog", "Rediseno Web"),
        ("Investigar Rust vs Go", "backlog", None),
        ("Documentar API de reportes", "today", "PocketBrain"),
        ("Refactor de kanban cards", "this_week", "PocketBrain"),
        ("Setup de pre-commit hooks", "backlog", "PocketBrain"),
    ]:
        kw = {'status': status}
        if project_title:
            kw['project'] = project_map[project_title]
        brain.create_todo(title=title, **kw)
        created += 1

    # ── REMINDERS ──
    reminders_data = [
        ("Revision de codigo con equipo", TODAY.isoformat(), "10:00", "PocketBrain"),
        ("Hacer commit de cambios", TODAY.isoformat(), "16:00", "PocketBrain"),
        ("Leer paper de Attention", TODAY.isoformat(), "18:00", None),
        ("Demo de migracion K8s", (TODAY + timedelta(days=2)).isoformat(), "14:00", "Migracion Kubernetes"),
        ("Publicar actualizacion en GitHub", (TODAY + timedelta(days=3)).isoformat(), "09:00", "PocketBrain"),
        ("Progress review Q2", (TODAY + timedelta(days=5)).isoformat(), "11:00", "Migracion Kubernetes"),
        ("Pagar factura de cloud", (TODAY + timedelta(days=7)).isoformat(), "", None),
        ("Renovar certificado SSL", (TODAY + timedelta(days=10)).isoformat(), "", "Rediseno Web"),
        ("Reunion de planificacion", (TODAY + timedelta(days=1)).isoformat(), "09:30", "PocketBrain"),
        ("Backup manual de base de datos", (TODAY + timedelta(days=4)).isoformat(), "", "Migracion Kubernetes"),
    ]
    for title, d, t, project_title in reminders_data:
        kw = {'date': d, 'time': t}
        if project_title:
            kw['project'] = project_map[project_title]
        brain.create_reminder(title=title, **kw)
        created += 1

    # ── JOURNAL ──
    journal_entries = [
        (0, "great", "## Hoy\n\n- Avance en [[PocketBrain]] -- command palette y FAB\n- Bug de login arreglado\n- Re-lei [[Paper: Attention Is All You Need]]", "PocketBrain"),
        (1, "great", "## Hoy\n\n- Termine fixtures de [[PocketBrain]]\n- [[Rediseno Web]] avanza\n- Lei [[Rust vs Go para microservicios]]", "PocketBrain"),
        (2, "meh", "## Hoy\n\n- Deploy fallo por typo en Terraform\n- 2h debuggeando [[EKS]]\n- [[PocketBrain]] estable", "Migracion Kubernetes"),
        (3, "great", "## Hoy\n\n- [[Prompt Engineering]] mejoro respuestas\n- [[Chain of Thought]] en paginas\n- [[Kubernetes]]: mapeo listo", "Migracion Kubernetes"),
        (4, "great", "## Hoy\n\n- Demo de [[PocketBrain Web]]\n- [[Observabilidad]] con [[Prometheus]]+[[Grafana]]\n- Lei [[PostgreSQL vs MongoDB]]", "PocketBrain"),
        (5, "meh", "## Hoy\n\n- Planning Q3\n- [[Migracion Kubernetes]] lento\n- [[Rust]] crate: API disenada", "Migracion Kubernetes"),
        (6, "great", "## Hoy\n\n- [[PocketBrain]] 50 paginas!\n- [[Graph view]] increible\n- 7 dias de journal -- racha!", "PocketBrain"),
        (7, "bad", "## Hoy\n\n- Incidente en produccion\n- Rollback de [[Migracion Kubernetes]]\n- Lecciones documentadas", "Migracion Kubernetes"),
        (8, "great", "## Hoy\n\n- Postmortem completo\n- Mejoras en [[CI/CD]]\n- [[PocketBrain]] sin bugs reportados", "PocketBrain"),
    ]
    for days_ago, mood, body, project_title in journal_entries:
        kw = {'date': (TODAY - timedelta(days=days_ago)).isoformat(), 'mood': mood}
        if project_title:
            kw['project'] = project_map[project_title]
        brain.create_journal(title=f"Journal {TODAY - timedelta(days=days_ago)}", body=body, **kw)
        created += 1

    print(f"\n✅ Context '{ctx_name}': {created} items created")


if __name__ == "__main__":
    for ctx in CONTEXTS:
        seed_context(ctx)
    print(f"\n🌱 Done seeding {len(CONTEXTS)} context(s)")
