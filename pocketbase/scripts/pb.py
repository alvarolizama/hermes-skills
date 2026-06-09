"""
PocketBase helper library for Hermes agents.
=============================================

Lee automaticamente de las variables de entorno:
  POCKETBASE_HOST, POCKETBASE_EMAIL, POCKETBASE_PASSWORD

Uso desde execute_code:
    import sys, os
    sys.path.insert(0, os.path.expanduser(
        '~/.hermes/skills/productivity/pocketbase/scripts'))
    from pb import PB
    pb = PB()
    pb.auth()  # una vez
    pages = pb.list('wiki_pages', filter="page_type='concept'")
    pb.create('wiki_pages', {'title': 'Mi pagina', 'slug': 'mi-pagina', ...})
"""

import os
import subprocess
import json
import re
from datetime import datetime, timezone
from typing import Any, Optional


def _load_env(path: str = None) -> None:
    """Carga variables de ~/.hermes/.env si no están ya en el entorno."""
    if os.environ.get('POCKETBASE_HOST'):
        return  # ya están cargadas
    path = path or os.path.expanduser('~/.hermes/.env')
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, val = line.partition('=')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


# Cargar env vars al importar el módulo
_load_env()


# ─────────────────────────────────────────────────────────────────────
#  CLIENTE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────

class PB:
    """Cliente PocketBase con configuración via variables de entorno.

    Args:
        host:    URL del servidor (default: $POCKETBASE_HOST)
        email:   Email del superusuario (default: $POCKETBASE_EMAIL)
        password: Password del superusuario (default: $POCKETBASE_PASSWORD)
    """

    def __init__(
        self,
        host: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.host = host or os.environ.get('POCKETBASE_HOST', 'http://localhost:8090')
        self.email = email or os.environ.get('POCKETBASE_EMAIL', '')
        self.password = password or os.environ.get('POCKETBASE_PASSWORD', '')
        self._token: Optional[str] = None

    # ── Auth ────────────────────────────────────────────────────────

    def auth(self) -> str:
        """Autentica como superusuario y guarda el token internamente.
        
        Returns:
            El token JWT.
        """
        if not self.email or not self.password:
            raise ValueError(
                "Faltan credenciales. Revisa POCKETBASE_EMAIL y POCKETBASE_PASSWORD en .env")
        
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{self.host}/api/collections/_superusers/auth-with-password",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"identity": self.email, "password": self.password})
        ], capture_output=True, text=True)
        
        data = json.loads(result.stdout)
        if 'token' not in data:
            raise RuntimeError(f"Auth falló: {data}")
        self._token = data['token']
        return self._token

    def get_token(self) -> str:
        """Devuelve el token, auto-autenticando si es necesario."""
        if not self._token:
            self.auth()
        return self._token

    def refresh_token(self) -> str:
        """Refresca el token actual."""
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{self.host}/api/collections/_superusers/auth-refresh",
            "-H", f"Authorization: Bearer {self.get_token()}"
        ], capture_output=True, text=True)
        data = json.loads(result.stdout)
        self._token = data['token']
        return self._token

    def impersonate(self, user_id: str, duration: int = 3600) -> str:
        """Genera token de impersonación para un usuario.
        
        Args:
            user_id: ID del usuario a impersonar
            duration: Duración en segundos (default: 1 hora)
        
        Returns:
            Token de impersonación (no-refrescable).
        """
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{self.host}/api/collections/users/impersonate",
            "-H", f"Authorization: Bearer {self.get_token()}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"duration": duration}),
            "--data-urlencode", f"userId={user_id}"
        ], capture_output=True, text=True)
        data = json.loads(result.stdout)
        return data['token']

    # ── Requests internos ───────────────────────────────────────────

    def _request(self, method: str, path: str, data: Any = None, params: Optional[dict] = None) -> Any:
        """Ejecuta un request HTTP a la API de PocketBase.

        Auto-autentica si es necesario via get_token().
        """
        import urllib.parse
        url = f"{self.host}{path}"
        if params:
            qs = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items())
            url += f"?{qs}"

        args = ["curl", "-s", "-X", method, url]
        args += ["-H", f"Authorization: Bearer {self.get_token()}"]
        if data is not None:
            args += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]

        result = subprocess.run(args, capture_output=True, text=True)
        if not result.stdout.strip():
            return {"success": result.returncode == 0}
        return json.loads(result.stdout)

    # ── Health ───────────────────────────────────────────────────────

    def health(self) -> dict:
        """Verifica que la instancia de PocketBase esté viva."""
        return self._request("GET", "/api/health")

    # ── Collections ─────────────────────────────────────────────────

    def list_collections(self, **params) -> list:
        """Lista todas las colecciones (requiere superusuario)."""
        result = self._request("GET", "/api/collections", params=params or None)
        return result.get('items', result) if isinstance(result, dict) else result

    def get_collection(self, name_or_id: str) -> dict:
        """Obtiene una colección por nombre o ID."""
        return self._request("GET", f"/api/collections/{name_or_id}")

    def create_collection(
        self,
        name: str,
        fields: list,
        collection_type: str = "base",
        list_rule: Optional[str] = None,
        view_rule: Optional[str] = None,
        create_rule: Optional[str] = None,
        update_rule: Optional[str] = None,
        delete_rule: Optional[str] = None,
    ) -> dict:
        """Crea una nueva colección (superusuario).
        
        Args:
            name: Nombre de la colección
            fields: Lista de campos (dicts con name, type, required, etc.)
            collection_type: 'base' | 'auth'
            *_rule: Reglas de seguridad (null = solo superusuarios)
        """
        body = {
            "name": name,
            "type": collection_type,
            "fields": fields,
            "listRule": list_rule,
            "viewRule": view_rule,
            "createRule": create_rule,
            "updateRule": update_rule,
            "deleteRule": delete_rule,
        }
        return self._request("POST", "/api/collections", data=body)

    def update_collection(self, name_or_id: str, data: dict) -> dict:
        """Actualiza una colección."""
        return self._request("PATCH", f"/api/collections/{name_or_id}", data=data)

    def delete_collection(self, name_or_id: str) -> dict:
        """Elimina una colección."""
        return self._request("DELETE", f"/api/collections/{name_or_id}")

    def truncate_collection(self, name_or_id: str) -> dict:
        """Borra todos los registros de una colección."""
        return self._request("DELETE", f"/api/collections/{name_or_id}/truncate")

    def import_collections(self, collections: list, delete_missing: bool = False) -> dict:
        """Importa/actualiza múltiples colecciones en batch."""
        return self._request("PUT", "/api/collections/import", data={
            "collections": collections,
            "deleteMissing": delete_missing,
        })

    # ── Records ─────────────────────────────────────────────────────

    def list(self, collection: str, **params) -> list:
        """Lista registros con filtros, sort y paginación opcionales.
        
        Query params útiles:
            filter: str  (ej. "(title~'abc' && status='published')")
            sort: str    (ej. "-created" para DESC)
            page: int    (default: 1)
            perPage: int (default: 30)
            expand: str  (ej. "domain,tags" para relaciones)
            fields: str  (ej. "id,title,slug" para solo ciertos campos)
            skipTotal: bool (performance)
        """
        result = self._request("GET", f"/api/collections/{collection}/records", params=params or None)
        return result.get('items', []) if isinstance(result, dict) else []

    def all(self, collection: str, **params) -> list:
        """Lista TODOS los registros (maneja paginación automáticamente)."""
        items = []
        page = 1
        per_page = 200
        while True:
            batch = self._request("GET", f"/api/collections/{collection}/records",
                                 params={**params, "page": page, "perPage": per_page})
            batch_items = batch.get('items', [])
            if not batch_items:
                break
            items.extend(batch_items)
            total_pages = batch.get('totalPages', 1)
            if page >= total_pages:
                break
            page += 1
        return items

    def get(self, collection: str, id: str, expand: Optional[str] = None) -> dict:
        """Obtiene un registro por ID.
        
        Args:
            expand: Relaciones a expandir (ej. "domain,tags,related_pages")
        """
        params = {"expand": expand} if expand else None
        return self._request("GET", f"/api/collections/{collection}/records/{id}", params=params)

    def create(self, collection: str, data: dict) -> dict:
        """Crea un registro."""
        return self._request("POST", f"/api/collections/{collection}/records", data=data)

    def update(self, collection: str, id: str, data: dict) -> dict:
        """Actualiza un registro."""
        return self._request("PATCH", f"/api/collections/{collection}/records/{id}", data=data)

    def delete(self, collection: str, id: str) -> bool:
        """Elimina un registro. Returns True si éxito."""
        result = self._request("DELETE", f"/api/collections/{collection}/records/{id}")
        return isinstance(result, dict) and result.get('success', True)

    # ── Batch ────────────────────────────────────────────────────────

    def batch(self, requests: list) -> dict:
        """Ejecuta múltiples operaciones en una transacción.
        
        Cada request: {"method": "POST"|"PATCH"|"DELETE",
                       "url": "/api/collections/posts/records",
                       "body": {...}}  # opcional para POST/PATCH
        """
        return self._request("POST", "/api/batch", data={"requests": requests})

    # ── Files ────────────────────────────────────────────────────────

    def get_file_url(self, collection: str, record_id: str, filename: str, thumb: Optional[str] = None) -> str:
        """Devuelve la URL pública de un archivo."""
        url = f"{self.host}/api/files/{collection}/{record_id}/{filename}"
        if thumb:
            url += f"?thumb={thumb}"
        return url

    # ── Logs (superusuario) ─────────────────────────────────────────

    def list_logs(self, **params) -> list:
        """Lista logs del sistema."""
        result = self._request("GET", "/api/logs", params=params or None)
        return result.get('items', []) if isinstance(result, dict) else []

    # ── Backups (superusuario) ──────────────────────────────────────

    def list_backups(self) -> list:
        result = self._request("GET", "/api/backups")
        return result if isinstance(result, list) else []

    def create_backup(self) -> dict:
        return self._request("POST", "/api/backups")

    def restore_backup(self, name: str) -> dict:
        return self._request("PUT", "/api/backups/restore", data={"name": name})

    def delete_backup(self, name: str) -> dict:
        return self._request("DELETE", f"/api/backups/{name}")

    # ── Settings (superusuario) ─────────────────────────────────────

    def get_settings(self) -> dict:
        return self._request("GET", "/api/settings")

    def update_settings(self, data: dict) -> dict:
        return self._request("PATCH", "/api/settings", data=data)


# ─────────────────────────────────────────────────────────────────────
#  QUICK SHORTCUT
# ─────────────────────────────────────────────────────────────────────

def quick_pb() -> PB:
    """Crea y autentica un cliente PB en un solo paso.
    
    Uso:
        from pb import quick_pb
        pb = quick_pb()
        records = pb.list('mi_coleccion')
    """
    pb = PB()
    pb.auth()
    return pb
