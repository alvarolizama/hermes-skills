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
    brain.ingest_text('## My Note\n\nContent here...', page_type='concept')
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
    """Carga POCKETBRAIN_HOST, POCKETBRAIN_EMAIL, POCKETBRAIN_PASSWORD del .env."""
    env = {}
    env_path = os.path.expanduser('~/.hermes/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def _pocketbrain_pb():
    """Crea un PB autenticado usando POCKETBRAIN_* del .env."""
    env = _load_pocketbrain_env()
    host = env.get('POCKETBRAIN_HOST', 'http://localhost:8090')
    email = env.get('POCKETBRAIN_EMAIL', '')
    password = env.get('POCKETBRAIN_PASSWORD', '')
    return quick_pb(host, email, password)


# ═════════════════════════════════════════════════════════════════════
#  SCHEMA
# ═════════════════════════════════════════════════════════════════════

BRAIN_SCHEMA = {
    "contexts": {
        "name": "contexts",
        "type": "base",
        "fields": [
            {"name": "name", "type": "text", "required": True, "unique": True},
            {"name": "label", "type": "text"},
            {"name": "description", "type": "text"},
            {"name": "schema_config", "type": "json"},
        ],
    },
    "brain_domains": {
        "name": "brain_domains",
        "type": "base",
        "fields": [
            {"name": "name", "type": "text", "required": True},
            {"name": "label", "type": "text"},
            {"name": "brain", "type": "relation", "collectionId": "contexts",
             "cascadeDelete": False, "maxSelect": 1},
        ],
    },
    "brain_tags": {
        "name": "brain_tags",
        "type": "base",
        "fields": [
            {"name": "name", "type": "text", "required": True},
            {"name": "category", "type": "text"},
            {"name": "brain", "type": "relation", "collectionId": "contexts",
             "cascadeDelete": False, "maxSelect": 1},
        ],
    },
    "brain_pages": {
        "name": "brain_pages",
        "type": "base",
        "fields": [
            {"name": "title", "type": "text", "required": True},
            {"name": "slug", "type": "text", "required": True, "unique": True},
            {"name": "brain", "type": "relation", "collectionId": "contexts",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "domain", "type": "relation", "collectionId": "brain_domains",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "page_type", "type": "select", "required": True,
             "values": ["entity", "concept", "comparison", "query", "raw", "project"], "maxSelect": 1},
            {"name": "body", "type": "text"},
            {"name": "summary", "type": "text"},
            {"name": "confidence", "type": "select",
             "values": ["high", "medium", "low"], "maxSelect": 1},
            {"name": "source_url", "type": "url"},
            {"name": "source_sha256", "type": "text"},
            {"name": "contested", "type": "bool"},
            {"name": "contradictions", "type": "text"},
            {"name": "tags", "type": "relation", "collectionId": "brain_tags",
             "cascadeDelete": False, "maxSelect": None},
            {"name": "archived", "type": "bool"},
            {"name": "attachment", "type": "file", "maxSelect": 1, "maxSize": 0},
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
            {"name": "confidence", "type": "text"},
        ],
    },
    "brain_todos": {
        "name": "brain_todos",
        "type": "base",
        "fields": [
            {"name": "title", "type": "text", "required": True},
            {"name": "content", "type": "editor"},
            {"name": "status", "type": "select", "required": True,
             "values": ["backlog", "this week", "today", "in progress", "done", "cancelled"]},
            {"name": "domain", "type": "select", "required": True,
             "values": ["personal", "projects", "bravo"]},
            {"name": "owner", "type": "select", "required": True,
             "values": ["alvaro", "chaos-manager", "project-manager", "bravo-manager", "minion", "alv-bot", "bravo-bot", "ops-bot"]},
            {"name": "comment", "type": "text"},
            {"name": "started_date", "type": "date"},
            {"name": "completed_date", "type": "date"},
            {"name": "cancelled_date", "type": "date"},
            {"name": "brain", "type": "relation", "collectionId": "contexts",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "page", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "goal", "type": "relation", "collectionId": "brain_goals",
             "cascadeDelete": False, "maxSelect": 1},
        ],
    },
    "brain_journal": {
        "name": "brain_journal",
        "type": "base",
        "fields": [
            {"name": "title", "type": "text", "required": True},
            {"name": "body", "type": "text"},
            {"name": "date", "type": "date", "required": True},
            {"name": "brain", "type": "relation", "collectionId": "contexts",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "mood", "type": "select",
             "values": ["great", "meh", "bad"], "maxSelect": 1},
            {"name": "tags", "type": "relation", "collectionId": "brain_tags",
             "cascadeDelete": False, "maxSelect": None},
            {"name": "page", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},
        ],
    },
    "brain_files": {
        "name": "brain_files",
        "type": "base",
        "fields": [
            {"name": "name", "type": "text", "required": True},
            {"name": "page", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "brain", "type": "relation", "collectionId": "contexts",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "file", "type": "file", "maxSelect": 1, "maxSize": 0},
            {"name": "file_type", "type": "select",
             "values": ["pdf", "image", "doc", "sheet", "other"], "maxSelect": 1},
            {"name": "goal", "type": "relation", "collectionId": "brain_goals",
             "cascadeDelete": False, "maxSelect": 1},
        ],
    },
    "brain_deliverables": {
        "name": "brain_deliverables",
        "type": "base",
        "fields": [
            {"name": "title", "type": "text", "required": True},
            {"name": "description", "type": "text"},
            {"name": "page", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "brain", "type": "relation", "collectionId": "contexts",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "file", "type": "file", "maxSelect": 1, "maxSize": 0},
            {"name": "version", "type": "text"},
            {"name": "status", "type": "select",
             "values": ["draft", "review", "final", "archived"], "maxSelect": 1},
            {"name": "milestone", "type": "text"},
            {"name": "tags", "type": "relation", "collectionId": "brain_tags",
             "cascadeDelete": False, "maxSelect": None},
            {"name": "goal", "type": "relation", "collectionId": "brain_goals",
             "cascadeDelete": False, "maxSelect": 1},
        ],
    },
    "brain_reminders": {
        "name": "brain_reminders",
        "type": "base",
        "fields": [
            {"name": "title", "type": "text", "required": True},
            {"name": "content", "type": "text"},
            {"name": "date", "type": "date", "required": True},
            {"name": "time", "type": "text"},
            {"name": "brain", "type": "relation", "collectionId": "contexts",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "page", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "done", "type": "bool"},
            {"name": "done_date", "type": "date"},
        ],
    },
    "brain_goals": {
        "name": "brain_goals",
        "type": "base",
        "fields": [
            {"name": "title", "type": "text", "required": True},
            {"name": "description", "type": "text"},
            {"name": "type", "type": "select", "required": True,
             "values": ["goal", "milestone", "okr"], "maxSelect": 1},
            {"name": "status", "type": "select", "required": True,
             "values": ["planned", "active", "done", "cancelled"], "maxSelect": 1},
            {"name": "deadline", "type": "date"},
            {"name": "brain", "type": "relation", "collectionId": "contexts",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "page", "type": "relation", "collectionId": "brain_pages",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "parent", "type": "relation", "collectionId": "brain_goals",
             "cascadeDelete": False, "maxSelect": 1},
            {"name": "tags", "type": "relation", "collectionId": "brain_tags",
             "cascadeDelete": False, "maxSelect": None},
            {"name": "goal", "type": "relation", "collectionId": "brain_goals",
             "cascadeDelete": False, "maxSelect": 1},
        ],
    },
    "brain_log": {
        "name": "brain_log",
        "type": "base",
        "fields": [
            {"name": "brain", "type": "relation", "collectionId": "contexts",
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

CREATION_ORDER = ["contexts", "brain_domains", "brain_tags", "brain_pages", "brain_goals", "brain_todos", "brain_journal", "brain_files", "brain_deliverables", "brain_reminders", "brain_log", "brain_page_versions"]

# Colecciones con campos self-reference que necesitan PATCH post-creación
SELF_REF_FIELDS = {
    "brain_goals": [
        {"name": "parent", "type": "relation", "collectionId": "brain_goals",
         "cascadeDelete": False, "maxSelect": 1},
        {"name": "goal", "type": "relation", "collectionId": "brain_goals",
         "cascadeDelete": False, "maxSelect": 1},
    ],
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
        contexts = pb.list('contexts', filter="(name='" + context_name + "')")
        if contexts:
            context_id = contexts[0]['id']
        else:
            raise ValueError("Contexto '" + context_name + "' no encontrado")

    # Orden: dependencias primero (hijos antes que padres)
    order = [
        'brain_page_versions',  # depende de brain_pages
        'brain_log',            # depende de brain_pages
        'brain_todos',          # depende de brain_pages, brain_goals
        'brain_deliverables',  # depende de brain_pages
        'brain_files',         # depende de brain_pages
        'brain_reminders',     # depende de brain_pages
        'brain_journal',       # depende de brain_pages
        'brain_goals',         # depende de brain_pages (self-ref parent)
        'brain_pages',         # depende de brain_domains, brain_tags
        'brain_tags',          # depende de contexts
        'brain_domains',       # depende de contexts
    ]

    stats = {}
    for col in order:
        try:
            if context_id:
                # Contar y borrar solo los de este contexto
                records = pb.all(col, filter="(brain='" + context_id + "')", perPage=500)
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

    # Si es limpieza total, también borrar contexts
    if not context_name:
        try:
            count = len(pb.all('contexts', perPage=500))
            pb._request('DELETE', '/api/collections/contexts/truncate')
            stats['contexts'] = count
        except Exception as e:
            stats['contexts'] = 'ERROR: ' + str(e)[:80]

    return stats


def setup_contexts(pb: PB) -> dict:
    """Crea las 9 colecciones del PocketBrain en PocketBase.

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

    def __init__(self, context_name: str, pb: Optional[PB] = None,
                 agent: str = 'chaos-manager', user: str = 'alvaro'):
        self.context_name = context_name
        self.pb = pb or _pocketbrain_pb()
        self.agent = agent
        self.user = user
        self._context_id: Optional[str] = None
        self._schema: Optional[dict] = None
        self._domain_cache: dict = {}   # name → id
        self._tag_cache: dict = {}      # name → id

    # ── Orient ───────────────────────────────────────────────────

    def orient(self) -> dict:
        """Carga el contexto del cerebro: ID, schema, dominios y tags cacheados.

        Llama esto al inicio de cada sesión antes de operar con un cerebro.
        """
        contexts = self.pb.list('contexts', filter=f"(name='{self.context_name}')")
        if not contexts:
            raise ValueError(
                f"Contexto '{self.context_name}' no encontrado. "
                f"Usa create_context() primero."
            )

        context = contexts[0]
        self._context_id = context['id']
        self._schema = context.get('schema_config', {}) or {}

        # Cachear dominios
        self._domain_cache = {}
        for d in self.pb.all('brain_domains',
                             filter=f"(brain='{self._context_id}')"):
            self._domain_cache[d['name']] = d['id']

        # Cachear tags
        self._tag_cache = {}
        for t in self.pb.all('brain_tags',
                             filter=f"(brain='{self._context_id}')"):
            self._tag_cache[t['name']] = t['id']

        # Contar páginas
        page_count = len(self.pb.list('brain_pages',
            filter=f"(brain='{self._context_id}' && archived=false)",
            perPage=1, skipTotal=False))

        return {
            'brain': context,
            'domain_count': len(self._domain_cache),
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
        result = self.pb.create('contexts', {
            'name': self.context_name,
            'label': label,
            'description': description,
            'schema_config': schema_config or default_schema,
        })
        self._context_id = result['id']
        self._schema = schema_config or default_schema
        self.log('setup', description=f'Cerebro "{self.context_name}" creado')
        return result

    # ── Domain management ────────────────────────────────────────

    def get_or_create_domain(self, name: str, label: str = '') -> str:
        """Obtiene el ID de un dominio, creándolo si no existe."""
        if name in self._domain_cache:
            return self._domain_cache[name]

        existing = self.pb.list('brain_domains',
            filter=f"(name='{name}' && brain='{self._context_id}')")
        if existing:
            self._domain_cache[name] = existing[0]['id']
            return existing[0]['id']

        result = self.pb.create('brain_domains', {
            'name': name,
            'label': label or name,
            'brain': self._context_id,
        })
        self._domain_cache[name] = result['id']
        return result['id']

    # ── Tag management ───────────────────────────────────────────

    def get_or_create_tag(self, name: str, category: str = '') -> str:
        """Obtiene el ID de un tag, creándolo si no existe."""
        if name in self._tag_cache:
            return self._tag_cache[name]

        existing = self.pb.list('brain_tags',
            filter=f"(name='{name}' && brain='{self._context_id}')")
        if existing:
            self._tag_cache[name] = existing[0]['id']
            return existing[0]['id']

        result = self.pb.create('brain_tags', {
            'name': name,
            'category': category,
            'brain': self._context_id,
        })
        self._tag_cache[name] = result['id']
        return result['id']

    # ── Page CRUD ────────────────────────────────────────────────

    def create_page(self, title: str, body: str, page_type: str = 'concept',
                    domain: Optional[str] = None, tags: Optional[list] = None,
                    summary: str = '', confidence: Optional[str] = None,
                    source_url: str = '', source_sha256: str = '',
                    contested: bool = False, contradictions: str = '') -> dict:
        """Crea una página de conocimiento.

        Args:
            title: Título de la página
            body: Contenido en markdown con [[wikilinks]]
            page_type: 'entity', 'concept', 'comparison', 'query', 'raw'
            domain: Nombre del dominio (se crea si no existe)
            tags: Lista de nombres de tags (se crean si no existen)
            summary: Resumen (default: primeras 200 chars del body)
            confidence: 'high', 'medium', 'low'
            source_url: URL original si es raw
            source_sha256: Hash del contenido raw
            contested: ¿Tiene contradicciones?
            contradictions: Slugs de páginas en conflicto (coma-separados)
            related_slugs: Lista de slugs de páginas relacionadas
        """
        if not self._context_id:
            self.orient()

        slug = slugify(title)

        data = {
            'title': title,
            'slug': slug,
            'brain': self._context_id,
            'page_type': page_type,
            'body': body,
            'summary': summary or body[:200].split('\n')[0] if body else '',
            'contested': contested,
            'contradictions': contradictions,
            'archived': False,
        }

        if domain:
            data['domain'] = self.get_or_create_domain(domain)
        if confidence:
            data['confidence'] = confidence
        if source_url:
            data['source_url'] = source_url
        if source_sha256:
            data['source_sha256'] = source_sha256
        if tags:
            data['tags'] = [self.get_or_create_tag(t) for t in tags]

        page = self.pb.create('brain_pages', data)
        self.log('create', page_id=page.get('id'), description=f'Created: {title}')
        self.save_version(slug, 'Initial version')
        return page

    def update_page(self, slug_or_id: str, **updates) -> dict:
        """Actualiza una página existente.

        Args:
            slug_or_id: Slug o ID de la página
            **updates: Campos a actualizar. 'domain' acepta string (nombre).
                       'tags' acepta lista de nombres. 
                       'related_slugs' acepta lista de slugs.
        """
        page = self._get_page(slug_or_id)
        if not page:
            raise ValueError(f"Página '{slug_or_id}' no encontrada")

        # Resolver nombres a IDs
        if 'domain' in updates and isinstance(updates['domain'], str):
            updates['domain'] = self.get_or_create_domain(updates.pop('domain'))
        if 'tags' in updates and updates['tags']:
            updates['tags'] = [self.get_or_create_tag(t) for t in updates['tags']]

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

    def get_page(self, slug: str, expand: str = 'domain,tags,related_pages') -> Optional[dict]:
        """Obtiene una página por slug con relaciones expandidas."""
        return self._get_page(slug, expand)

    def list_pages(self, page_type: Optional[str] = None,
                   domain: Optional[str] = None,
                   tag: Optional[str] = None,
                   include_archived: bool = False,
                   sort: str = '', per_page: int = 50) -> list:
        """Lista páginas con filtros opcionales."""
        if not self._context_id:
            self.orient()
        filters = [f"(brain='{self._context_id}')"]
        if not include_archived:
            filters.append("(archived=false)")
        if page_type:
            filters.append(f"(page_type='{page_type}')")
        if domain:
            # Resolver nombre de dominio a ID
            domain_id = self.get_or_create_domain(domain)
            filters.append(f"(domain='{domain_id}')")
        if tag:
            # Resolver nombre de tag a ID
            tag_id = self.get_or_create_tag(tag)
            filters.append(f"(tags?='{tag_id}')")

        params = {
            'filter': "&&".join(filters),
            'perPage': per_page,
            'expand': 'domain,tags',
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
            filter=f"(brain='{self._context_id}' && archived=false)")

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
                    source_url: str = '',
                    domain: Optional[str] = None,
                    tags: Optional[list] = None) -> dict:
        """Ingesta texto crudo como página.

        Calcula source_sha256 automáticamente si page_type='raw'.
        """
        if not self._context_id:
            self.orient()

        title = title or f"Ingest {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        return self.create_page(
            title=title,
            body=text,
            page_type=page_type,
            domain=domain,
            tags=tags,
            source_url=source_url,
            source_sha256=sha256(text) if page_type == 'raw' else '',
        )

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
            'brain': self._context_id,
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
        filters = [f"(brain='{self._context_id}')"]
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
            filter=f"(brain='{self._context_id}' && archived=false)",
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
            if page.get('confidence') == 'low':
                report['low_confidence'].append(slug)

            # Contested
            if page.get('contested'):
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

        # ── Summary ──
        report['summary'] = {
            'orphans': len(report['orphans']),
            'broken_links': len(report['broken_links']),
            'low_confidence': len(report['low_confidence']),
            'contested': len(report['contested_pages']),
            'invalid_tags': len(report['invalid_tags']),
            'oversized': len(report['oversized_pages']),
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
        self.pb.update('brains', self._context_id,
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
            filter=f"(brain='{self._context_id}' && archived=false)",
            sort='title')

        index = {
            'brain': self.context_name,
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
                'confidence': p.get('confidence'),
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
            'confidence': page.get('confidence', ''),
        })

    def get_history(self, slug: str, limit: int = 20) -> list:
        """Devuelve el historial de versiones de una página (más reciente primero)."""
        page = self._get_page(slug)
        if not page:
            return []
        return self.pb.list('brain_page_versions',
            filter=f"(page='{page['id']}')", sort='-version', perPage=limit)

    # ── Todos ───────────────────────────────────────────────────

    def create_todo(self, title: str, domain: str,
                    page_slug: Optional[str] = None,
                    goal_id: Optional[str] = None,
                    content: str = "",
                    status: str = "backlog",
                    owner: str = "alvaro") -> dict:
        if not self._context_id:
            self.orient()
        data = {'title': title, 'content': content, 'status': status,
                'domain': domain, 'owner': owner, 'brain': self._context_id}
        if page_slug:
            page = self._get_page(page_slug)
            if page:
                data['page'] = page['id']
        if goal_id:
            data['goal'] = goal_id
        todo = self.pb.create('brain_todos', data)
        self.log('create', description='Todo: ' + title)
        return todo

    def todos(self, status: Optional[str] = None,
              domain: Optional[str] = None,
              owner: Optional[str] = None,
              goal_id: Optional[str] = None,
              limit: int = 50) -> list:
        if not self._context_id:
            self.orient()
        filters = ["(brain='" + self._context_id + "')"]
        if status: filters.append("(status='" + status + "')")
        if domain: filters.append("(domain='" + domain + "')")
        if owner: filters.append("(owner='" + owner + "')")
        if goal_id: filters.append("(goal='" + goal_id + "')")
        return self.pb.list('brain_todos', filter="&&".join(filters),
                            perPage=limit, expand='page,goal')

    def update_todo(self, todo_id: str, **updates) -> dict:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        new_status = updates.get('status')
        if new_status == 'in progress':
            updates['started_date'] = updates.get('started_date', now)
        elif new_status == 'done':
            updates['completed_date'] = updates.get('completed_date', now)
        elif new_status == 'cancelled':
            updates['cancelled_date'] = updates.get('cancelled_date', now)
        if 'page_slug' in updates:
            slug = updates.pop('page_slug')
            if slug:
                page = self._get_page(slug)
                if page:
                    updates['page'] = page['id']
        result = self.pb.update('brain_todos', todo_id, updates)
        desc = 'Todo updated: ' + str(list(updates.keys()))
        self.log('update', description=desc)
        return result

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
        """Obtiene o crea una entrada del diario para una fecha.

        Args:
            date_val: Fecha (string 'YYYY-MM-DD', date, o datetime).

        Returns:
            El registro de brain_journal (creado si no existe).
        """
        if not self._context_id:
            self.orient()

        date_str = self._journal_date_str(date_val)
        title = "Journal: " + date_str

        # Buscar si ya existe
        existing = self.pb.list('brain_journal',
            filter="(brain='" + self._context_id + "' && date='" + date_str + " 00:00:00.000Z')",
            perPage=1)
        if existing:
            return existing[0]

        # Crear nueva entrada
        entry = self.pb.create('brain_journal', {
            'title': title,
            'body': '',
            'date': date_str + ' 00:00:00.000Z',
            'brain': self._context_id,
        })
        self.log('create', description='Journal entry: ' + date_str)
        return entry

    def journal_write(self, body: str, date_val=None,
                      mood: Optional[str] = None,
                      tags: Optional[list] = None,
                      append: bool = False) -> dict:
        """Escribe en el diario.

        Args:
            body: Contenido markdown a escribir.
            date_val: Fecha (default: hoy).
            mood: 'great', 'meh', o 'bad' (opcional).
            tags: Lista de nombres de tags (opcional).
            append: Si True, agrega al body existente en vez de reemplazar.

        Returns:
            El registro actualizado.
        """
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

        result = self.pb.update('brain_journal', entry['id'], updates)
        self.log('update', description='Journal write: ' + self._journal_date_str(date_val))
        return result

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

        return self.pb.list('brain_journal',
            filter="(brain='" + self._context_id + "' && date>='" + d_from + " 00:00:00.000Z' && date<='" + d_to + " 00:00:00.000Z')",
            sort='date',
            perPage=100)

    def journal_search(self, query: str, limit: int = 20) -> list:
        """Busca en todas las entradas del diario.

        Divide el query en palabras y busca cada una de forma
        case-insensitive en title y body. Rankea por relevancia.
        """
        if not self._context_id:
            self.orient()

        candidates = self.pb.all('brain_journal',
            filter="(brain='" + self._context_id + "')")

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
        """Adjunta un archivo a una pagina."""
        import subprocess

        if not self._context_id:
            self.orient()

        page = self._get_page(page_slug)
        if not page:
            raise ValueError("Pagina '" + page_slug + "' no encontrada")

        name = name or os.path.basename(filepath)
        host = self.pb.host
        token = self.pb.get_token()
        url = host + "/api/collections/brain_files/records"
        auth = "Authorization: Bearer " + token

        args = [
            "curl", "-s", "-X", "POST", url,
            "-H", auth,
            "-F", "name=" + name,
            "-F", "page=" + page["id"],
            "-F", "brain=" + self._context_id,
            "-F", "file_type=" + file_type,
            "-F", "file=@" + filepath,
        ]

        result = subprocess.run(args, capture_output=True, text=True)
        data = json.loads(result.stdout)

        if "id" not in data:
            raise RuntimeError("File attach failed: " + str(data))

        self.log("create", page_id=page["id"],
                 description="Attached file: " + name)
        return data


    def list_files(self, page_slug: str) -> list:
        """Lista archivos adjuntos a una pagina."""
        page = self._get_page(page_slug)
        if not page:
            return []
        return self.pb.list("brain_files",
            filter="(page='" + page["id"] + "')",
            perPage=100)

    def delete_file(self, file_id: str) -> bool:
        """Elimina un archivo adjunto."""
        return self.pb.delete("brain_files", file_id)

    # ── Deliverables ─────────────────────────────────────────────

    def create_deliverable(self, project_slug: str, filepath: str,
                           title: str, version: str = 'v1',
                           status: str = 'draft',
                           description: str = '',
                           milestone: str = '',
                           tags: Optional[list] = None) -> dict:
        """Crea un entregable versionado para un proyecto.

        Args:
            project_slug: Slug del proyecto (page_type: project).
            filepath: Ruta al archivo en disco.
            title: Nombre del entregable.
            version: Version (ej. 'v1', 'draft-2', 'final').
            status: 'draft', 'review', 'final', 'archived'.
            description: Descripcion del entregable.
            milestone: Fase del proyecto (ej. 'MVP', 'Fase 1').
            tags: Lista de nombres de tags.
        """
        import subprocess

        if not self._context_id:
            self.orient()

        page = self._get_page(project_slug)
        if not page:
            raise ValueError("Proyecto '" + project_slug + "' no encontrado")

        host = self.pb.host
        token = self.pb.get_token()
        url = host + "/api/collections/brain_deliverables/records"
        auth = "Authorization: Bearer %s" % token

        args = [
            "curl", "-s", "-X", "POST", url,
            "-H", auth,
            "-F", "title=" + title,
            "-F", "page=" + page["id"],
            "-F", "brain=" + self._context_id,
            "-F", "version=" + version,
            "-F", "status=" + status,
            "-F", "description=" + description,
            "-F", "milestone=" + milestone,
            "-F", "file=@" + filepath,
        ]

        if tags:
            for t in tags:
                tid = self.get_or_create_tag(t)
                args += ["-F", "tags=" + tid]

        result = subprocess.run(args, capture_output=True, text=True)
        data = json.loads(result.stdout)

        if "id" not in data:
            raise RuntimeError("Deliverable create failed: " + str(data))

        self.log("create", page_id=page["id"],
                 description="Deliverable: " + title + " " + version)
        return data

    def list_deliverables(self, project_slug: str,
                          status: Optional[str] = None) -> list:
        """Lista entregables de un proyecto."""
        page = self._get_page(project_slug)
        if not page:
            return []

        f = "(page='" + page["id"] + "')"
        if status:
            f = "(page='" + page["id"] + "' && status='" + status + "')"

        return self.pb.list("brain_deliverables", filter=f, perPage=100)

    def version_deliverable(self, deliverable_id: str,
                            filepath: str, new_version: str) -> dict:
        """Sube una nueva version de un entregable.

        Crea un NUEVO registro con el mismo titulo pero nueva version.
        La version anterior se marca como 'archived'.
        """
        import subprocess

        old = self.pb.get("brain_deliverables", deliverable_id)
        if not old:
            raise ValueError("Deliverable no encontrado")

        # Archivar version anterior
        self.pb.update("brain_deliverables", deliverable_id, {"status": "archived"})

        # Crear nueva version
        host = self.pb.host
        token = self.pb.get_token()
        url = host + "/api/collections/brain_deliverables/records"
        auth = "Authorization: Bearer %s" % token

        args = [
            "curl", "-s", "-X", "POST", url,
            "-H", auth,
            "-F", "title=" + old.get("title", ""),
            "-F", "page=" + old.get("page", ""),
            "-F", "brain=" + old.get("brain", self._context_id or ""),
            "-F", "version=" + new_version,
            "-F", "status=draft",
            "-F", "description=" + old.get("description", ""),
            "-F", "milestone=" + old.get("milestone", ""),
            "-F", "file=@" + filepath,
        ]

        result = subprocess.run(args, capture_output=True, text=True)
        data = json.loads(result.stdout)

        if "id" not in data:
            raise RuntimeError("Version failed: " + str(data))

        self.log("create", page_id=old.get("page"),
                 description="Deliverable v" + new_version + ": " + old.get("title", ""))
        return data

    def update_deliverable(self, deliverable_id: str, **updates) -> dict:
        """Actualiza metadata de un entregable (status, milestone, etc.)."""
        return self.pb.update("brain_deliverables", deliverable_id, updates)

    # ── Goals / Milestones / OKRs ──────────────────────────────

    def create_goal(self, title: str, type: str = 'goal',
                    project_slug: Optional[str] = None,
                    description: str = '',
                    deadline: str = '',
                    parent_id: Optional[str] = None,
                    status: str = 'planned') -> dict:
        """Crea un goal, milestone u OKR.

        Args:
            title: Nombre.
            type: 'goal', 'milestone', 'okr'.
            project_slug: Slug del proyecto asociado.
            description: Detalle.
            deadline: Fecha limite (YYYY-MM-DD) - obligatorio para milestones.
            parent_id: ID del OKR padre (para key results).
            status: 'planned', 'active', 'done', 'cancelled'.
        """
        if not self._context_id:
            self.orient()

        data = {
            'title': title,
            'type': type,
            'description': description,
            'status': status,
            'brain': self._context_id,
        }

        if deadline:
            data['deadline'] = deadline + ' 00:00:00.000Z'
        if project_slug:
            project = self._get_page(project_slug)
            if project:
                data['page'] = project['id']
        if parent_id:
            data['parent'] = parent_id

        goal = self.pb.create('brain_goals', data)
        self.log('create', description='Goal: ' + title)
        return goal

    def list_goals(self, project_slug: Optional[str] = None,
                   type: Optional[str] = None,
                   status: Optional[str] = None) -> list:
        """Lista goals con filtros opcionales."""
        if not self._context_id:
            self.orient()

        filters = ["(brain='" + self._context_id + "')"]
        if type:
            filters.append("(type='" + type + "')")
        if status:
            filters.append("(status='" + status + "')")

        goals = self.pb.list('brain_goals',
            filter="&&".join(filters), perPage=200, expand='parent')

        if project_slug:
            page = self._get_page(project_slug)
            if page:
                goals = [g for g in goals if g.get('page') == page['id']]

        return goals

    def complete_goal(self, goal_id: str, retrospective: str = '') -> dict:
        if retrospective:
            self.pb.update('brain_goals', goal_id, {'status': 'done', 'retrospective': retrospective})
        else:
            self.pb.update('brain_goals', goal_id, {'status': 'done'})
        self.log('update', description='Goal completed: ' + goal_id)
        return self.pb.get('brain_goals', goal_id)

    def cancel_goal(self, goal_id: str, retrospective: str = '') -> dict:
        if retrospective:
            self.pb.update('brain_goals', goal_id, {'status': 'cancelled', 'retrospective': retrospective})
        else:
            self.pb.update('brain_goals', goal_id, {'status': 'cancelled'})
        self.log('update', description='Goal cancelled: ' + goal_id)
        return self.pb.get('brain_goals', goal_id)

    def update_goal(self, goal_id: str, **updates) -> dict:
        """Actualiza un goal (status, deadline, etc.)."""
        if 'deadline' in updates and updates['deadline']:
            if '00:00:00' not in str(updates['deadline']):
                updates['deadline'] = str(updates['deadline']) + ' 00:00:00.000Z'
        return self.pb.update('brain_goals', goal_id, updates)

    def get_goal_tree(self, project_slug: Optional[str] = None) -> list:
        """Devuelve goals anidados (OKRs con sus key results)."""
        goals = self.list_goals(project_slug=project_slug)
        goal_map = {g['id']: g for g in goals}

        # Build tree
        roots = []
        for g in goals:
            g['children'] = []
            parent_id = g.get('parent')
            if parent_id and parent_id in goal_map:
                goal_map[parent_id].setdefault('children', []).append(g)
            elif not parent_id:
                roots.append(g)

        # Sort: milestones by deadline
        for g in goals:
            if g.get('children'):
                g['children'].sort(key=lambda x: x.get('title', ''))

        return roots


    def create_reminder(self, title: str, date: str, time: str = '',
                        content: str = '', page_slug: Optional[str] = None) -> dict:
        """Crea un recordatorio."""
        if not self._context_id: self.orient()
        data = {'title': title, 'date': date + ' 00:00:00.000Z', 'time': time,
                'content': content, 'brain': self._context_id, 'done': False}
        if page_slug:
            page = self._get_page(page_slug)
            if page: data['page'] = page['id']
        r = self.pb.create('brain_reminders', data)
        self.log('create', description='Reminder: ' + title)
        return r

    def reminders(self, done: Optional[bool] = None, date: str = '',
                  page_slug: str = '') -> list:
        """Lista recordatorios. date='today' para hoy."""
        if not self._context_id: self.orient()
        f = ["(brain='" + self._context_id + "')"]
        if done is not None: f.append("(done=" + str(done).lower() + ")")
        if date:
            from datetime import date as dt
            ds = dt.today().strftime('%Y-%m-%d') if date == 'today' else date
            f.append("(date='" + ds + " 00:00:00.000Z')")
        return self.pb.list('brain_reminders', filter="&&".join(f), perPage=100, sort='date,time', expand='page')

    def complete_reminder(self, reminder_id: str) -> dict:
        """Marca un recordatorio como done."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        return self.pb.update('brain_reminders', reminder_id, {'done': True, 'done_date': now})

    # ── File ingest ──────────────────────────────────────────────

    def ingest_file(self, filepath: str, title: str = '',
                    domain: Optional[str] = None,
                    tags: Optional[list] = None,
                    source_url: str = '') -> dict:
        """Ingesta un archivo (PDF, TXT, etc.) al cerebro.

        Args:
            filepath: Ruta al archivo en disco.
            title: Título (default: nombre del archivo).
            domain: Dominio opcional.
            tags: Tags opcionales.
            source_url: URL original si aplica.

        Returns:
            El registro creado en brain_pages.

        El archivo se sube como attachment. El body se deja vacío
        inicialmente — luego se llena con el texto extraído.
        """
        import subprocess

        if not self._context_id:
            self.orient()

        filename = os.path.basename(filepath)
        title = title or os.path.splitext(filename)[0]
        slug = slugify(title)
        file_hash = sha256_file(filepath)

        # Resolver domain y tags a IDs
        domain_id = self.get_or_create_domain(domain) if domain else ''
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
            "-F", f"brain={self._context_id}",
            "-F", "page_type=raw",
            "-F", f"source_sha256={file_hash}",
            "-F", f"attachment=@{filepath}",
        ]
        if domain_id:
            args += ["-F", f"domain={domain_id}"]
        if source_url:
            args += ["-F", f"source_url={source_url}"]
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

    # ── Internals ────────────────────────────────────────────────

    def _get_page(self, slug_or_id: str, expand: str = '') -> Optional[dict]:
        """Obtiene página por slug o ID."""
        if not self._context_id:
            self.orient()
        # Buscar por slug primero
        pages = self.pb.list('brain_pages',
            filter=f"(brain='{self._context_id}' && slug='{slug_or_id}')",
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
            if page:
                ids.append(page['id'])
        return ids
