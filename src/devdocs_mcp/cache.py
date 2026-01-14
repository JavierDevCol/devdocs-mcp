"""
Sistema de caché en disco para DevDocs MCP
Almacena documentación localmente para acceso offline y rápido
"""
import re
from pathlib import Path
from typing import Optional


# Directorio de caché por defecto
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "devdocs-mcp"


class DevDocsCache:
    """Caché simple en disco para documentación de DevDocs"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, name: str) -> str:
        """Convierte un path en nombre de archivo válido"""
        # Reemplazar caracteres no válidos
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = re.sub(r'[-/\s]+', '_', name)
        name = name.strip('_')
        return name[:200]  # Limitar longitud
    
    def _get_docs_list_path(self) -> Path:
        """Ruta al archivo de lista de documentaciones"""
        return self.cache_dir / "docs.json"
    
    def _get_index_path(self, tech: str) -> Path:
        """Ruta al índice de una tecnología"""
        return self.cache_dir / tech / "index.json"
    
    def _get_page_path(self, tech: str, page_path: str) -> Path:
        """Ruta a una página de documentación"""
        safe_name = self._sanitize_filename(page_path)
        return self.cache_dir / tech / f"{safe_name}.md"
    
    # ─────────────────────────────────────────────────────────
    # Lista de documentaciones (docs.json)
    # ─────────────────────────────────────────────────────────
    
    def get_docs_list(self) -> Optional[str]:
        """Obtiene la lista de documentaciones desde caché"""
        path = self._get_docs_list_path()
        if path.exists():
            return path.read_text(encoding='utf-8')
        return None
    
    def save_docs_list(self, content: str) -> None:
        """Guarda la lista de documentaciones en caché"""
        path = self._get_docs_list_path()
        path.write_text(content, encoding='utf-8')
    
    # ─────────────────────────────────────────────────────────
    # Índice de tecnología (index.json)
    # ─────────────────────────────────────────────────────────
    
    def get_index(self, tech: str) -> Optional[str]:
        """Obtiene el índice de una tecnología desde caché"""
        path = self._get_index_path(tech)
        if path.exists():
            return path.read_text(encoding='utf-8')
        return None
    
    def save_index(self, tech: str, content: str) -> None:
        """Guarda el índice de una tecnología en caché"""
        path = self._get_index_path(tech)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    
    # ─────────────────────────────────────────────────────────
    # Páginas de documentación (.md)
    # ─────────────────────────────────────────────────────────
    
    def get_page(self, tech: str, page_path: str) -> Optional[str]:
        """Obtiene una página de documentación desde caché"""
        path = self._get_page_path(tech, page_path)
        if path.exists():
            return path.read_text(encoding='utf-8')
        return None
    
    def save_page(self, tech: str, page_path: str, content: str) -> None:
        """Guarda una página de documentación en caché"""
        path = self._get_page_path(tech, page_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    
    def page_exists(self, tech: str, page_path: str) -> bool:
        """Verifica si una página existe en caché"""
        return self._get_page_path(tech, page_path).exists()
    
    # ─────────────────────────────────────────────────────────
    # Utilidades
    # ─────────────────────────────────────────────────────────
    
    def get_cache_stats(self) -> dict:
        """Obtiene estadísticas del caché"""
        total_files = 0
        total_size = 0
        techs = {}
        
        for tech_dir in self.cache_dir.iterdir():
            if tech_dir.is_dir():
                tech_files = list(tech_dir.glob("*.md"))
                tech_size = sum(f.stat().st_size for f in tech_files)
                techs[tech_dir.name] = {
                    "files": len(tech_files),
                    "size_mb": round(tech_size / 1024 / 1024, 2)
                }
                total_files += len(tech_files)
                total_size += tech_size
        
        return {
            "cache_dir": str(self.cache_dir),
            "total_files": total_files,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "technologies": techs
        }
    
    def clear_cache(self, tech: Optional[str] = None) -> dict:
        """Limpia el caché (todo o una tecnología específica)"""
        import shutil
        
        if tech:
            tech_dir = self.cache_dir / tech
            if tech_dir.exists():
                shutil.rmtree(tech_dir)
                return {"cleared": tech, "status": "ok"}
            return {"cleared": tech, "status": "not_found"}
        else:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            return {"cleared": "all", "status": "ok"}
