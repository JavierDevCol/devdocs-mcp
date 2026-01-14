"""DevDocs MCP Server - Acceso a documentación de DevDocs desde Claude"""

__version__ = "0.2.0"  # Added hybrid mode support

from .api import DevDocsAPI
from .cache import DevDocsCache
from .hybrid import HybridClient, HybridMode, DataSource
from .server import main

__all__ = [
    "DevDocsAPI",
    "DevDocsCache", 
    "HybridClient",
    "HybridMode",
    "DataSource",
    "main",
]
