"""
Cliente Híbrido para DevDocs
Soporta múltiples fuentes: Local (Docker) → Caché → Remoto (API)
"""
import os
import json
from typing import Optional
from enum import Enum
import httpx

from .cache import DevDocsCache


class DataSource(Enum):
    """Fuentes de datos disponibles"""
    LOCAL = "local"      # DevDocs Docker local (más rápido)
    CACHE = "cache"      # Caché en disco
    REMOTE = "remote"    # API remota de DevDocs


class HybridMode(Enum):
    """Modos de operación del cliente híbrido"""
    AUTO = "auto"              # Local → Cache → Remote (fallback automático)
    LOCAL_ONLY = "local_only"  # Solo local, falla si no disponible
    REMOTE_ONLY = "remote_only"  # Solo remoto (comportamiento original)
    OFFLINE = "offline"        # Solo cache, nunca hace requests


class HybridClient:
    """
    Cliente híbrido que puede obtener documentación de múltiples fuentes.
    
    Prioridad por defecto (modo AUTO):
    1. DevDocs local (Docker) - ~5ms latencia
    2. Caché en disco - instantáneo
    3. API remota - ~300ms latencia
    
    Configuración via variables de entorno:
    - DEVDOCS_LOCAL_URL: URL del servidor DevDocs local (default: http://localhost:9292)
    - DEVDOCS_MODE: auto, local_only, remote_only, offline
    """
    
    # URLs de la API remota de DevDocs
    REMOTE_DOCS_URL = "https://devdocs.io/docs.json"
    REMOTE_INDEX_URL = "https://documents.devdocs.io/{tech}/index.json"
    REMOTE_PAGE_URL = "https://documents.devdocs.io/{tech}/{path}.html"
    
    # Endpoints del servidor DevDocs local
    LOCAL_DOCS_URL = "{base}/docs"
    LOCAL_INDEX_URL = "{base}/docs/{tech}/index.json"
    LOCAL_PAGE_URL = "{base}/docs/{tech}/{path}.html"
    
    def __init__(
        self,
        cache: Optional[DevDocsCache] = None,
        local_url: Optional[str] = None,
        mode: Optional[HybridMode] = None
    ):
        """
        Inicializa el cliente híbrido.
        
        Args:
            cache: Instancia de caché (crea una por defecto)
            local_url: URL del servidor DevDocs local
            mode: Modo de operación
        """
        self.cache = cache or DevDocsCache()
        
        # Configuración desde env o parámetros
        self.local_url = local_url or os.getenv("DEVDOCS_LOCAL_URL", "http://localhost:9292")
        
        mode_str = os.getenv("DEVDOCS_MODE", "auto").lower()
        self.mode = mode or HybridMode(mode_str) if mode_str in [m.value for m in HybridMode] else HybridMode.AUTO
        
        # Cliente HTTP con timeouts diferenciados
        self.local_client = httpx.Client(timeout=5.0, follow_redirects=True)  # Local rápido
        self.remote_client = httpx.Client(timeout=60.0, follow_redirects=True)  # Remoto más tiempo
        
        # Estado
        self._local_available: Optional[bool] = None
        self._last_source: Optional[DataSource] = None
    
    def __del__(self):
        """Cerrar clientes HTTP"""
        if hasattr(self, 'local_client'):
            self.local_client.close()
        if hasattr(self, 'remote_client'):
            self.remote_client.close()
    
    # ─────────────────────────────────────────────────────────
    # Verificación de disponibilidad
    # ─────────────────────────────────────────────────────────
    
    def check_local_available(self, force_check: bool = False) -> bool:
        """
        Verifica si el servidor DevDocs local está disponible.
        
        Args:
            force_check: Forzar verificación (no usar caché del estado)
        
        Returns:
            True si el servidor local está disponible
        """
        if self._local_available is not None and not force_check:
            return self._local_available
        
        try:
            url = self.LOCAL_DOCS_URL.format(base=self.local_url)
            response = self.local_client.get(url)
            self._local_available = response.status_code == 200
        except Exception:
            self._local_available = False
        
        return self._local_available
    
    def get_status(self) -> dict:
        """
        Obtiene el estado actual del cliente híbrido.
        
        Returns:
            Diccionario con información del estado
        """
        return {
            "mode": self.mode.value,
            "local_url": self.local_url,
            "local_available": self.check_local_available(force_check=True),
            "cache_stats": self.cache.get_stats(),
            "last_source": self._last_source.value if self._last_source else None
        }
    
    def set_mode(self, mode: HybridMode) -> dict:
        """
        Cambia el modo de operación.
        
        Args:
            mode: Nuevo modo de operación
        
        Returns:
            Estado actualizado
        """
        self.mode = mode
        return self.get_status()
    
    def set_local_url(self, url: str) -> dict:
        """
        Cambia la URL del servidor local.
        
        Args:
            url: Nueva URL del servidor local
        
        Returns:
            Estado actualizado con verificación de disponibilidad
        """
        self.local_url = url
        self._local_available = None  # Reset estado
        return self.get_status()
    
    # ─────────────────────────────────────────────────────────
    # Obtención de datos con fallback
    # ─────────────────────────────────────────────────────────
    
    def _get_from_local(self, endpoint: str) -> Optional[str]:
        """Intenta obtener datos del servidor local"""
        if self.mode == HybridMode.REMOTE_ONLY:
            return None
        
        if not self.check_local_available():
            return None
        
        try:
            response = self.local_client.get(endpoint)
            if response.status_code == 200:
                self._last_source = DataSource.LOCAL
                return response.text
        except Exception:
            self._local_available = False
        
        return None
    
    def _get_from_cache(self, cache_key: str, cache_type: str) -> Optional[str]:
        """Intenta obtener datos del caché"""
        if cache_type == "docs_list":
            data = self.cache.get_docs_list()
        elif cache_type == "index":
            data = self.cache.get_index(cache_key)
        elif cache_type == "page":
            # cache_key formato: "tech|path"
            parts = cache_key.split("|", 1)
            if len(parts) == 2:
                data = self.cache.get_page(parts[0], parts[1])
            else:
                data = None
        else:
            data = None
        
        if data:
            self._last_source = DataSource.CACHE
        
        return data
    
    def _get_from_remote(self, endpoint: str) -> Optional[str]:
        """Intenta obtener datos de la API remota"""
        if self.mode in (HybridMode.LOCAL_ONLY, HybridMode.OFFLINE):
            return None
        
        try:
            response = self.remote_client.get(endpoint)
            if response.status_code == 200:
                self._last_source = DataSource.REMOTE
                return response.text
        except Exception:
            pass
        
        return None
    
    def _save_to_cache(self, data: str, cache_key: str, cache_type: str):
        """Guarda datos en el caché"""
        if cache_type == "docs_list":
            self.cache.save_docs_list(data)
        elif cache_type == "index":
            self.cache.save_index(cache_key, data)
        elif cache_type == "page":
            parts = cache_key.split("|", 1)
            if len(parts) == 2:
                self.cache.save_page(parts[0], parts[1], data)
    
    # ─────────────────────────────────────────────────────────
    # API Pública
    # ─────────────────────────────────────────────────────────
    
    def get_docs_list(self, force_refresh: bool = False) -> tuple[list[dict], DataSource]:
        """
        Obtiene la lista de documentaciones disponibles.
        
        Returns:
            Tupla (lista de docs, fuente de datos)
        """
        cache_key = "docs_list"
        
        # Modo AUTO: Local → Cache → Remote
        if self.mode == HybridMode.AUTO and not force_refresh:
            # Intentar local
            local_url = self.LOCAL_DOCS_URL.format(base=self.local_url)
            data = self._get_from_local(local_url)
            if data:
                self._save_to_cache(data, cache_key, "docs_list")
                return json.loads(data), DataSource.LOCAL
            
            # Intentar cache
            data = self._get_from_cache(cache_key, "docs_list")
            if data:
                return json.loads(data), DataSource.CACHE
        
        # Modo OFFLINE: Solo cache
        if self.mode == HybridMode.OFFLINE:
            data = self._get_from_cache(cache_key, "docs_list")
            if data:
                return json.loads(data), DataSource.CACHE
            raise Exception("No hay datos en caché y el modo es OFFLINE")
        
        # Modo LOCAL_ONLY
        if self.mode == HybridMode.LOCAL_ONLY:
            local_url = self.LOCAL_DOCS_URL.format(base=self.local_url)
            data = self._get_from_local(local_url)
            if data:
                self._save_to_cache(data, cache_key, "docs_list")
                return json.loads(data), DataSource.LOCAL
            raise Exception(f"Servidor local no disponible en {self.local_url}")
        
        # Intentar remoto (AUTO fallback o REMOTE_ONLY)
        data = self._get_from_remote(self.REMOTE_DOCS_URL)
        if data:
            self._save_to_cache(data, cache_key, "docs_list")
            return json.loads(data), DataSource.REMOTE
        
        # Último intento: cache
        if not force_refresh:
            data = self._get_from_cache(cache_key, "docs_list")
            if data:
                return json.loads(data), DataSource.CACHE
        
        raise Exception("No se pudo obtener la lista de documentaciones")
    
    def get_index(self, tech: str, force_refresh: bool = False) -> tuple[dict, DataSource]:
        """
        Obtiene el índice de una documentación.
        
        Returns:
            Tupla (índice, fuente de datos)
        """
        cache_key = tech
        
        if self.mode == HybridMode.AUTO and not force_refresh:
            # Intentar local
            local_url = self.LOCAL_INDEX_URL.format(base=self.local_url, tech=tech)
            data = self._get_from_local(local_url)
            if data:
                self._save_to_cache(data, cache_key, "index")
                return json.loads(data), DataSource.LOCAL
            
            # Intentar cache
            data = self._get_from_cache(cache_key, "index")
            if data:
                return json.loads(data), DataSource.CACHE
        
        if self.mode == HybridMode.OFFLINE:
            data = self._get_from_cache(cache_key, "index")
            if data:
                return json.loads(data), DataSource.CACHE
            raise Exception(f"No hay índice de {tech} en caché y el modo es OFFLINE")
        
        if self.mode == HybridMode.LOCAL_ONLY:
            local_url = self.LOCAL_INDEX_URL.format(base=self.local_url, tech=tech)
            data = self._get_from_local(local_url)
            if data:
                self._save_to_cache(data, cache_key, "index")
                return json.loads(data), DataSource.LOCAL
            raise Exception(f"Servidor local no disponible para {tech}")
        
        # Remoto
        remote_url = self.REMOTE_INDEX_URL.format(tech=tech)
        data = self._get_from_remote(remote_url)
        if data:
            self._save_to_cache(data, cache_key, "index")
            return json.loads(data), DataSource.REMOTE
        
        # Fallback cache
        if not force_refresh:
            data = self._get_from_cache(cache_key, "index")
            if data:
                return json.loads(data), DataSource.CACHE
        
        raise Exception(f"No se pudo obtener el índice de {tech}")
    
    def get_page(self, tech: str, path: str, force_refresh: bool = False) -> tuple[str, DataSource]:
        """
        Obtiene el contenido de una página.
        
        Returns:
            Tupla (contenido HTML, fuente de datos)
        """
        clean_path = path.split('#')[0]
        cache_key = f"{tech}|{clean_path}"
        
        if self.mode == HybridMode.AUTO and not force_refresh:
            # Intentar local
            local_url = self.LOCAL_PAGE_URL.format(base=self.local_url, tech=tech, path=clean_path)
            data = self._get_from_local(local_url)
            if data:
                self._save_to_cache(data, cache_key, "page")
                return data, DataSource.LOCAL
            
            # Intentar cache
            data = self._get_from_cache(cache_key, "page")
            if data:
                return data, DataSource.CACHE
        
        if self.mode == HybridMode.OFFLINE:
            data = self._get_from_cache(cache_key, "page")
            if data:
                return data, DataSource.CACHE
            raise Exception(f"No hay página {tech}/{path} en caché y el modo es OFFLINE")
        
        if self.mode == HybridMode.LOCAL_ONLY:
            local_url = self.LOCAL_PAGE_URL.format(base=self.local_url, tech=tech, path=clean_path)
            data = self._get_from_local(local_url)
            if data:
                self._save_to_cache(data, cache_key, "page")
                return data, DataSource.LOCAL
            raise Exception(f"Servidor local no disponible para {tech}/{path}")
        
        # Remoto
        remote_url = self.REMOTE_PAGE_URL.format(tech=tech, path=clean_path)
        data = self._get_from_remote(remote_url)
        if data:
            self._save_to_cache(data, cache_key, "page")
            return data, DataSource.REMOTE
        
        # Fallback cache
        if not force_refresh:
            data = self._get_from_cache(cache_key, "page")
            if data:
                return data, DataSource.CACHE
        
        raise Exception(f"No se pudo obtener la página {tech}/{path}")
