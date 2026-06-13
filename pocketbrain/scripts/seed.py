#!/usr/bin/env python3
"""Seed PocketBrain with dense interconnected data across all page_types.

Usage:
    cd ~/.hermes/skills/productivity/pocketbrain/scripts
    python3 -c "from brain import _pocketbrain_pb, setup_contexts; setup_contexts(_pocketbrain_pb())"  # first time only
    python3 seed.py

Creates ~72 pages: 10 entities, 10 concepts, 4 comparisons, 3 queries, 4 raw,
3 projects, 5 goals, 5 milestones, 15 todos, 8 reminders, 7 journal entries.
All interconnected via [[wikilinks]].
"""

import sys, os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brain import Brain, _pocketbrain_pb, setup_contexts

# Ensure schema exists
pb = _pocketbrain_pb()
setup_contexts(pb)

brain = Brain(os.environ.get('POCKETBRAIN_CONTEXT', 'personal'))
brain.orient()
print(f"Context: {brain.context_name} ({brain._context_id})")

created = 0

def create(title, body, page_type='concept', **kw):
    global created
    try:
        brain.create_page(title=title, body=body, page_type=page_type, **kw)
        created += 1
        if created % 5 == 0:
            print(f"  ... {created} pages")
    except Exception as e:
        if 'duplicate' not in str(e).lower():
            print(f"  SKIP {title[:50]}: {e}")

# ── ENTITIES ──
entities = [
    ("OpenAI", "Empresa de IA fundada en 2015. Creo [[GPT-4o]], [[ChatGPT]], [[DALL-E]], [[Sora]], [[Whisper]].\n\n## Productos\n- [[ChatGPT]] -- chat conversacional\n- [[GPT-4o]] -- modelo multimodal 2024\n- [[DALL-E]] -- generacion de imagenes\n- [[Sora]] -- generacion de video\n## Partnership\n- [[Microsoft]]"),
    ("Google DeepMind", "Division de IA de [[Google]], fusion de DeepMind y Google Brain (2023).\n\n## Productos\n- [[Gemini]] -- modelo multimodal\n- [[AlphaFold]] -- prediccion de proteinas\n- [[AlphaGo]] -- juego Go\n## Research\n- [[Reinforcement Learning]]\n- [[Transformers]]"),
    ("Anthropic", "Empresa de IA fundada en 2021 por ex-empleados de [[OpenAI]].\n\n## Productos\n- [[Claude]] -- modelo de lenguaje\n- [[Claude 3.5 Sonnet]] -- modelo 2024\n- [[Constitutional AI]]\n## Enfoque: [[AI Safety]], [[Alignment]]"),
    ("AWS", "Amazon Web Services. Plataforma cloud lider con ~33% market share.\n\n## Servicios\n- [[EC2]] -- computo\n- [[S3]] -- almacenamiento\n- [[Lambda]] -- serverless\n- [[RDS]]/[[Aurora]] -- bases de datos\n- [[DynamoDB]] -- NoSQL\n- [[EKS]] -- Kubernetes gestionado\n## Competidores: [[Azure]], [[GCP]]"),
    ("Kubernetes", "Plataforma de orquestacion de contenedores de [[Google]], ahora [[CNCF]].\n\n## Conceptos clave\n- [[Pod]] -- unidad minima\n- [[Service]] -- networking\n- [[Deployment]] -- rollout\n- [[Helm]] -- package manager\n- [[Ingress]] -- trafico externo\n## Distribuciones: [[EKS]], [[GKE]], [[AKS]], [[K3s]]"),
    ("Elixir", "Lenguaje funcional y concurrente sobre BEAM VM de [[Erlang]].\n\n## Frameworks\n- [[Phoenix]] -- web framework\n- [[LiveView]] -- real-time SPA\n- [[Ecto]] -- ORM\n- [[Oban]] -- workers\n## Ecosistema: [[Hex]], [[Mix]], [[OTP]]"),
    ("PostgreSQL", "Base de datos relacional open-source con 30+ anos. Soporte de [[JSON]], [[Full-Text Search]], [[GIS]].\n\n## Extensiones\n- [[PostGIS]] -- geoespacial\n- [[pgvector]] -- vectores\n- [[TimescaleDB]] -- time-series\n## Caracteristicas: [[MVCC]], [[WAL]], [[Partitioning]]\n## Competidores: [[MySQL]], [[SQLite]], [[MongoDB]], [[DynamoDB]]"),
    ("Rust", "Lenguaje de sistemas con seguridad y performance. Creado por [[Mozilla]].\n\n## Caracteristicas\n- [[Ownership]] -- sin GC\n- [[Borrow Checker]] -- safe concurrency\n## Ecosistema: [[Cargo]], [[Tokio]], [[Actix]], [[Axum]], [[Serde]]\n## Adopcion: [[Linux kernel]], [[AWS]], [[Discord]]"),
    ("Phoenix Framework", "Web framework para [[Elixir]]. Real-time sin JS con [[LiveView]].\n\n## Componentes\n- [[LiveView]] -- server-rendered real-time\n- [[Ecto]] -- capa de datos\n- [[Channels]] -- WebSockets\n- [[PubSub]] -- mensajeria"),
    ("PyTorch", "Framework de ML open-source de [[Meta AI]]. Dominante en investigacion.\n\n## Caracteristicas\n- Dynamic computation graphs\n- [[CUDA]] acceleration\n- TorchScript para produccion\n## Ecosistema: [[torchvision]], [[Hugging Face]]"),
]
for title, body in entities:
    create(title, body, 'entity', confidence='high')

# ── CONCEPTS ──
concepts = [
    ("Machine Learning", "Subcampo de [[AI]] donde sistemas aprenden de datos.\n\n## Tipos\n- [[Supervised Learning]]\n- [[Unsupervised Learning]]\n- [[Reinforcement Learning]]\n## Frameworks: [[PyTorch]], [[Scikit-learn]]\n## Algoritmos: [[Linear Regression]], [[Decision Trees]], [[Random Forest]], [[Gradient Boosting]]"),
    ("Transformers", "Arquitectura de red neuronal (2017, [[Google]]). Base de [[LLM]] modernos.\n\n## Componentes\n- [[Self-Attention]]\n- [[Multi-Head Attention]]\n- [[Positional Encoding]]\n## Modelos basados: [[BERT]], [[GPT]], [[T5]], [[Vision Transformer]]"),
    ("LLM", "Large Language Models. Modelos entrenados con billones de parametros.\n\n## Principios\n- [[Scaling Laws]]\n- [[In-Context Learning]]\n- [[Chain of Thought]]\n- [[RLHF]]\n## Modelos: [[GPT-4o]], [[Claude 3.5 Sonnet]], [[Gemini]], [[Llama 3]]"),
    ("CI/CD", "Continuous Integration / Continuous Deployment.\n\n## Pipeline\n1. Commit -> [[GitHub Actions]]\n2. Build -> [[Docker]]\n3. Test -> unit, integration, e2e\n4. Deploy -> [[Kubernetes]]/[[ECS]]\n## Herramientas: [[ArgoCD]], [[Terraform]], [[Helm]]"),
    ("Microservices", "Arquitectura de servicios pequenos e independientes.\n\n## Patrones\n- [[API Gateway]]\n- [[Circuit Breaker]]\n- [[Saga Pattern]]\n- [[CQRS]]\n- [[Event Sourcing]]\n## Comunicacion: [[REST]], [[GraphQL]], [[gRPC]], [[Kafka]]"),
    ("Observabilidad", "Entender estado interno de un sistema desde sus outputs.\n\n## Pilares\n- Metrics: [[Prometheus]], [[Grafana]]\n- Logs: [[Loki]], [[ELK]]\n- Traces: [[Jaeger]], [[Tempo]]\n## Enfoques: [[RED Method]], [[USE Method]]"),
    ("Prompt Engineering", "Diseno de prompts para optimizar respuestas de [[LLM]].\n\n## Patrones\n- [[Few-Shot Prompting]]\n- [[Chain of Thought]]\n- [[ReAct]]\n## Mejores practicas: especifico, contextual, iterar"),
    ("Event Sourcing", "Cambios de estado como secuencia de eventos.\n\n## Beneficios: Auditoria, reconstruccion, [[CQRS]] natural.\n## Implementaciones: [[Kafka]], EventStoreDB\n## Relacion con [[Microservices]], [[Saga Pattern]]"),
    ("Circuit Breaker", "Patron de tolerancia a fallos. Evita llamadas a servicios caidos.\n\n## Estados: CLOSED -> OPEN -> HALF-OPEN\n## Implementaciones: [[Hystrix]], [[Resilience4j]]\n## Relacion con [[Microservices]], [[Observabilidad]]"),
    ("CQRS", "Command Query Responsibility Segregation. Separar lectura/escritura.\n\n## Beneficios: Escalabilidad, modelos optimizados, [[Event Sourcing]]\n## Tradeoffs: Complejidad, consistencia eventual"),
]
for title, body in concepts:
    create(title, body, 'concept', confidence='high')

# ── COMPARISONS ──
comparisons = [
    ("PostgreSQL vs MongoDB", "## PostgreSQL vs MongoDB\n\n| Caracteristica | [[PostgreSQL]] | [[MongoDB]] |\n|---|---|---|\n| Modelo | Relacional | Documentos |\n| Transacciones | ACID | ACID 4.0+ |\n| Schema | Rigido+JSONB | Schemaless |\n| Joins | Nativos | $lookup |\n| Escalabilidad | Vertical+replicas | Horizontal nativo |\n\nConclusion: [[PostgreSQL]] para relacionales, [[MongoDB]] para documentos."),
    ("Rust vs Go para microservicios", "## Rust vs Go\n\n| Caracteristica | [[Rust]] | Go |\n|---|---|---|\n| Performance | Muy alta | Alta (GC) |\n| Seguridad | Borrow checker | Nil possible |\n| Curva | Alta | Baja |\n| Concurrency | Async+threads | Goroutines |\n\nConclusion: [[Rust]] para perf critico, Go productividad."),
    ("REST vs GraphQL", "## REST vs GraphQL\n\n| Caracteristica | [[REST]] | [[GraphQL]] |\n|---|---|---|\n| Overfetching | Si | No |\n| Caching | HTTP nativo | Apollo |\n| Tooling | Swagger | GraphiQL |\n\nConclusion: [[REST]] APIs publicas, [[GraphQL]] queries complejas."),
    ("Docker vs Podman", "## Docker vs Podman\n\n| Caracteristica | [[Docker]] | Podman |\n|---|---|---|\n| Daemon | dockerd | No |\n| Rootless | Config | Nativo |\n| K8s | Nativo | Pod YAML |\n\nConclusion: Podman mas seguro, [[Docker]] mas compatible."),
]
for title, body in comparisons:
    create(title, body, 'comparison', confidence='medium')

# ── QUERIES ──
queries = [
    ("Como escalar PostgreSQL?", "## Respuesta\n\n1. Vertical: CPU/RAM/IOPS\n2. Read replicas\n3. [[Partitioning]] (PG 12+)\n4. Pooling: [[PgBouncer]]\n5. Caching: [[Redis]]/Materialized Views\n6. Sharding: [[Citus]]\n\nMonitoreo: [[pg_stat_statements]], [[Prometheus]]+[[Grafana]]"),
    ("Como funciona el Attention?", "## Respuesta\n\nNucleo de [[Transformers]]. Q (query), K (key), V (value).\nScore = softmax(Q*K^T / sqrt(d_k)). Output = score * V.\n\nTipos: [[Self-Attention]], [[Cross-Attention]], [[Multi-Head Attention]]\nPaper: [[Paper: Attention Is All You Need]]"),
    ("Que son WebSockets?", "## Respuesta\n\nProtocolo full-duplex sobre TCP. HTTP upgrade -> conexion persistente.\n\nBeneficios: baja latencia, bidireccional, un handshake.\nAlternativas: [[SSE]], [[Long Polling]], [[WebRTC]]\nFrameworks: [[Phoenix Channels]], Socket.io"),
]
for title, body in queries:
    create(title, body, 'query', confidence='high')

# ── RAW ──
raws = [
    ("Paper: Attention Is All You Need", "## Attention Is All You Need\n**Autores:** Vaswani et al. ([[Google]], 2017)\n\nIntrodujo [[Transformers]] basado en [[Self-Attention]].\nEncoder: 6 capas [[Multi-Head Attention]]+FFN. Decoder: 6 capas.\nBase de [[BERT]], [[GPT]], [[T5]], todos los [[LLM]]."),
    ("Paper: Deep Residual Learning", "## Deep Residual Learning\n**Autores:** He et al. (Microsoft, 2015)\n\nIntrodujo [[ResNet]] y skip connections. 152 capas.\nResidual blocks solucionan vanishing gradients.\nBase de [[Computer Vision]] moderno."),
    ("Video: Microservices Patterns", "## Mastering Chaos - Netflix Microservices\n**Autor:** Josh Evans ([[Netflix]])\n\nExperiencia de [[Netflix]] migrando a [[Microservices]].\nLecciones: [[Circuit Breaker]] con [[Hystrix]], [[Chaos Engineering]], Service Discovery."),
    ("Articulo: Kubernetes Best Practices", "## Kubernetes Best Practices (Google Cloud)\n\nGuia oficial de [[Google]] para [[Kubernetes]] en produccion.\nKey: Requests&Limits en [[Pod]], [[Helm]], Network Policies, [[RBAC]]."),
]
for title, body in raws:
    create(title, body, 'raw', confidence='high')

# ── PROJECTS ──
create("PocketBrain", "Herramienta de gestion de conocimiento sobre [[PocketBase]].\n\nStack: [[PocketBase]]+[[PostgreSQL]], vanilla JS/PocketPages, [[vis.js]].\nFeatures: [[Auto-linking]], [[Backlinks]], [[Graph view]], [[Command Palette]].\nHosting: zima.vpn.cloud", 'project')
create("Rediseno de Sitio Web", "Rediseno del sitio corporativo. Migrar de [[WordPress]] a [[Next.js]]+[[Tailwind CSS]].\n\nObjetivos: Performance 95+, SEO, CMS [[Strapi]].\nTimeline: Q3 2026", 'project')
create("Migracion a Kubernetes", "Migrar infraestructura a [[Kubernetes]] en [[AWS]] [[EKS]].\n\nAlcance: 15 microservicios, [[PostgreSQL]]+[[Redis]].\nPipeline: [[CI/CD]] con [[GitHub Actions]]+[[ArgoCD]].\nObservabilidad: [[Prometheus]]+[[Grafana]]+[[Jaeger]]", 'project')

# ── GOALS + MILESTONES ──
for title, gtype, status, slug in [
    ("Alcanzar 100 usuarios activos de PocketBrain", 'goal', 'active', 'pocketbrain'),
    ("Mejorar performance de busqueda a <100ms", 'goal', 'planned', 'pocketbrain'),
    ("Lanzar publicamente PocketBrain v2", 'goal', 'active', 'pocketbrain'),
    ("Reducir deuda tecnica", 'goal', 'active', 'migracion-a-kubernetes'),
    ("Publicar primer crate Rust en crates.io", 'goal', 'backlog', ''),
]:
    brain.create_goal(title, type=gtype, status=status, project_slug=slug if slug else None)

for title, status, deadline, slug in [
    ("Completar MVP PocketBrain v2 con auto-linking", 'active', '2026-09-30', 'pocketbrain'),
    ("Migrar 50% servicios a K8s", 'active', '2026-09-15', 'migracion-a-kubernetes'),
    ("Lanzar beta del nuevo sitio web", 'active', '2026-10-01', 'rediseno-de-sitio-web'),
    ("Tener 50 paginas de conocimiento en PocketBrain", 'active', '2026-07-15', 'pocketbrain'),
    ("Completar migracion de WordPress a Next.js", 'planned', '2026-11-30', 'rediseno-de-sitio-web'),
]:
    brain.create_goal(title, type='milestone', status=status, deadline=deadline, project_slug=slug if slug else None)

# ── TODOS ──
for title, status, slug in [
    ("Escribir README de PocketBrain v2", "today", "pocketbrain"),
    ("Agregar search con fuzziness a PocketBrain", "backlog", "pocketbrain"),
    ("Optimizar queries de PocketBase con indices", "this week", "pocketbrain"),
    ("Implementar command palette en PocketBrain Web", "today", "pocketbrain"),
    ("Configurar CI/CD con GitHub Actions", "in progress", "migracion-a-kubernetes"),
    ("Escribir Terraform para EKS en AWS", "backlog", "migracion-a-kubernetes"),
    ("Configurar Prometheus + Grafana para K8s", "this week", "migracion-a-kubernetes"),
    ("Redisenar pagina de pricing", "this week", "rediseno-de-sitio-web"),
    ("Crear componente de FAQ en Next.js", "today", "rediseno-de-sitio-web"),
    ("Revisar PR #42 del equipo", "today", ""),
    ("Actualizar dependencias (Dependabot)", "this week", ""),
    ("Leer paper de Gemini para entender arquitectura", "backlog", ""),
    ("Migrar servicio de auth a K8s", "backlog", "migracion-a-kubernetes"),
    ("Escribir tests e2e para landing page", "backlog", "rediseno-de-sitio-web"),
    ("Investigar Rust vs Go para proximo microservicio", "backlog", ""),
]:
    brain.create_todo(title, status=status, page_slug=slug if slug else None)

# ── REMINDERS ──
today = date.today()
for i, (title, d, t) in enumerate([
    ("Reunion revision de codigo con equipo Bravo", today.isoformat(), "10:00"),
    ("Hacer commit de los cambios de PocketBrain", today.isoformat(), "16:00"),
    ("Leer paper de Attention para Transformers", today.isoformat(), "18:00"),
    ("Demo de migracion K8s con stakeholders", (today+timedelta(days=2)).isoformat(), "14:00"),
    ("Publicar actualizacion en GitHub", (today+timedelta(days=3)).isoformat(), "09:00"),
    ("Revisar progress review Bravo Q2", (today+timedelta(days=5)).isoformat(), "11:00"),
    ("Pagar factura de AWS mensual", (today+timedelta(days=7)).isoformat(), ""),
    ("Renovar certificado SSL de zima.vpn.cloud", (today+timedelta(days=10)).isoformat(), ""),
]):
    slugs = ['migracion-a-kubernetes', 'pocketbrain', 'pocketbrain', 'migracion-a-kubernetes', 'pocketbrain', 'migracion-a-kubernetes', '', '']
    brain.create_reminder(title, date=d, time=t, page_slug=slugs[i] if slugs[i] else None)

# ── JOURNAL ──
for days_ago, mood, body, page_slug in [
    (0, "great", "## Hoy\n\n- Avance en [[PocketBrain]] -- implemente command palette y FAB\n- Bug de login arreglado\n- Re-lei [[Paper: Attention Is All You Need]]", "pocketbrain"),
    (1, "great", "## Hoy\n\n- Termine fixtures de [[PocketBrain]]\n- [[Rediseno de Sitio Web]] avanza\n- Lei [[Rust vs Go para microservicios]]\n- [[Microservices]] clave para [[Migracion a Kubernetes]]", "pocketbrain"),
    (2, "meh", "## Hoy\n\n- Deploy fallo por typo en [[Terraform]]\n- 2h debuggeando [[EKS]]\n- [[PocketBrain]] estable en zima", "migracion-a-kubernetes"),
    (3, "great", "## Hoy\n\n- [[Prompt Engineering]] mejoro respuestas\n- [[Chain of Thought]] en paginas\n- [[Kubernetes]]: mapeo listo", "migracion-a-kubernetes"),
    (4, "great", "## Hoy\n\n- Demo de [[PocketBrain Web]]\n- [[Observabilidad]] con [[Prometheus]]+[[Grafana]]\n- Lei [[PostgreSQL vs MongoDB]]", "pocketbrain"),
    (5, "meh", "## Hoy\n\n- Planning Q3\n- [[Migracion a Kubernetes]] lento\n- [[Rust]] crate: API disenada pero no compila", "migracion-a-kubernetes"),
    (6, "great", "## Hoy\n\n- [[PocketBrain]] 50 paginas!\n- [[Graph view]] increible\n- 7 dias de journal -- racha!", "pocketbrain"),
]:
    brain.journal_write(body, date_val=today-timedelta(days=days_ago), mood=mood)
    if page_slug:
        # Append will update; we need to also link the journal page to project via related_pages
        entry = brain.journal(today-timedelta(days=days_ago))
        if entry and 'id' in entry:
            project = brain._get_page(page_slug)
            if project and 'id' in project:
                current = entry.get('related_pages') or []
                if isinstance(current, str):
                    current = [current] if current else []
                if project['id'] not in current:
                    brain.update_page(entry['slug'], related_slugs=[page_slug])

created += 5 + 5 + 15 + 8 + 7  # count goals, milestones, todos, reminders, journal
print(f"\nDone! Created {created} items in context '{brain.context_name}'")
print(f"  Entities: 10  Concepts: 10  Comparisons: 4  Queries: 3  Raw: 4  Projects: 3")
print(f"  Goals: 5  Milestones: 5  Todos: 15  Reminders: 8  Journal: 7")
