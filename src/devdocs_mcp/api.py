"""
Cliente API para DevDocs
Maneja las peticiones HTTP a la API de DevDocs
"""
import json
from typing import Optional
import httpx

from .cache import DevDocsCache
from .utils import html_to_markdown


# URLs de la API de DevDocs
DEVDOCS_DOCS_URL = "https://devdocs.io/docs.json"
DEVDOCS_INDEX_URL = "https://documents.devdocs.io/{tech}/index.json"
DEVDOCS_PAGE_URL = "https://documents.devdocs.io/{tech}/{path}.html"


class DevDocsAPI:
    """Cliente para la API de DevDocs con caché integrado"""
    
    def __init__(self, cache: Optional[DevDocsCache] = None):
        self.cache = cache or DevDocsCache()
        # Habilitar seguimiento de redirects
        self.client = httpx.Client(timeout=60.0, follow_redirects=True)
    
    def __del__(self):
        """Cerrar cliente HTTP al destruir"""
        if hasattr(self, 'client'):
            self.client.close()
    
    # ─────────────────────────────────────────────────────────
    # Lista de documentaciones
    # ─────────────────────────────────────────────────────────
    
    def get_docs_list(self, force_refresh: bool = False) -> list[dict]:
        """
        Obtiene la lista de todas las documentaciones disponibles.
        
        Returns:
            Lista de diccionarios con info de cada documentación:
            [{"name": "Python", "slug": "python~3.10", "version": "3.10", ...}, ...]
        """
        # Intentar caché primero
        if not force_refresh:
            cached = self.cache.get_docs_list()
            if cached:
                return json.loads(cached)
        
        # Obtener de la API
        response = self.client.get(DEVDOCS_DOCS_URL)
        response.raise_for_status()
        
        # Guardar en caché
        self.cache.save_docs_list(response.text)
        
        return response.json()
    
    def search_docs(self, query: str) -> list[dict]:
        """
        Busca documentaciones por nombre.
        
        Args:
            query: Término de búsqueda (ej: "python", "react", "spring")
        
        Returns:
            Lista de documentaciones que coinciden
        """
        docs = self.get_docs_list()
        query_lower = query.lower()
        
        return [
            doc for doc in docs
            if query_lower in doc.get('name', '').lower()
            or query_lower in doc.get('slug', '').lower()
        ]
    
    # ─────────────────────────────────────────────────────────
    # Índice de una tecnología
    # ─────────────────────────────────────────────────────────
    
    def get_index(self, tech: str, force_refresh: bool = False) -> dict:
        """
        Obtiene el índice completo de una documentación.
        
        Args:
            tech: Slug de la tecnología (ej: "python~3.10", "spring_boot")
        
        Returns:
            Diccionario con entries y types de la documentación
        """
        # Intentar caché primero
        if not force_refresh:
            cached = self.cache.get_index(tech)
            if cached:
                return json.loads(cached)
        
        # Obtener de la API
        url = DEVDOCS_INDEX_URL.format(tech=tech)
        response = self.client.get(url)
        response.raise_for_status()
        
        # Guardar en caché
        self.cache.save_index(tech, response.text)
        
        return response.json()
    
    def search_in_index(self, tech: str, query: str, limit: int = 20) -> list[dict]:
        """
        Busca dentro del índice de una documentación.
        
        Args:
            tech: Slug de la tecnología
            query: Término de búsqueda
            limit: Máximo de resultados
        
        Returns:
            Lista de entradas que coinciden con la búsqueda
        """
        index = self.get_index(tech)
        entries = index.get('entries', [])
        query_lower = query.lower()
        
        results = []
        for entry in entries:
            name = entry.get('name', '').lower()
            path = entry.get('path', '').lower()
            
            # Búsqueda en nombre y path
            if query_lower in name or query_lower in path:
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_index_stats(self, tech: str) -> dict:
        """
        Obtiene estadísticas del índice de una documentación.
        
        Returns:
            Diccionario con conteos y tipos
        """
        index = self.get_index(tech)
        entries = index.get('entries', [])
        types = index.get('types', [])
        
        # Contar páginas únicas (sin anclas #)
        unique_pages = set()
        for entry in entries:
            path = entry.get('path', '')
            base_path = path.split('#')[0]
            if base_path:
                unique_pages.add(base_path)
        
        return {
            "tech": tech,
            "total_entries": len(entries),
            "unique_pages": len(unique_pages),
            "types": [t.get('name') for t in types]
        }
    
    # ─────────────────────────────────────────────────────────
    # Contenido de páginas
    # ─────────────────────────────────────────────────────────
    
    def get_page(self, tech: str, path: str, force_refresh: bool = False) -> str:
        """
        Obtiene el contenido de una página de documentación en Markdown.
        
        Args:
            tech: Slug de la tecnología (ej: "python~3.10")
            path: Path de la página (ej: "library/asyncio")
        
        Returns:
            Contenido de la página en formato Markdown
        """
        # Limpiar path de anclas
        clean_path = path.split('#')[0]
        
        # Intentar caché primero
        if not force_refresh:
            cached = self.cache.get_page(tech, clean_path)
            if cached:
                return cached
        
        # Obtener de la API
        url = DEVDOCS_PAGE_URL.format(tech=tech, path=clean_path)
        response = self.client.get(url)
        response.raise_for_status()
        
        # Convertir HTML a Markdown
        markdown = html_to_markdown(response.text)
        
        # Agregar metadata
        web_url = f"https://devdocs.io/{tech}/{clean_path}"
        content = f"""# {clean_path}

**Fuente:** [{web_url}]({web_url})

---

{markdown}
"""
        
        # Guardar en caché
        self.cache.save_page(tech, clean_path, content)
        
        return content
    
    def get_page_raw_html(self, tech: str, path: str) -> str:
        """
        Obtiene el HTML raw de una página (sin convertir ni cachear).
        Útil para debugging.
        """
        clean_path = path.split('#')[0]
        url = DEVDOCS_PAGE_URL.format(tech=tech, path=clean_path)
        response = self.client.get(url)
        response.raise_for_status()
        return response.text

    # ─────────────────────────────────────────────────────────
    # NUEVAS FUNCIONALIDADES
    # ─────────────────────────────────────────────────────────
    
    def get_multiple_pages(self, tech: str, paths: list[str]) -> dict:
        """
        Obtiene múltiples páginas de una documentación.
        
        Args:
            tech: Slug de la tecnología
            paths: Lista de paths a obtener
        
        Returns:
            Diccionario con páginas y estadísticas
        """
        results = {}
        successful = 0
        failed = 0
        
        for path in paths:
            try:
                content = self.get_page(tech, path)
                results[path] = {'content': content}
                successful += 1
            except Exception as e:
                results[path] = {'error': str(e)}
                failed += 1
        
        return {
            'pages': results,
            'successful': successful,
            'failed': failed
        }
    
    def search_across_docs(self, query: str, techs: list[str] = None, limit_per_tech: int = 5) -> dict:
        """
        Busca en múltiples documentaciones a la vez.
        
        Args:
            query: Término de búsqueda
            techs: Lista de tecnologías donde buscar (None = las más populares)
            limit_per_tech: Máximo de resultados por tecnología
        
        Returns:
            Diccionario con resultados por tecnología
        """
        # Si no se especifican techs, usar las más populares
        if techs is None:
            techs = [
                "javascript", "python~3.12", "react", "node", 
                "typescript", "html", "css", "vue~3", "angular"
            ]
        
        results = {}
        total_results = 0
        
        for tech in techs:
            try:
                tech_results = self.search_in_index(tech, query, limit=limit_per_tech)
                if tech_results:
                    results[tech] = {'entries': tech_results}
                    total_results += len(tech_results)
            except Exception as e:
                results[tech] = {'error': str(e)}
        
        return {
            'results': results,
            'searched_count': len(techs),
            'total_results': total_results
        }
    
    def get_type_entries(self, tech: str, entry_type: str, limit: int = 50) -> dict:
        """
        Obtiene entradas filtradas por tipo (class, function, method, etc.).
        
        Args:
            tech: Slug de la tecnología
            entry_type: Tipo a filtrar (ej: "class", "function", "method", "module")
            limit: Máximo de resultados
        
        Returns:
            Diccionario con entradas y tipos disponibles
        """
        try:
            index = self.get_index(tech)
            entries = index.get('entries', [])
            available_types = set()
            type_lower = entry_type.lower()
            
            results = []
            for entry in entries:
                entry_type_value = entry.get('type', '').lower()
                if entry_type_value:
                    available_types.add(entry_type_value)
                if type_lower in entry_type_value:
                    results.append(entry)
                    if len(results) >= limit:
                        break
            
            return {
                'entries': results,
                'available_types': list(available_types)
            }
        except Exception as e:
            return {'error': str(e), 'entries': [], 'available_types': []}
    
    def get_available_types(self, tech: str) -> list[dict]:
        """
        Obtiene los tipos disponibles en una documentación.
        
        Returns:
            Lista de tipos con nombre y conteo
        """
        index = self.get_index(tech)
        return index.get('types', [])
    
    def export_documentation(self, tech: str, output_dir: str, max_pages: int = None) -> dict:
        """
        Exporta toda la documentación de una tecnología a archivos locales.
        
        Args:
            tech: Slug de la tecnología
            output_dir: Directorio de salida
            max_pages: Máximo de páginas a exportar (None = todas)
        
        Returns:
            Estadísticas de la exportación
        """
        import os
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Obtener índice
        index = self.get_index(tech)
        entries = index.get('entries', [])
        
        # Obtener páginas únicas
        unique_pages = set()
        for entry in entries:
            path = entry.get('path', '')
            base_path = path.split('#')[0]
            if base_path:
                unique_pages.add(base_path)
        
        pages_to_export = list(unique_pages)
        if max_pages:
            pages_to_export = pages_to_export[:max_pages]
        
        # Exportar cada página
        exported = 0
        failed = 0
        total_size = 0
        
        for page_path in pages_to_export:
            try:
                content = self.get_page(tech, page_path)
                
                # Crear nombre de archivo seguro
                safe_name = page_path.replace('/', '_').replace('\\', '_')
                file_path = output_path / f"{safe_name}.md"
                
                file_path.write_text(content, encoding='utf-8')
                exported += 1
                total_size += len(content)
            except Exception:
                failed += 1
        
        return {
            "tech": tech,
            "output_dir": str(output_path),
            "total_pages": len(unique_pages),
            "exported": exported,
            "failed": failed,
            "total_size_mb": round(total_size / 1024 / 1024, 2)
        }
    
    def get_examples_from_page(self, tech: str, path: str) -> dict:
        """
        Extrae bloques de código de una página de documentación.
        
        Args:
            tech: Slug de la tecnología
            path: Path de la página
        
        Returns:
            Diccionario con ejemplos de código encontrados
        """
        import re
        
        try:
            # Obtener contenido
            content = self.get_page(tech, path)
            
            # Buscar bloques de código markdown
            code_pattern = r'```(\w*)\n(.*?)```'
            matches = re.findall(code_pattern, content, re.DOTALL)
            
            examples = []
            for i, (language, code) in enumerate(matches, 1):
                examples.append({
                    "index": i,
                    "language": language or "text",
                    "code": code.strip()
                })
            
            return {'examples': examples}
        except Exception as e:
            return {'error': str(e), 'examples': []}
    
    def get_offline_status(self) -> dict:
        """
        Obtiene el estado de las documentaciones disponibles offline (en caché).
        
        Returns:
            Información detallada del caché
        """
        stats = self.cache.get_cache_stats()
        
        # Construir diccionario de tecnologías con info adicional
        technologies = {}
        for tech, info in stats.get('technologies', {}).items():
            index_cached = self.cache.get_index(tech) is not None
            technologies[tech] = {
                "has_index": index_cached,
                "pages_cached": info['files'],
                "size_mb": info['size_mb']
            }
        
        return {
            "cache_dir": stats['cache_dir'],
            "total_size_mb": stats['total_size_mb'],
            "available_offline_count": len(technologies),
            "docs_list_cached": self.cache.get_docs_list() is not None,
            "technologies": technologies
        }

