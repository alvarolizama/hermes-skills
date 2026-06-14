"""
PocketBrain — Multi-brain knowledge base on PocketBase.
=======================================================

Depends on pocketbase skill's pb.py module.

Usage:
    from brain import Brain, setup_contexts
    
    # First time: create the collections
    pb = quick_pb()
    setup_contexts(pb)
    
    # Connect to a brain
    brain = Brain('personal')
    brain.orient()
    
    # Operations
    brain.create_note(title='My Note', body='Content here...')
    results = brain.search('transformer')
    report = brain.lint()
"""

import sys, os, json, hashlib, re, unicodedata
from datetime import datetime, timezone
from typing import Optional, Any

# Import from pocketbase skill
sys.path.insert(0, os.path.expanduser('~/.hermes/skills/productivity/pocketbase/scripts'))
from pb import PB, quick_pb

# ── PocketBrain env loader ──────────────────────────────────────────

def _load_pocketbrain_env():
    """Carga POCKETHOST_HOST, POCKETHOST_EMAIL, POCKETHOST_PASSWORD, POCKETBRAIN_CONTEXT del .env y los setea en os.environ."""
    env = {}
    env_path = os.path.expanduser('~/.hermes/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    val = v.strip().strip('"').strip("'")
                    env[k.strip()] = val
                    # Propagar a os.environ para que esté disponible globalmente
                    if k.strip().startswith('POCKETHOST_') or k.strip().startswith('POCKETBRAIN_'):
                        os.environ[k.strip()] = val
    return env

def _pocketbrain_pb():
    """Crea un PB autenticado usando POCKETHOST_* del .env."""
    env = _load_pocketbrain_env()
    host = env.get('POCKETHOST_HOST', env.get('POCKETBRAIN_HOST', 'http://localhost:8090'))
    email = env.get('POCKETHOST_EMAIL', env.get('POCKETBRAIN_EMAIL', ''))
    password = env.get('POCKETHOST_PASSWORD', env.get('POCKETBRAIN_PASSWORD', ''))
    return quick_pb(host, email, password)


# ═════════════════════════════════════════════════════════════════════
#  SCHEMA
# ═════════════════════════════════════════════════════════════════════

BRAIN_SCHEMA = {
    "brain_contexts": {
        "name": "brain_contexts",
        "type": "base",
        "fields": [
            {"name": "name", "type": "text", "required": True, "unique": True},
            {"name": "label", "type": "text"},
            {"name": "description", "type": "text"},
            {"name": "schema_config", "type": "json"},
        ],
    },
    "brain_tags": {
        "name": "brain_tags",
        "type": "base",
        "fields": [
            {"name": "name", "type": "text", "required": True},
            {"name": "category", "type": "text"},
            {"name": "context", "type": "relation", "collectionId": "brain_contexts",
             "cascadeDelete": False, "maxSelect": 1},
        ],
    },
    "brain_pages": {
        "name": "brain_pages",
        "type": "base",
        "fields": [
            # ── Core ─────────────────────────────────────────────
            {"name": "title", "type": "text", "required": True},
            {"name": "slug", "type": "text", "required": True, "unique": True},
            {"name": "context", "type": "relation", "collectionId": "brain_contexts",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "page_type", "type": "select", "required": True,
             "values": ["entity", "concept", "comparison", "query", "raw",
                        "project", "plan", "note", "idea", "todo",
                        "goal", "milestone", "reminder", "journal", "file"],
             "maxSelect": 1},
            {"name": "body", "type": "text"},
            {"name": "summary", "type": "text"},
            {"name": "tags", "type": "relation", "collectionId": "brain_tags",
             "cascadeDelete": False, "maxSelect": None},
            {"name": "related_pages", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": None},
            {"name": "archived", "type": "bool"},

            # ── Knowledge (entity, concept, comparison, query, raw) ──
            {"name": "kb_confidence", "type": "select",
             "values": ["high", "medium", "low"], "maxSelect": 1, "required": False},
            {"name": "kb_contested", "type": "bool"},
            {"name": "kb_contradictions", "type": "text"},
            {"name": "kb_source_url", "type": "url"},
            {"name": "kb_source_sha256", "type": "text"},

            # ── Shared fields (used by multiple page types) ─────
            {"name": "status", "type": "select",
             "values": ["planned", "active", "on_hold", "completed", "cancelled",
                        "draft", "seed", "considering", "paused", "dropped", "done",
                        "backlog", "this_week", "today", "in_progress"],
             "maxSelect": 1, "required": False},
            {"name": "owner", "type": "text"},
            {"name": "deadline", "type": "date"},
            {"name": "date", "type": "date"},
            {"name": "time", "type": "text"},
            {"name": "done", "type": "bool"},
            {"name": "done_date", "type": "date"},
            {"name": "mood", "type": "text"},
            {"name": "project", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},

            # ── Todo ───────────────────────────────────────────────
            {"name": "todo_goal", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},

            # ── File ────────────────────────────────────────────────
            {"name": "file_type", "type": "text"},
            {"name": "file_version", "type": "text"},
            {"name": "file_attachment", "type": "file", "maxSelect": 1, "maxSize": 0},
        ],
    },
    "brain_page_versions": {
        "name": "brain_page_versions",
        "type": "base",
        "fields": [
            {"name": "page", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "version", "type": "number", "required": True},
            {"name": "title", "type": "text"},
            {"name": "body", "type": "text"},
            {"name": "summary", "type": "text"},
            {"name": "change_summary", "type": "text"},
            {"name": "page_type", "type": "text"},
        ],
    },
    "brain_log": {
        "name": "brain_log",
        "type": "base",
        "fields": [
            {"name": "context", "type": "relation", "collectionId": "brain_contexts",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "action", "type": "select", "required": True,
             "values": ["ingest", "update", "query", "lint", "create", "archive", "delete", "setup"],
             "maxSelect": 1},
            {"name": "page", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "description", "type": "text"},
            {"name": "details", "type": "json"},
        ],
    },
}

CREATION_ORDER = ["brain_contexts", "brain_tags", "brain_pages", "brain_log", "brain_page_versions"]

# Colecciones con campos self-reference o cross-reference que necesitan PATCH post-creación
SELF_REF_FIELDS = {
    "brain_pages": [
        {"name": "related_pages", "type": "relation", "collectionId": "brain_pages",
         "cascadeDelete": False, "maxSelect": None},
        {"name": "project", "type": "relation", "collectionId": "brain_pages",
         "cascadeDelete": False, "maxSelect": 1},
        {"name": "todo_goal", "type": "relation", "collectionId": "brain_pages",
         "cascadeDelete": False, "maxSelect": 1},
    ],
    "brain_page_versions": [
        {"name": "page", "type": "relation", "collectionId": "brain_pages",
         "cascadeDelete": False, "maxSelect": 1},
    ],
    "brain_log": [
        {"name": "page", "type": "relation", "collectionId": "brain_pages",
         "cascadeDelete": False, "maxSelect": 1},
    ],
}

# Nombres de campos que deben omitirse en la creación inicial y agregarse vía PATCH
DEFERRED_FIELDS = set()
for _fields in SELF_REF_FIELDS.values():
    for f in _fields:
        DEFERRED_FIELDS.add(f['name'])

# Mapeo de colección -> nombres de campos que se omiten en creación y se patchan después
DEFERRED_BY_COLLECTION = {}
for col_name, fields in SELF_REF_FIELDS.items():
    DEFERRED_BY_COLLECTION[col_name] = {f['name'] for f in fields}

# Dependencias para creación/verificación (sin relaciones internas)
DEPENDENCIES = {
    'brain_pages':     ['brain_contexts', 'brain_tags'],
    'brain_log':       ['brain_contexts'],
    'brain_page_versions': ['brain_contexts'],
}


def setup_contexts(pb: PB) -> dict:
    """Crea las colecciones del PocketBrain en PocketBase.

    Resuelve dinámicamente los IDs de las colecciones para las relaciones,
    ya que PocketBase requiere IDs reales (pbc_xxx) en collectionId, no nombres.

    Usa un enfoque de dos pasos:
      1. Crea todas las colecciones sin campos de relación interna/cruzada no resueltos.
      2. PATCHea cada colección para agregar los campos diferidos con collectionId real.
    """
    import copy
    results = {}
    collection_ids = {}

    # Paso 1: Crear colecciones base (sin campos diferidos)
    for name in CREATION_ORDER:
        schema = BRAIN_SCHEMA[name]
        deferred_names = DEFERRED_BY_COLLECTION.get(name, set())

        # Verificar si ya existe
        try:
            existing = pb.get_collection(name)
            if existing and 'id' in existing:
                collection_ids[name] = existing['id']
                results[name] = {"status": "already_exists", "id": existing['id']}
                continue
        except Exception:
            pass

        # Copiar campos y omitir los diferidos
        fields = copy.deepcopy(schema['fields'])
        fields = [f for f in fields if f['name'] not in deferred_names]

        # Resolver collectionId placeholders en campos restantes
        for field in fields:
            if field.get('type') == 'relation' and field.get('collectionId'):
                ref_name = field['collectionId']
                if ref_name in collection_ids:
                    field['collectionId'] = collection_ids[ref_name]
                else:
                    try:
                        col_info = pb.get_collection(ref_name)
                        if col_info and 'id' in col_info:
                            field['collectionId'] = col_info['id']
                            collection_ids[ref_name] = col_info['id']
                    except Exception:
                        pass

        try:
            result = pb.create_collection(
                name=schema['name'],
                fields=fields,
                collection_type=schema['type'],
            )
            if isinstance(result, dict) and 'id' in result:
                collection_ids[name] = result['id']
                results[name] = {"status": "created", "id": result['id']}
            else:
                results[name] = {"status": "error", "error": str(result)}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}

    # Paso 2: PATCH de campos diferidos con collectionId real
    for name, patch_fields in SELF_REF_FIELDS.items():
        if name not in collection_ids:
            continue
        col_id = collection_ids[name]
        try:
            existing = pb.get_collection(col_id)
            current_fields = existing.get('fields', [])
            # Convertir campos patch a usar collectionId real de brain_pages
            resolved_patch = []
            for f in patch_fields:
                f_copy = dict(f)
                target = f_copy.get('collectionId')
                if target and target in collection_ids:
                    f_copy['collectionId'] = collection_ids[target]
                resolved_patch.append(f_copy)
            updated_fields = current_fields + resolved_patch
            pb.update_collection(col_id, {'fields': updated_fields})
            results[name]['deferred_patched'] = [f['name'] for f in patch_fields]
        except Exception as e:
            results[name]['deferred_patched'] = f"error: {str(e)[:80]}"

    return results


# Dependencias para creación/verificación
DEPENDENCIES = {
    'brain_pages':     ['brain_contexts', 'brain_tags'],
    'brain_log':       ['brain_contexts', 'brain_pages'],
    'brain_page_versions': ['brain_contexts', 'brain_pages'],
}


# ═════════════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════════════

def slugify(text: str) -> str:
    """Convierte texto a slug: lowercase, hyphens, sin acentos ni especiales."""
    text = text.lower().strip()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')[:120]


def sha256(text: str) -> str:
    """Hash SHA-256 de un string."""
    return hashlib.sha256(text.encode()).hexdigest()


def sha256_file(filepath: str) -> str:
    """Hash SHA-256 de un archivo (lectura por chunks)."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def extract_wikilinks(body: str) -> list:
    """Extrae todos los [[wikilinks]] de un texto markdown."""
    if not body:
        return []
    return re.findall(r'\[\[([^\]]+)\]\]', body)


# ═════════════════════════════════════════════════════════════════════
#  SETUP
# ═════════════════════════════════════════════════════════════════════

def nuke_context(pb, context_name: str = None, confirm: str = None):
    """Borra todos los datos de un cerebro o de toda la DB.

    Args:
        pb: Instancia PB autenticada.
        context_name: Nombre del contexto a limpiar. Si es None, limpia TODO.
        confirm: Debe ser 'YES_DELETE_ALL' para proceder.

    Returns:
        Dict con contadores de registros borrados por colección.
    """
    if confirm != 'YES_DELETE_ALL':
        raise ValueError("Debes pasar confirm='YES_DELETE_ALL' para confirmar.")

    context_id = None
    if context_name:
        contexts = pb.list('brain_contexts', filter="(name='" + context_name + "')")
        if contexts:
            context_id = contexts[0]['id']
        else:
            raise ValueError("Contexto '" + context_name + "' no encontrado")

    # Orden: dependencias primero (hijos antes que padres)
    order = [
        'brain_log',            # depende de brain_pages
        'brain_page_versions',  # depende de brain_pages
        'brain_pages',         # depende de brain_tags
        'brain_tags',          # depende de brain_contexts
    ]

    stats = {}
    for col in order:
        try:
            if context_id:
                # Contar y borrar solo los de este contexto
                records = pb.all(col, filter="(context='" + context_id + "')", perPage=500)
                count = len(records)
                for r in records:
                    pb.delete(col, r['id'])
            else:
                # Truncar toda la colección
                count = len(pb.all(col, perPage=500))
                pb._request('DELETE', '/api/collections/' + col + '/truncate')
            stats[col] = count
        except Exception as e:
            stats[col] = 'ERROR: ' + str(e)[:80]

    # Si es limpieza total, también borrar brain_contexts
    if not context_name:
        try:
            count = len(pb.all('brain_contexts', perPage=500))
            pb._request('DELETE', '/api/collections/brain_contexts/truncate')
            stats['brain_contexts'] = count
        except Exception as e:
            stats['brain_contexts'] = 'ERROR: ' + str(e)[:80]

    return stats


def setup_contexts(pb: PB) -> dict:
    """Crea las 6 colecciones del PocketBrain en PocketBase.

    Resuelve dinámicamente los IDs de las colecciones para las relaciones,
    ya que PocketBase requiere IDs reales (pbc_xxx) en collectionId, no nombres.

    Args:
        pb: Instancia de PB autenticada (usa quick_pb() si no tienes una).

    Returns:
        Dict con {nombre_coleccion: {'status': 'created'|'already_exists'|'error', ...}}
    """
    import copy
    results = {}
    collection_ids = {}  # name → pbc_id

    for name in CREATION_ORDER:
        schema = BRAIN_SCHEMA[name]

        # Verificar si ya existe
        try:
            existing = pb.get_collection(name)
            if existing and 'id' in existing:
                collection_ids[name] = existing['id']
                results[name] = {"status": "already_exists", "id": existing['id']}
                continue
        except Exception:
            pass

        # Resolver collectionId placeholders en campos relation
        fields = copy.deepcopy(schema['fields'])
        
        # Quitar campos self-reference (se agregan con PATCH después)
        self_ref_names = {f['name'] for f in SELF_REF_FIELDS.get(name, [])}
        fields = [f for f in fields if f['name'] not in self_ref_names]
        
        for field in fields:
            if field.get('type') == 'relation' and field.get('collectionId'):
                ref_name = field['collectionId']
                if ref_name in collection_ids:
                    field['collectionId'] = collection_ids[ref_name]
                else:
                    # Try to look up directly
                    try:
                        col_info = pb.get_collection(ref_name)
                        if col_info and 'id' in col_info:
                            field['collectionId'] = col_info['id']
                    except Exception:
                        pass

        try:
            result = pb.create_collection(
                name=schema['name'],
                fields=fields,
                collection_type=schema['type'],
            )
            if isinstance(result, dict) and 'id' in result:
                collection_ids[name] = result['id']
                results[name] = {"status": "created", "id": result['id']}
            else:
                results[name] = {"status": "error", "error": str(result)}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}

    # Post-creation: PATCH self-referencing fields
    for name in SELF_REF_FIELDS:
        if name in collection_ids:
            col_id = collection_ids[name]
            patch_fields = []
            for f in SELF_REF_FIELDS[name]:
                field_copy = dict(f)
                field_copy['collectionId'] = col_id
                patch_fields.append(field_copy)
            try:
                existing = pb.get_collection(col_id)
                current_fields = existing.get('fields', [])
                updated_fields = current_fields + patch_fields
                pb.update_collection(col_id, {'fields': updated_fields})
                results[name]['self_ref_patched'] = True
            except Exception as e:
                results[name]['self_ref_patched'] = 'error: ' + str(e)[:80]

    return results


# ═════════════════════════════════════════════════════════════════════
#  BRAIN CLASS
# ═════════════════════════════════════════════════════════════════════


PAGE_TYPES = [
    'entity', 'concept', 'comparison', 'query', 'raw',
    'project', 'plan', 'note', 'idea', 'todo',
    'goal', 'milestone', 'reminder', 'journal', 'file'
]


def suggest_page_type(title: str, body: str = '') -> str:
    """Sugiere un page_type basado en el contenido.

    Heurísticas:
    - 'project' si el título contiene palabras como proyecto, mvp, roadmap
    - 'raw' si el body empieza con URL o parece fuente externa
    - 'comparison' si el body contiene tablas o 'vs' en el título
    - 'query' si el título termina con ? o empieza con query:
    - 'entity' si el título parece un nombre propio (mayúscula inicial, sin verbo)
    - 'concept' para todo lo demás (default)

    Args:
        title: Título de la página.
        body: Contenido markdown (opcional).

    Returns:
        Uno de los PAGE_TYPES
    """
    t = title.lower().strip()
    b = (body or '').lower()

    # Project
    project_keywords = ['proyecto', 'project', 'mvp', 'sprint', 'release', 'lanzamiento']
    if any(kw in t for kw in project_keywords):
        return 'project'

    # Raw
    if b.startswith('http://') or b.startswith('https://') or b.startswith('#'):
        return 'raw'
    if t.startswith('ingest') or t.startswith('raw:'):
        return 'raw'

    # Comparison
    if ' vs ' in t or ' vs. ' in t or ' versus ' in t:
        return 'comparison'
    # Tables in body often indicate comparisons
    if '|' in b and ('---' in b or b.count('|') > 6):
        return 'comparison'

    # Query
    if t.endswith('?') or t.startswith('query:') or t.startswith('que ') or t.startswith('what '):
        return 'query'

    # Plan: roadmap, spec, strategy, design doc, timeline, schedule, budget
    plan_keywords = ['plan', 'roadmap', 'estrategia', 'strategy', 'spec', 'especificacion',
                     'timeline', 'cronograma', 'schedule', 'presupuesto', 'budget',
                     'design doc', 'diseno', 'arquitectura', 'propuesta', 'proposal']
    if any(kw in t for kw in plan_keywords):
        return 'plan'

    # Note: notas, apuntes, meeting notes, ideas sueltas
    note_keywords = ['note', 'nota', 'apunte', 'meeting', 'reunion', 'talk', 'charla',
                     'memoria', 'minutes', 'minuta']
    if any(kw in t for kw in note_keywords):
        return 'note'

    # Idea: brainstorming, propuesta, sugerencia, idea
    idea_keywords = ['idea', 'brainstorm', 'lluvia', 'propuesta', 'suggestion',
                     'que tal si', 'what if', 'imagine', 'imagina']
    # Normalizar acentos en el título para matching
    t_noacc = t.replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('á','a')
    if any(kw in t_noacc for kw in idea_keywords):
        return 'idea'

    # Entity: proper noun pattern (single word, capitalized, not a common term)
    # Heuristic: short title, no spaces, looks like a model/product name
    if len(title.split()) <= 3 and not any(kw in t for kw in ['que es', 'what is', 'como', 'how to', 'guia', 'guide']):
        # Skip if title contains common concept/technical words
        concept_words = ['cache', 'arquitectura', 'patron', 'pattern', 'algoritmo', 'algorithm',
                         'protocolo', 'framework', 'libreria', 'librería', 'library',
                         'distribuido', 'distributed', 'microservicio', 'api', 'base de datos']
        if any(cw in t for cw in concept_words):
            return 'concept'
        # Could be entity or concept — prefer entity for named things
        common_verbs = ['implementar', 'build', 'create', 'usar', 'use', 'como']
        if not any(v in t for v in common_verbs):
            return 'entity'

    # Default: concept
    return 'concept'


class Brain:
    """Cliente para un cerebro de conocimiento específico.

    Args:
        context_name: Nombre del contexto ('personal', 'projects', etc.)
        pb: Instancia PB opcional (si no, crea una nueva y autentica).

    Uso típico:
        brain = Brain('personal')
        brain.orient()                        # cargar contexto
        brain.create_page(...)                # crear página
        pages = brain.search('transformer')   # buscar
        report = brain.lint()                 # auditar
    """

    def __init__(self, context_name: str = '', pb: Optional[PB] = None,
                 agent: str = 'chaos-manager', user: str = 'alvaro'):
        if not context_name:
            context_name = os.environ.get('POCKETBRAIN_CONTEXT', '') or 'personal'
        self.context_name = context_name
        self.pb = pb or _pocketbrain_pb()
        self.agent = agent
        self.user = user
        self._context_id: Optional[str] = None
        self._schema: Optional[dict] = None
        self._tag_cache: dict = {}      # name → id

    # ── Orient ───────────────────────────────────────────────────

    def orient(self) -> dict:
        """Carga el contexto del cerebro: ID, schema, tags cacheados.

        Llama esto al inicio de cada sesión antes de operar con un cerebro.
        """
        contexts = self.pb.list('brain_contexts', filter=f"(name='{self.context_name}')")
        if not contexts:
            raise ValueError(
                f"Contexto '{self.context_name}' no encontrado. "
                f"Usa create_context() primero."
            )

        context = contexts[0]
        self._context_id = context['id']
        self._schema = context.get('schema_config', {}) or {}

        # Cachear tags
        self._tag_cache = {}
        for t in self.pb.all('brain_tags',
                             filter=f"(context='{self._context_id}')"):
            self._tag_cache[t['name']] = t['id']

        # Contar páginas
        page_count = len(self.pb.list('brain_pages',
            filter=f"(context='{self._context_id}' && archived=false)",
            perPage=1, skipTotal=False))

        return {
            'context': context,
            'tag_count': len(self._tag_cache),
            'page_count': page_count,
            'schema': self._schema,
        }

    # ── Brain CRUD ───────────────────────────────────────────────

    def create_context(self, label: str, description: str = '',
                     schema_config: Optional[dict] = None) -> dict:
        """Crea un nuevo cerebro.

        Args:
            label: Nombre legible ("Cerebro Personal")
            description: Qué cubre este cerebro
            schema_config: Configuración opcional (usa defaults si no se provee)
        """
        default_schema = {
            "conventions": {
                "file_names": "lowercase-hyphens",
                "min_outbound_links": 2,
                "max_page_lines": 200,
            },
            "tag_taxonomy": {},
            "page_thresholds": {
                "create_page_after_sources": 2,
                "split_page_at_lines": 200,
            },
            "provenance": {
                "markers_enabled": True,
                "citation_format": "^[source-slug]",
            },
        }
        result = self.pb.create('brain_contexts', {
            'name': self.context_name,
            'label': label,
            'description': description,
            'schema_config': schema_config or default_schema,
        })
        self._context_id = result['id']
        self._schema = schema_config or default_schema
        self.log('setup', description=f'Cerebro "{self.context_name}" creado')
        return result

    # ── Tag management ───────────────────────────────────────────

    def get_or_create_tag(self, name: str, category: str = '') -> str:
        """Obtiene el ID de un tag, creándolo si no existe."""
        if name in self._tag_cache:
            return self._tag_cache[name]

        existing = self.pb.list('brain_tags',
            filter=f"(name='{name}' && context='{self._context_id}')")
        if existing:
            self._tag_cache[name] = existing[0]['id']
            return existing[0]['id']

        result = self.pb.create('brain_tags', {
            'name': name,
            'category': category,
            'context': self._context_id,
        })
        self._tag_cache[name] = result['id']
        return result['id']

    # ── Page CRUD ────────────────────────────────────────────────

    def create_page(self, title: str, body: str = '', page_type: str = 'concept',
                    *, filepath: str = '', related_slugs: Optional[list] = None,
                    tags: Optional[list] = None, **kwargs) -> dict:
        """Crea una página de conocimiento.

        Args:
            title: Título de la página
            body: Contenido en markdown con [[wikilinks]]
            page_type: Uno de los PAGE_TYPES
            filepath: Si se provee, sube el archivo como file_attachment vía curl
            related_slugs: Lista de slugs de páginas relacionadas
            tags: Lista de nombres de tags (se crean si no existen)
            **kwargs: Campos del schema directamente (kb_*, status, owner, deadline, etc.)
        """
        if not self._context_id:
            self.orient()

        slug = slugify(title)

        # Auto-suggest page_type si no se especificó explícitamente
        effective_page_type = page_type
        if not effective_page_type or effective_page_type == '':
            effective_page_type = suggest_page_type(title, body)
        if effective_page_type not in PAGE_TYPES:
            raise ValueError(f"page_type '{effective_page_type}' no válido. Debe ser uno de: {', '.join(PAGE_TYPES)}")

        # Extraer [[wikilinks]] del body para auto-link
        links = extract_wikilinks(body)
        linked_page_ids = []
        for link_slug in links:
            # Soporte para alias [[target|alias]]
            link_slug = link_slug.split('|')[0].strip()
            linked = self._get_page(link_slug)
            if linked and 'id' in linked:
                linked_page_ids.append(linked['id'])

        # Si se pasaron related_slugs, resolverlos también
        if related_slugs:
            for rs in related_slugs:
                rp = self._get_page(rs)
                if rp and 'id' in rp and rp['id'] not in linked_page_ids:
                    linked_page_ids.append(rp['id'])

        data = {
            'title': title,
            'slug': slug,
            'context': self._context_id,
            'page_type': effective_page_type,
            'body': body,
            'summary': kwargs.pop('summary', body[:200].split('\n')[0] if body else ''),
            'archived': False,
        }

        # Tags
        if tags:
            data['tags'] = [self.get_or_create_tag(t) for t in tags]

        # Related pages
        if linked_page_ids:
            data['related_pages'] = linked_page_ids

        # Resolver relaciones pasadas como slugs a IDs
        relation_fields = {'project', 'todo_goal'}
        for rel_key in relation_fields:
            if rel_key in kwargs:
                rel_val = kwargs[rel_key]
                if isinstance(rel_val, str) and rel_val and not rel_val.startswith('pbc_'):
                    rel_page = self._get_page(rel_val)
                    if rel_page and 'id' in rel_page:
                        kwargs[rel_key] = rel_page['id']
                    else:
                        kwargs[rel_key] = None

        # Campos directos del schema (excluir parámetros de conveniencia)
        convenience = {'filepath', 'related_slugs', 'tags'}
        for key, value in kwargs.items():
            if key in convenience:
                continue
            if value is not None and value != '':
                data[key] = value

        # Si hay filepath, hacer multipart upload via curl
        if filepath:
            import subprocess
            host = self.pb.host
            url = f"{host}/api/collections/brain_pages/records"
            token = self.pb.get_token()
            args = ["curl", "-s", "-X", "POST", url,
                    "-H", f"Authorization: Bearer {token}",
                    "-F", f"title={title}",
                    "-F", f"slug={slug}",
                    "-F", f"context={self._context_id}",
                    "-F", f"page_type={effective_page_type}",
                    "-F", f"body={body or ''}",
                    "-F", f"file_attachment=@{filepath}",
            ]
            for key, value in data.items():
                if key in ('title', 'slug', 'context', 'page_type', 'body'):
                    continue
                if isinstance(value, list):
                    for v in value:
                        args += ["-F", f"{key}={v}"]
                else:
                    args += ["-F", f"{key}={value}"]
            result = subprocess.run(args, capture_output=True, text=True)
            data_resp = json.loads(result.stdout)
            if 'id' not in data_resp:
                raise RuntimeError(f"File upload failed: {data_resp}")
            page = data_resp
        else:
            page = self.pb.create('brain_pages', data)
        page_id = page.get('id')

        # Auto-backlinks: agregar esta página al related_pages de cada página linkeada
        if linked_page_ids and page_id:
            for linked_id in linked_page_ids:
                try:
                    linked_page = self.pb.get('brain_pages', linked_id, expand='related_pages')
                    current_related = linked_page.get('expand', {}).get('related_pages', [])
                    current_ids = [r['id'] for r in current_related] if current_related and isinstance(current_related[0], dict) else linked_page.get('related_pages', [])
                    if page_id not in current_ids:
                        current_ids.append(page_id)
                        self.pb.update('brain_pages', linked_id, {'related_pages': current_ids})
                except Exception:
                    pass  # Si falla el backlink, no bloquear la creación

        self.log('create', page_id=page_id, description=f'Created: {title} (type={effective_page_type}, links={len(linked_page_ids)})')
        self.save_version(slug, 'Initial version')
        return page

    # ── Typed page creators ──────────────────────────────────────

    def create_project(self, title: str, body: str = '', **kwargs) -> dict:
        """Crea una página de tipo project."""
        return self.create_page(title=title, body=body, page_type='project', **kwargs)

    def create_goal(self, title: str, body: str = '', **kwargs) -> dict:
        """Crea una página de tipo goal."""
        return self.create_page(title=title, body=body, page_type='goal', **kwargs)

    def create_milestone(self, title: str, body: str = '', **kwargs) -> dict:
        """Crea una página de tipo milestone."""
        return self.create_page(title=title, body=body, page_type='milestone', **kwargs)

    def create_plan(self, title: str, body: str = '', **kwargs) -> dict:
        """Crea una página de tipo plan."""
        return self.create_page(title=title, body=body, page_type='plan', **kwargs)

    def create_idea(self, title: str, body: str = '', **kwargs) -> dict:
        """Crea una página de tipo idea."""
        return self.create_page(title=title, body=body, page_type='idea', **kwargs)

    def create_note(self, title: str, body: str = '', **kwargs) -> dict:
        """Crea una página de tipo note."""
        return self.create_page(title=title, body=body, page_type='note', **kwargs)

    def create_todo(self, title: str, body: str = '', **kwargs) -> dict:
        """Crea una página de tipo todo."""
        return self.create_page(title=title, body=body, page_type='todo', **kwargs)

    def create_reminder(self, title: str, body: str = '', **kwargs) -> dict:
        """Crea una página de tipo reminder."""
        return self.create_page(title=title, body=body, page_type='reminder', **kwargs)

    def create_journal(self, title: str = '', body: str = '', **kwargs) -> dict:
        """Crea una página de tipo journal."""
        if not title:
            from datetime import date
            title = f"Journal: {date.today().isoformat()}"
        return self.create_page(title=title, body=body, page_type='journal', **kwargs)

    def create_file(self, title: str, body: str = '', *, filepath: str = '', **kwargs) -> dict:
        """Crea una página de tipo file. Si filepath se provee, adjunta el archivo."""
        return self.create_page(title=title, body=body, page_type='file', filepath=filepath, **kwargs)

    def build_backlinks(self, slug: Optional[str] = None) -> dict:
        """Reconstruye los related_pages de una o todas las páginas
        basándose en los [[wikilinks]] del body.

        Escanea el body de cada página en busca de [[wikilinks]],
        y actualiza el campo related_pages de cada página linkeada
        para que incluya a la página que la referencia.

        Args:
            slug: Slug específico (opcional). Si no se provee, procesa todas.

        Returns:
            Dict con stats de backlinks creados.
        """
        if not self._context_id:
            self.orient()

        if slug:
            pages = [self._get_page(slug)] if self._get_page(slug) else []
        else:
            pages = self.pb.all('brain_pages',
                filter=f"(context='{self._context_id}' && archived=false)")

        stats = {'scanned': 0, 'backlinks_added': 0}
        slug_map = {p['slug']: p for p in pages}

        for page in pages:
            body = page.get('body', '') or ''
            links = extract_wikilinks(body)
            stats['scanned'] += 1

            for link_slug in links:
                link_slug = link_slug.split('|')[0].strip()
                target = slug_map.get(link_slug)
                if not target:
                    continue

                # Agregar esta página como related_page de la página linkeada
                try:
                    current = target.get('related_pages', []) or []
                    if isinstance(current, list) and len(current) > 0 and isinstance(current[0], dict):
                        current = [r['id'] for r in current]
                    if page['id'] not in current:
                        current.append(page['id'])
                        self.pb.update('brain_pages', target['id'], {'related_pages': current})
                        stats['backlinks_added'] += 1
                        # Actualizar slug_map para evitar re-procesar
                        slug_map[link_slug] = self._get_page(link_slug) or target
                except Exception:
                    pass

        self.log('update', description=f'Build backlinks: {stats}')
        return stats

    def update_page(self, slug_or_id: str, **updates) -> dict:
        """Actualiza una página existente.

        Args:
            slug_or_id: Slug o ID de la página
            **updates: Campos a actualizar. 'tags' acepta lista de nombres. 
                       'related_slugs' acepta lista de slugs.
        """
        page = self._get_page(slug_or_id)
        if not page:
            raise ValueError(f"Página '{slug_or_id}' no encontrada")

        # Resolver nombres a IDs
        if 'tags' in updates and updates['tags']:
            updates['tags'] = [self.get_or_create_tag(t) for t in updates['tags']]
        if 'related_slugs' in updates:
            slugs = updates.pop('related_slugs')
            if slugs:
                ids = self._slugs_to_ids(slugs if isinstance(slugs, list) else [slugs])
                if ids:
                    updates['related_pages'] = ids

        result = self.pb.update('brain_pages', page['id'], updates)
        change_desc = ', '.join(updates.keys())
        self.log('update', page_id=page['id'],
                 description=f'Updated: {page["title"]} ({change_desc})')
        self.save_version(page['slug'], f'Updated: {change_desc}')
        return result

    def append_to_page(self, slug: str, text: str, heading: str = '') -> dict:
        """Agrega contenido al final del body sin reemplazarlo.

        Args:
            slug: Slug de la pagina.
            text: Markdown a agregar.
            heading: Si se provee, se inserta como '## heading' antes del texto.

        Returns:
            El registro actualizado.

        Ejemplo:
            brain.append_to_page('mantrams', '- Nuevo matram: X', heading='2026-06-10')
        """
        page = self._get_page(slug)
        if not page:
            raise ValueError(f"Pagina '{slug}' no encontrada")

        new_body = page.get('body', '') or ''
        if new_body:
            new_body += '\n\n'
        if heading:
            new_body += '## ' + heading + '\n\n'
        new_body += text

        return self.update_page(slug, body=new_body)

    def archive_page(self, slug: str) -> dict:
        """Archiva una página (soft delete)."""
        page = self._get_page(slug)
        if not page:
            raise ValueError(f"Página '{slug}' no encontrada")
        result = self.pb.update('brain_pages', page['id'], {'archived': True})
        self.log('archive', page_id=page['id'],
                 description=f'Archived: {page["title"]}')
        return result

    def delete_page(self, slug: str) -> bool:
        """Elimina permanentemente una página."""
        page = self._get_page(slug)
        if not page:
            raise ValueError(f"Página '{slug}' no encontrada")
        title = page['title']
        result = self.pb.delete('brain_pages', page['id'])
        self.log('delete', description=f'Deleted: {title}')
        return result

    # ── Query ────────────────────────────────────────────────────

    def get_page(self, slug: str, expand: str = 'tags,related_pages') -> Optional[dict]:
        """Obtiene una página por slug con relaciones expandidas."""
        return self._get_page(slug, expand)

    def list_pages(self, page_type: Optional[str] = None,
                   tag: Optional[str] = None,
                   status: Optional[str] = None,
                   owner: Optional[str] = None,
                   include_archived: bool = False,
                   sort: str = '', per_page: int = 50) -> list:
        """Lista páginas con filtros opcionales."""
        if not self._context_id:
            self.orient()
        filters = [f"(context='{self._context_id}' && archived=false)"]
        if page_type:
            filters.append(f"(page_type='{page_type}')")
        if tag:
            # Resolver nombre de tag a ID
            tag_id = self.get_or_create_tag(tag)
            filters.append(f"(tags?='{tag_id}')")
        if status:
            filters.append(f"(status='{status}')")
        if owner:
            filters.append(f"(owner='{owner}')")

        params = {
            'filter': "&&".join(filters),
            'perPage': per_page,
            'expand': 'tags,related_pages',
        }
        if sort:
            params['sort'] = sort
        return self.pb.list('brain_pages', **params)

    def search(self, query: str, limit: int = 20) -> list:
        """Busca páginas por título o contenido.

        Divide el query en palabras y busca cada una de forma
        case-insensitive contra title y body. Combina resultados
        rankeados por relevancia (coincidencias en título pesan más).

        Args:
            query: Texto a buscar (ej. 'transformer architecture')
            limit: Máximo de resultados.

        Returns:
            Lista de páginas ordenadas por relevancia descendente.
        """
        if not self._context_id:
            self.orient()

        # Traer todas las páginas activas del cerebro
        candidates = self.pb.all('brain_pages',
            filter=f"(context='{self._context_id}' && archived=false)")

        if not candidates:
            return []

        # Tokenizar el query
        terms = [t.lower() for t in query.split() if len(t) > 1]

        # Scoring: cada término matcheado en title = 3pts, en body = 1pt
        scored = []
        for page in candidates:
            title_lower = (page.get('title') or '').lower()
            body_lower = (page.get('body') or '').lower()
            score = 0
            for term in terms:
                if term in title_lower:
                    score += 3
                if term in body_lower:
                    score += 1
            if score > 0:
                scored.append((score, page))

        # Ordenar por score descendente, limitar
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]

    # ── Ingest ───────────────────────────────────────────────────

    def ingest_text(self, text: str, title: str = '',
                    page_type: str = 'raw',
                    kb_source_url: str = '',
                    tags: Optional[list] = None) -> dict:
        """Ingesta texto crudo como página.

        Calcula kb_source_sha256 automáticamente si page_type='raw'.
        """
        if not self._context_id:
            self.orient()

        title = title or f"Ingest {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        kwargs = {
            'title': title,
            'body': text,
            'page_type': page_type,
            'tags': tags,
        }
        if kb_source_url:
            kwargs['kb_source_url'] = kb_source_url
        if page_type == 'raw':
            kwargs['kb_source_sha256'] = sha256(text)
        return self.create_page(**kwargs)

    # ── Log ──────────────────────────────────────────────────────

    def log(self, action: str, page_id: Optional[str] = None,
            description: str = '', details: Optional[dict] = None) -> dict:
        """Registra una acción en el brain_log con trazabilidad."""
        if not self._context_id:
            self.orient()

        meta = details or {}
        meta['agent'] = self.agent
        meta['requested_by'] = self.user

        data = {
            'context': self._context_id,
            'action': action,
            'description': description,
            'details': meta,
        }
        if page_id:
            data['page'] = page_id
        return self.pb.create('brain_log', data)

    def recent_logs(self, limit: int = 30,
                    action: Optional[str] = None) -> list:
        """Últimas entradas del log."""
        filters = [f"(context='{self._context_id}')"]
        if action:
            filters.append(f"(action='{action}')")
        return self.pb.list('brain_log',
            filter="&&".join(filters),
            perPage=limit, expand='page')

    # ── Lint ─────────────────────────────────────────────────────

    def lint(self) -> dict:
        """Ejecuta un lint completo del cerebro.

        Revisa: huérfanos, links rotos, baja confianza, contradicciones,
        páginas gigantes, tags no autorizados.

        Returns:
            Dict con issues categorizados y conteo resumen.
        """
        if not self._context_id:
            self.orient()

        pages = self.pb.all('brain_pages',
            filter=f"(context='{self._context_id}' && archived=false)",
            expand='tags')

        report = {
            'total_pages': len(pages),
            'orphans': [],
            'broken_links': [],
            'low_confidence': [],
            'contested_pages': [],
            'invalid_tags': [],
            'oversized_pages': [],
        }

        # Mapa slug → page
        slug_map = {p['slug']: p for p in pages}

        # Tags válidos en cache
        valid_tags = set(self._tag_cache.keys())

        # Tags de la taxonomía (los "autorizados")
        taxonomy_tags = set()
        if self._schema and 'tag_taxonomy' in self._schema:
            for cat_tags in self._schema['tag_taxonomy'].values():
                taxonomy_tags.update(cat_tags)

        max_lines = (
            self._schema.get('page_thresholds', {})
            .get('split_page_at_lines', 200)
        )

        # ── Análisis por página ──
        all_linked = set()  # slugs que reciben [[wikilinks]]
        page_tags = {}      # slug → lista de nombres de tag

        for page in pages:
            slug = page['slug']
            body = page.get('body', '')

            # Confidence
            if page.get('kb_confidence') == 'low':
                report['low_confidence'].append(slug)

            # Contested
            if page.get('kb_contested'):
                report['contested_pages'].append(slug)

            # Oversized
            if body and body.count('\n') > max_lines:
                report['oversized_pages'].append(slug)

            # Tags de la página
            expanded_tags = page.get('expand', {}).get('tags', [])
            ptags = []
            if expanded_tags and isinstance(expanded_tags, list) and len(expanded_tags) > 0:
                if isinstance(expanded_tags[0], dict):
                    ptags = [t.get('name', '') for t in expanded_tags]
                else:
                    # IDs crudos — buscar en cache
                    for tid in expanded_tags:
                        for name, cid in self._tag_cache.items():
                            if cid == tid:
                                ptags.append(name)
                                break
            page_tags[slug] = ptags

            # Tags no autorizados (vs taxonomía si existe)
            if taxonomy_tags:
                for t in ptags:
                    if t not in taxonomy_tags:
                        report['invalid_tags'].append({
                            'page': slug, 'tag': t,
                        })

            # Wikilinks
            links = extract_wikilinks(body)
            for link in links:
                all_linked.add(link)
                if link not in slug_map:
                    report['broken_links'].append({
                        'page': slug, 'link': link,
                    })

        # ── Huérfanos ──
        for page in pages:
            if page['slug'] not in all_linked:
                report['orphans'].append(page['slug'])

        # ── Drift detection ──
        report['drift'] = self.detect_drift(limit=50)

        # ── Frontmatter validation ──
        report['frontmatter_issues'] = self.validate_frontmatter()

        # ── Summary ──
        report['summary'] = {
            'orphans': len(report['orphans']),
            'broken_links': len(report['broken_links']),
            'low_confidence': len(report['low_confidence']),
            'contested': len(report['contested_pages']),
            'invalid_tags': len(report['invalid_tags']),
            'oversized': len(report['oversized_pages']),
            'drift': len(report['drift']),
            'frontmatter_issues': sum(len(v) for v in report['frontmatter_issues'].values()),
        }

        self.log('lint', description=f'Lint: {report["summary"]}')
        return report

    # ── Schema management ────────────────────────────────────────

    def get_schema(self) -> dict:
        """Obtiene el schema_config del cerebro."""
        if not self._context_id:
            self.orient()
        return self._schema or {}

    def update_schema(self, updates: dict) -> dict:
        """Actualiza el schema_config (merge superficial)."""
        current = self.get_schema()
        merged = {**current, **updates}
        self.pb.update('brain_contexts', self._context_id,
                       {'schema_config': merged})
        self._schema = merged
        self.log('update', description='Schema actualizado')
        return merged

    def add_tag_to_taxonomy(self, tag: str, category: str) -> dict:
        """Agrega un tag a la taxonomía del schema."""
        schema = self.get_schema()
        taxonomy = schema.setdefault('tag_taxonomy', {})
        if category not in taxonomy:
            taxonomy[category] = []
        if tag not in taxonomy[category]:
            taxonomy[category].append(tag)
        return self.update_schema({'tag_taxonomy': taxonomy})

    # ── Index ────────────────────────────────────────────────────

    def index(self) -> dict:
        """Genera un índice del cerebro agrupado por page_type.

        Equivalente al index.md del llm-wiki original.
        """
        if not self._context_id:
            self.orient()

        pages = self.pb.all('brain_pages',
            filter=f"(context='{self._context_id}' && archived=false)",
            sort='title')

        index = {
            'context': self.context_name,
            'total_pages': len(pages),
            'entity': [],
            'concept': [],
            'comparison': [],
            'query': [],
            'raw': [],
        }

        for p in pages:
            pt = p.get('page_type', 'concept')
            index[pt].append({
                'slug': p['slug'],
                'title': p['title'],
                'summary': p.get('summary', ''),
                'kb_confidence': p.get('kb_confidence'),
            })

        return index

    # ── Version history ─────────────────────────────────────────

    def save_version(self, slug: str, change_summary: str = '') -> Optional[dict]:
        """Guarda una snapshot de la página actual en brain_page_versions.

        Se llama automáticamente desde create_page() y update_page().
        """
        page = self._get_page(slug)
        if not page:
            return None

        # Calcular el siguiente número de versión
        existing = self.pb.list('brain_page_versions',
            filter=f"(page='{page['id']}')", sort='-version', perPage=1)
        next_version = (existing[0]['version'] + 1) if existing else 1

        return self.pb.create('brain_page_versions', {
            'page': page['id'],
            'version': next_version,
            'title': page.get('title', ''),
            'body': page.get('body', ''),
            'summary': page.get('summary', ''),
            'change_summary': change_summary,
            'page_type': page.get('page_type', ''),
        })

    def get_history(self, slug: str, limit: int = 20) -> list:
        """Devuelve el historial de versiones de una página (más reciente primero)."""
        page = self._get_page(slug)
        if not page:
            return []
        return self.pb.list('brain_page_versions',
            filter=f"(page='{page['id']}')", sort='-version', perPage=limit)

    # ── Todos ───────────────────────────────────────────────────

    def todos(self, status: Optional[str] = None,
              owner: Optional[str] = None,
              goal_id: Optional[str] = None,
              limit: int = 50) -> list:
        return self.list_pages(
            page_type='todo',
            status=status,
            owner=owner,
            sort='-created',
            per_page=limit,
        )

    def update_todo(self, todo_id: str, **updates) -> dict:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        new_status = updates.get('status')
        if new_status == 'done':
            updates['done'] = True
            updates.setdefault('done_date', now)
        if 'page_slug' in updates:
            updates['related_slugs'] = [updates.pop('page_slug')]
        return self.update_page(todo_id, **updates)

    def start_todo(self, todo_id: str) -> dict:
        return self.update_todo(todo_id, status='in progress')

    def complete_todo(self, todo_id: str) -> dict:
        return self.update_todo(todo_id, status='done')

    def cancel_todo(self, todo_id: str) -> dict:
        return self.update_todo(todo_id, status='cancelled')

    def move_todo(self, todo_id: str, new_status: str) -> dict:
        valid = ['backlog', 'this week', 'today', 'in progress', 'done', 'cancelled']
        if new_status not in valid:
            raise ValueError("Status invalido: " + new_status)
        return self.update_todo(todo_id, status=new_status)

    # ── Journal ─────────────────────────────────────────────────

    def _journal_date_str(self, date_val=None):
        """Formatea fecha a string YYYY-MM-DD."""
        from datetime import datetime, timezone, date
        if date_val is None:
            date_val = date.today()
        if isinstance(date_val, str):
            return date_val
        if isinstance(date_val, (date, datetime)):
            return date_val.strftime('%Y-%m-%d')
        return str(date_val)

    def journal_today(self) -> dict:
        """Obtiene o crea la entrada del diario de hoy.

        Si no existe, la crea vacia. Siempre devuelve un registro.
        """
        from datetime import date
        return self.journal(date.today())

    def journal(self, date_val) -> dict:
        date_str = self._journal_date_str(date_val)
        title = "Journal: " + date_str
        existing = self.list_pages(page_type='journal')
        for p in existing:
            pd = (p.get('date', '') or '')[:10]
            if pd == date_str or pd == date_str[:10]:
                return p
        return self.create_journal(
            title=title,
            body='',
            date=date_str,
        )

    def journal_write(self, body: str, date_val=None,
                      mood: Optional[str] = None,
                      tags: Optional[list] = None,
                      append: bool = False) -> dict:
        entry = self.journal(date_val)
        updates = {}
        if append and entry.get('body'):
            updates['body'] = entry['body'] + '\n\n' + body
        else:
            updates['body'] = body
        if mood:
            updates['mood'] = mood
        if tags:
            updates['tags'] = [self.get_or_create_tag(t) for t in tags]
        return self.update_page(entry['slug'], **updates)

    def journal_range(self, from_date, to_date) -> list:
        """Lee entradas del diario en un rango de fechas.

        Args:
            from_date: Fecha inicio (inclusive).
            to_date: Fecha fin (inclusive).

        Returns:
            Lista de entradas ordenadas por fecha ascendente.
        """
        if not self._context_id:
            self.orient()

        d_from = self._journal_date_str(from_date)
        d_to = self._journal_date_str(to_date)

        return self.pb.list('brain_pages',
            filter=f"(context='{self._context_id}' && page_type='journal' && date>='{d_from}' && date<='{d_to}')",
            sort='date',
            perPage=100)

    def journal_search(self, query: str, limit: int = 20) -> list:
        """Busca en todas las entradas del diario.

        Divide el query en palabras y busca cada una de forma
        case-insensitive en title y body. Rankea por relevancia.
        """
        if not self._context_id:
            self.orient()

        candidates = self.pb.all('brain_pages',
            filter=f"(context='{self._context_id}' && page_type='journal')")

        terms = [t.lower() for t in query.split() if len(t) > 1]
        if not terms:
            return []

        scored = []
        for entry in candidates:
            title_lower = (entry.get('title') or '').lower()
            body_lower = (entry.get('body') or '').lower()
            score = 0
            for term in terms:
                if term in title_lower:
                    score += 3
                if term in body_lower:
                    score += 1
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    # ── Files ───────────────────────────────────────────────────

    def attach_file(self, page_slug: str, filepath: str,
                    name: str = '', file_type: str = 'other') -> dict:
        """Adjunta un archivo a una pagina como pagina type='file'.

        Crea una brain_page con page_type='file' y file_attachment,
        linkeada a la pagina via related_slugs.
        """
        if not self._context_id:
            self.orient()

        page = self._get_page(page_slug)
        if not page:
            raise ValueError("Pagina '" + page_slug + "' no encontrada")

        name = name or os.path.basename(filepath)

        return self.create_file(
            title=name,
            body='',
            filepath=filepath,
            file_type=file_type,
            related_slugs=[page_slug],
        )


    def list_files(self, page_slug: str) -> list:
        """Lista archivos adjuntos a una pagina (brain_pages con page_type='file')."""
        if not self._context_id:
            self.orient()
        page = self._get_page(page_slug)
        if not page:
            return []
        return self.pb.list("brain_pages",
            filter=f"(context='{self._context_id}' && page_type='file' && archived=false && related_pages?='{page['id']}')",
            perPage=100)

    def delete_file(self, file_id: str) -> bool:
        """Elimina un archivo adjunto (soft delete archiving the brain_page)."""
        return self.pb.update("brain_pages", file_id, {"archived": True})

    # ── Goals / Milestones ─────────────────────────────────────

    def list_goals(self, project_slug: Optional[str] = None,
                   type: Optional[str] = None,
                   status: Optional[str] = None) -> list:
        """Lista goals como paginas con page_type."""
        filters = {}
        if type:
            filters['page_type'] = type
        if status:
            filters['status'] = status
        goals = self.list_pages(**filters)
        if project_slug:
            project = self._get_page(project_slug)
            if project and 'id' in project:
                goals = [g for g in goals if project['id'] in (g.get('related_pages') or [])]
        return goals

    def complete_goal(self, goal_id: str, retrospective: str = '') -> dict:
        return self.update_page(goal_id, status='done')

    def cancel_goal(self, goal_id: str, retrospective: str = '') -> dict:
        return self.update_page(goal_id, status='cancelled')

    def update_goal(self, goal_id: str, **updates) -> dict:
        return self.update_page(goal_id, **updates)

    def get_goal_tree(self, project_slug: Optional[str] = None) -> list:
        """Devuelve goals como lista plana."""
        return self.list_goals(project_slug=project_slug)

    # ── Reports (predefined structured output) ───────────────────

    def report_projects(self) -> list:
        """Lista resumen de proyectos con métricas básicas."""
        projects = self.list_pages(page_type='project')
        result = []
        for p in projects:
            pid = p['id']
            goals = [g for g in self.list_goals() if pid in (g.get('related_pages') or [])]
            todos = self.list_pages(page_type='todo', per_page=200)
            ptodos = [t for t in todos if pid in (t.get('related_pages') or [])]
            done_todos = [t for t in ptodos if t.get('status') == 'done']
            result.append({
                'slug': p['slug'], 'title': p.get('title', ''),
                'status': p.get('status', ''),
                'goals_count': len(goals),
                'todos_count': len(ptodos), 'todos_done': len(done_todos),
                'progress': int(len(done_todos) / len(ptodos) * 100) if ptodos else 0,
            })
        return result

    def report_project_status(self, project_slug: str) -> dict:
        """Status completo de un proyecto: goals, todos, reminders, journal, notas."""
        project = self._get_page(project_slug, expand='related_pages,tags')
        if not project:
            raise ValueError(f"Proyecto '{project_slug}' no encontrado")
        pid = project['id']
        all_goals = self.list_goals()
        all_todos = self.list_pages(page_type='todo', per_page=200)
        all_reminders = self.list_pages(page_type='reminder', sort='date,time', per_page=100)
        all_journal = self.list_pages(page_type='journal', sort='-date', per_page=50)
        all_notes = self.list_pages(page_type='note', per_page=50)
        all_files = self.list_pages(page_type='file', per_page=50)

        goals = [g for g in all_goals if pid in (g.get('related_pages') or [])]
        todos = [t for t in all_todos if pid in (t.get('related_pages') or [])]
        reminders = [r for r in all_reminders if pid in (r.get('related_pages') or [])]
        journal = [j for j in all_journal if pid in (j.get('related_pages') or [])]
        notes = [n for n in all_notes if pid in (n.get('related_pages') or [])]
        files = [f for f in all_files if pid in (f.get('related_pages') or [])]

        status_counts = {}
        for t in todos:
            status_counts[t.get('status', 'backlog')] = status_counts.get(t.get('status', 'backlog'), 0) + 1

        return {
            'project': {'slug': project['slug'], 'title': project.get('title', ''), 'body': project.get('body', '') or '', 'status': project.get('status', '')},
            'goals': goals, 'todos': todos, 'reminders': reminders,
            'journal': journal, 'notes': notes, 'files': files,
            'counts': {
                'goals': len(goals), 'todos': len(todos),
                'reminders': len(reminders), 'journal': len(journal),
                'notes': len(notes), 'files': len(files),
                'todos_by_status': status_counts,
            }
        }

    def report_todos(self, status: Optional[str] = None, project_slug: Optional[str] = None) -> list:
        """Reporte de todos con metadatos útiles."""
        todos = self.todos(status=status)
        if project_slug:
            project = self._get_page(project_slug)
            if project:
                todos = [t for t in todos if project['id'] in (t.get('related_pages') or [])]
        return [{
            'slug': t.get('slug', ''), 'title': t.get('title', ''),
            'status': t.get('status', 'backlog'),
            'owner': t.get('owner', ''), 'deadline': (t.get('deadline', '') or '')[:10],
        } for t in todos]

    def report_journal(self, days: int = 7) -> list:
        """Journal de los últimos N días."""
        from datetime import datetime, timezone, timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
        all_entries = self.list_pages(page_type='journal', sort='-date', per_page=100)
        return [{
            'slug': j.get('slug', ''), 'date': (j.get('date', '') or '')[:10],
            'mood': j.get('mood', ''), 'body': j.get('body', '') or '',
        } for j in all_entries if (j.get('date') or '')[:10] >= cutoff]

    def report_reminders(self, date: str = '') -> list:
        """Recordatorios próximos o de una fecha."""
        reminders = self.reminders(date=date)
        return [{
            'slug': r.get('slug', ''), 'title': r.get('title', ''),
            'date': (r.get('date', '') or '')[:10], 'time': r.get('time', ''),
            'done': bool(r.get('done', False)),
        } for r in reminders]

    def report_lint(self) -> dict:
        """Resumen de lint para reportes."""
        return self.lint()




    def reminders(self, done: Optional[bool] = None, date: str = '',
                  page_slug: str = '') -> list:
        """Lista recordatorios como paginas con page_type='reminder'."""
        return self.list_pages(page_type='reminder', sort='date,time')

    def complete_reminder(self, reminder_id: str) -> dict:
        """Marca un recordatorio como done."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        return self.update_page(reminder_id, done=True, done_date=now)

    # ── File ingest ──────────────────────────────────────────────

    def ingest_file(self, filepath: str, title: str = '',
                    tags: Optional[list] = None,
                    kb_source_url: str = '') -> dict:
        """Ingesta un archivo (PDF, TXT, etc.) al cerebro.

        Args:
            filepath: Ruta al archivo en disco.
            title: Título (default: nombre del archivo).
            tags: Tags opcionales.
            kb_source_url: URL original si aplica.

        Returns:
            El registro creado en brain_pages.

        El archivo se sube como file_attachment. El body se deja vacío
        inicialmente — luego se llena con el texto extraído.
        """
        import subprocess

        if not self._context_id:
            self.orient()

        filename = os.path.basename(filepath)
        title = title or os.path.splitext(filename)[0]
        slug = slugify(title)
        file_hash = sha256_file(filepath)

        # Resolver tags a IDs
        tag_ids = [self.get_or_create_tag(t) for t in tags] if tags else []

        # Construir el multipart POST con curl
        host = self.pb.host
        token = self.pb.get_token()
        url = f"{host}/api/collections/brain_pages/records"

        args = [
            "curl", "-s", "-X", "POST", url,
            "-H", f"Authorization: Bearer {token}",
            "-F", f"title={title}",
            "-F", f"slug={slug}",
            "-F", f"context={self._context_id}",
            "-F", "page_type=raw",
            "-F", f"kb_source_sha256={file_hash}",
            "-F", f"file_attachment=@{filepath}",
        ]
        if kb_source_url:
            args += ["-F", f"kb_source_url={kb_source_url}"]
        for tid in tag_ids:
            args += ["-F", f"tags={tid}"]

        result = subprocess.run(args, capture_output=True, text=True)
        data = json.loads(result.stdout)

        if 'id' not in data:
            raise RuntimeError(f"File ingest failed: {data}")

        self.log('ingest', page_id=data['id'],
                 description=f'Ingested file: {filename}')
        self.save_version(slug, f'Ingest inicial: {filename}')

        return data


    # ── LLM Wiki methods ──────────────────────────────────────────

    def detect_drift(self, limit: int = 50) -> list:
        """Detecta paginas raw cuyo kb_source_sha256 no coincide con el contenido actual.

        Para paginas con page_type='raw' y kb_source_sha256, recalcula el SHA256
        del body y lo compara con el almacenado.

        Args:
            limit: Maximo de paginas a revisar.

        Returns:
            Lista de paginas con drift detectado.
        """
        if not self._context_id:
            self.orient()

        pages = self.pb.list('brain_pages',
            filter=f"(context='{self._context_id}' && page_type='raw' && kb_source_sha256!='')",
            perPage=limit)

        drifted = []
        for page in pages:
            body = page.get('body', '') or ''
            current_hash = sha256(body)
            stored_hash = page.get('kb_source_sha256', '')
            if current_hash != stored_hash:
                drifted.append({
                    'slug': page['slug'],
                    'title': page['title'],
                    'stored_sha256': stored_hash[:16],
                    'current_sha256': current_hash[:16],
                    'kb_source_url': page.get('kb_source_url', ''),
                })

        self.log('lint', description=f'Drift detect: {len(drifted)} paginas con cambios')
        return drifted

    def validate_frontmatter(self) -> dict:
        """Verifica campos requeridos en todas las paginas no archivadas.

        Cada page_type tiene campos obligatorios:
        - entity: title, body, summary
        - concept: title, body, summary
        - comparison: title, body
        - raw: title, kb_source_url, kb_source_sha256
        - project: title, body
        - query: title, body

        Returns:
            Dict con page_type -> lista de paginas que faltan campos.
        """
        if not self._context_id:
            self.orient()

        required_fields = {
            'entity': ['title', 'body', 'summary'],
            'concept': ['title', 'body', 'summary'],
            'comparison': ['title', 'body'],
            'raw': ['title', 'kb_source_url', 'kb_source_sha256'],
            'project': ['title', 'body'],
            'query': ['title', 'body'],
        }

        pages = self.pb.all('brain_pages',
            filter=f"(context='{self._context_id}' && archived=false)")

        results = {}
        for page in pages:
            pt = page.get('page_type', 'concept')
            req = required_fields.get(pt, ['title'])
            missing = [f for f in req if not page.get(f)]
            if missing:
                if pt not in results:
                    results[pt] = []
                results[pt].append({
                    'slug': page['slug'],
                    'title': page['title'],
                    'missing': missing,
                })

        return results

    def archive_old(self, days: int = 90, dry_run: bool = True) -> dict:
        """Archiva paginas no actualizadas en mas de N dias.

        Args:
            days: Dias sin actualizar para considerar "viejo" (default: 90).
            dry_run: Si True, solo reporta sin archivar.

        Returns:
            Dict con slugs archivados (o candidatos si dry_run).
        """
        if not self._context_id:
            self.orient()

        from datetime import datetime, timezone, timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S') + '.000Z'

        pages = self.pb.all('brain_pages',
            filter=f"(context='{self._context_id}' && archived=false && updated<'{cutoff_str}')",
            sort='updated', perPage=100)

        results = []
        for page in pages:
            entry = {
                'slug': page['slug'],
                'title': page['title'],
                'updated': page.get('updated', ''),
                'page_type': page.get('page_type', ''),
            }
            if not dry_run:
                self.archive_page(page['slug'])
                entry['archived'] = True
            results.append(entry)

        action = 'lint' if dry_run else 'archive'
        self.log(action, description=f'Archive old: {len(results)} candidatos (dry_run={dry_run}, days={days})')
        return {'candidates': results, 'count': len(results), 'dry_run': dry_run}

    def rotate_log(self, max_entries: int = 500) -> dict:
        """Verifica tamano del log. Si excede max_entries, archiva en una
        pagina raw y trunca brain_log.

        Args:
            max_entries: Maximo de entradas antes de rotar.

        Returns:
            Dict con estado del log.
        """
        if not self._context_id:
            self.orient()

        # Contar entradas aproximado
        count_result = self.pb.list('brain_log',
            filter=f"(context='{self._context_id}')",
            perPage=1, skipTotal=False)
        # No tenemos total exacto facil, asi que intentamos all
        all_logs = self.pb.all('brain_log',
            filter=f"(context='{self._context_id}')",
            sort='created', perPage=max_entries + 200)
        total = len(all_logs)

        if total <= max_entries:
            return {'total': total, 'rotated': False, 'reason': 'below threshold'}

        keep = all_logs[-100:] if len(all_logs) > 100 else all_logs
        archive = [l for l in all_logs if l not in keep]

        if not archive:
            return {'total': total, 'rotated': False, 'reason': 'nothing to archive'}

        # Crear snapshot en brain_pages como raw
        import json
        from datetime import datetime, timezone
        archive_body = json.dumps(archive, indent=2, default=str)
        self.create_page(
            title=f"Log Archive {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            body=archive_body,
            page_type='raw',
        )

        # Eliminar entradas archivadas
        for entry in archive:
            self.pb.delete('brain_log', entry['id'])

        return {
            'total_before': total,
            'archived': len(archive),
            'remaining': len(keep),
            'rotated': True,
        }


    # ── Internals ────────────────────────────────────────────────

    def _get_page(self, slug_or_id: str, expand: str = '') -> Optional[dict]:
        """Obtiene página por slug o ID."""
        if not self._context_id:
            self.orient()
        # Buscar por slug primero
        pages = self.pb.list('brain_pages',
            filter=f"(context='{self._context_id}' && slug='{slug_or_id}')",
            perPage=1, expand=expand)
        if pages:
            return pages[0]
        # Intentar por ID
        try:
            return self.pb.get('brain_pages', slug_or_id, expand=expand)
        except Exception:
            return None

    def _slugs_to_ids(self, slugs: list) -> list:
        """Convierte lista de slugs a IDs de página."""
        ids = []
        for slug in slugs:
            page = self._get_page(slug)
            if page and 'id' in page:
                ids.append(page['id'])
        return ids

    def _slugs_from_related(self, page: dict) -> list:
        """Extrae slugs de related_pages expandidas de un registro."""
        expanded = page.get('expand', {}).get('related_pages', []) or []
        if not expanded:
            return []
        if isinstance(expanded[0], dict):
            return [r.get('slug', '') for r in expanded if r.get('slug')]
        return []
