"""
DevDocs MCP Server
Expone herramientas para acceder a documentación de DevDocs desde Claude
"""
import json
import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .api import DevDocsAPI
from .cache import DevDocsCache
from .utils import truncate_text


# Crear instancias globales
cache = DevDocsCache()
api = DevDocsAPI(cache)
server = Server("devdocs-mcp")


# ═══════════════════════════════════════════════════════════════
#                         TOOLS
# ═══════════════════════════════════════════════════════════════

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lista todas las herramientas disponibles"""
    return [
        Tool(
            name="list_documentations",
            description="""Lista todas las documentaciones disponibles en DevDocs.
Puedes filtrar por nombre de tecnología.

Ejemplos de uso:
- Sin filtro: lista todas las ~600 documentaciones
- Con filtro "python": lista Python 2.7, 3.8, 3.9, 3.10, 3.11, 3.12
- Con filtro "react": lista React, React Native, React Router, etc.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "Filtro opcional por nombre (ej: 'python', 'javascript', 'spring')"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="search_documentation",
            description="""Busca dentro del índice de una documentación específica.
Útil para encontrar clases, funciones, métodos, módulos, etc.

IMPORTANTE: Primero debes saber el slug exacto de la documentación.
Usa list_documentations para encontrarlo.

Ejemplos:
- tech="python~3.10", query="asyncio" → encuentra módulo asyncio
- tech="spring_boot", query="actuator" → encuentra docs de actuator
- tech="javascript", query="Promise" → encuentra Promise API""",
            inputSchema={
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Slug de la tecnología (ej: 'python~3.10', 'spring_boot', 'javascript')"
                    },
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Máximo de resultados (default: 20)",
                        "default": 20
                    }
                },
                "required": ["tech", "query"]
            }
        ),
        Tool(
            name="get_page_content",
            description="""Obtiene el contenido completo de una página de documentación.
Devuelve el contenido en formato Markdown.

IMPORTANTE: Necesitas el path exacto de la página.
Usa search_documentation para encontrarlo.

Ejemplos:
- tech="python~3.10", path="library/asyncio" → documentación de asyncio
- tech="spring_boot", path="actuator" → documentación de actuator
- tech="javascript", path="global_objects/promise" → documentación de Promise""",
            inputSchema={
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Slug de la tecnología"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path de la página (obtenido de search_documentation)"
                    }
                },
                "required": ["tech", "path"]
            }
        ),
        Tool(
            name="get_documentation_index",
            description="""Obtiene información del índice de una documentación.
Muestra estadísticas: total de entradas, páginas únicas, tipos de contenido.

Útil para entender la estructura de una documentación antes de buscar.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Slug de la tecnología"
                    }
                },
                "required": ["tech"]
            }
        ),
        Tool(
            name="get_cache_stats",
            description="""Muestra estadísticas del caché local.
Incluye: directorio, archivos totales, tamaño, documentaciones cacheadas.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="clear_cache",
            description="""Limpia el caché local.
Puedes limpiar todo o solo una tecnología específica.

Ejemplos:
- Sin parámetros: limpia TODO el caché
- tech="python~3.10": limpia solo caché de Python 3.10""",
            inputSchema={
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Tecnología específica a limpiar (opcional, si no se especifica limpia todo)"
                    }
                },
                "required": []
            }
        ),
        # ═══════════════════════════════════════════════════════════
        #                    NUEVAS TOOLS
        # ═══════════════════════════════════════════════════════════
        Tool(
            name="get_multiple_pages",
            description="""Obtiene múltiples páginas de documentación a la vez.
Útil para obtener documentación relacionada en una sola llamada.

Ejemplos:
- tech="python~3.10", paths=["library/asyncio", "library/asyncio-task", "library/asyncio-stream"]
- tech="react", paths=["hooks-intro", "hooks-state", "hooks-effect"]""",
            inputSchema={
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Slug de la tecnología"
                    },
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de paths de páginas a obtener"
                    }
                },
                "required": ["tech", "paths"]
            }
        ),
        Tool(
            name="search_across_docs",
            description="""Busca un término en MÚLTIPLES documentaciones a la vez.
Útil cuando no sabes en qué tecnología buscar.

Si no especificas techs, busca en las más populares:
JavaScript, Python, React, Node, TypeScript, HTML, CSS, Vue, Angular.

Ejemplos:
- query="websocket" → busca en todas las populares
- query="async", techs=["python~3.10", "javascript", "rust"] → busca en específicas""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda"
                    },
                    "techs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de tecnologías donde buscar (opcional)"
                    },
                    "limit_per_tech": {
                        "type": "integer",
                        "description": "Máximo de resultados por tecnología (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_type_entries",
            description="""Obtiene entradas filtradas por tipo (class, function, method, module, etc.).
Primero usa get_documentation_index para ver los tipos disponibles.

Ejemplos:
- tech="python~3.10", entry_type="class" → lista todas las clases
- tech="javascript", entry_type="method" → lista todos los métodos
- tech="react", entry_type="hook" → lista todos los hooks""",
            inputSchema={
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Slug de la tecnología"
                    },
                    "entry_type": {
                        "type": "string",
                        "description": "Tipo a filtrar (class, function, method, module, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Máximo de resultados (default: 50)",
                        "default": 50
                    }
                },
                "required": ["tech", "entry_type"]
            }
        ),
        Tool(
            name="get_examples",
            description="""Extrae solo los bloques de código/ejemplos de una página de documentación.
Útil cuando solo necesitas ver ejemplos de uso, no toda la documentación.

Ejemplos:
- tech="python~3.10", path="library/asyncio" → ejemplos de asyncio
- tech="javascript", path="global_objects/promise" → ejemplos de Promise""",
            inputSchema={
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Slug de la tecnología"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path de la página"
                    }
                },
                "required": ["tech", "path"]
            }
        ),
        Tool(
            name="export_documentation",
            description="""Exporta toda la documentación de una tecnología a archivos locales.
Los archivos se guardan como Markdown en el directorio especificado.

ADVERTENCIA: Puede tomar varios minutos para documentaciones grandes.
Usa max_pages para limitar la cantidad de páginas a exportar.

Ejemplos:
- tech="spring_boot", output_dir="./spring_docs" → exporta todo Spring Boot
- tech="python~3.10", output_dir="./python_docs", max_pages=50 → exporta 50 páginas""",
            inputSchema={
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Slug de la tecnología"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directorio donde guardar los archivos"
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Máximo de páginas a exportar (opcional, None = todas)"
                    }
                },
                "required": ["tech", "output_dir"]
            }
        ),
        Tool(
            name="offline_mode_status",
            description="""Muestra qué documentaciones están disponibles offline (en caché).
Indica qué tecnologías tienen el índice cacheado y cuántas páginas.

Útil para saber qué documentación puedes consultar sin conexión a internet.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Ejecuta una herramienta"""
    
    try:
        if name == "list_documentations":
            result = await handle_list_documentations(arguments)
        elif name == "search_documentation":
            result = await handle_search_documentation(arguments)
        elif name == "get_page_content":
            result = await handle_get_page_content(arguments)
        elif name == "get_documentation_index":
            result = await handle_get_documentation_index(arguments)
        elif name == "get_cache_stats":
            result = await handle_get_cache_stats(arguments)
        elif name == "clear_cache":
            result = await handle_clear_cache(arguments)
        # ═══ NUEVAS TOOLS ═══
        elif name == "get_multiple_pages":
            result = await handle_get_multiple_pages(arguments)
        elif name == "search_across_docs":
            result = await handle_search_across_docs(arguments)
        elif name == "get_type_entries":
            result = await handle_get_type_entries(arguments)
        elif name == "get_examples":
            result = await handle_get_examples(arguments)
        elif name == "export_documentation":
            result = await handle_export_documentation(arguments)
        elif name == "offline_mode_status":
            result = await handle_offline_mode_status(arguments)
        else:
            result = f"Error: Herramienta '{name}' no encontrada"
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ═══════════════════════════════════════════════════════════════
#                    HANDLERS DE TOOLS
# ═══════════════════════════════════════════════════════════════

async def handle_list_documentations(args: dict) -> str:
    """Lista documentaciones disponibles"""
    filter_text = args.get('filter', '')
    
    # Ejecutar en thread pool para no bloquear
    loop = asyncio.get_event_loop()
    
    if filter_text:
        docs = await loop.run_in_executor(None, api.search_docs, filter_text)
    else:
        docs = await loop.run_in_executor(None, api.get_docs_list)
    
    if not docs:
        return f"No se encontraron documentaciones{f' para: {filter_text}' if filter_text else ''}"
    
    # Formatear resultado
    lines = [f"## Documentaciones Disponibles ({len(docs)} encontradas)\n"]
    
    for doc in docs[:50]:  # Limitar a 50 para no saturar
        name = doc.get('name', 'Unknown')
        slug = doc.get('slug', '')
        version = doc.get('version', '')
        release = doc.get('release', '')
        
        version_info = version or release
        lines.append(f"- **{name}** (`{slug}`){f' - v{version_info}' if version_info else ''}")
    
    if len(docs) > 50:
        lines.append(f"\n... y {len(docs) - 50} más. Usa un filtro para ver específicas.")
    
    lines.append("\n\n💡 Usa el `slug` en otras herramientas (ej: `python~3.10`, `spring_boot`)")
    
    return '\n'.join(lines)


async def handle_search_documentation(args: dict) -> str:
    """Busca en el índice de una documentación"""
    tech = args.get('tech', '')
    query = args.get('query', '')
    limit = args.get('limit', 20)
    
    if not tech or not query:
        return "Error: Se requiere 'tech' y 'query'"
    
    loop = asyncio.get_event_loop()
    
    try:
        results = await loop.run_in_executor(
            None, 
            lambda: api.search_in_index(tech, query, limit)
        )
    except Exception as e:
        return f"Error buscando en {tech}: {str(e)}\n\n💡 Verifica que el slug sea correcto usando list_documentations"
    
    if not results:
        return f"No se encontraron resultados para '{query}' en {tech}"
    
    # Formatear resultado
    lines = [f"## Resultados para '{query}' en {tech} ({len(results)} encontrados)\n"]
    
    for entry in results:
        name = entry.get('name', 'Unknown')
        path = entry.get('path', '')
        entry_type = entry.get('type', '')
        
        # Limpiar path de anclas para mostrar
        clean_path = path.split('#')[0]
        
        lines.append(f"- **{name}**")
        lines.append(f"  - Path: `{clean_path}`")
        if entry_type:
            lines.append(f"  - Tipo: {entry_type}")
        lines.append("")
    
    lines.append(f"\n💡 Usa `get_page_content` con tech=`{tech}` y el path deseado para ver el contenido")
    
    return '\n'.join(lines)


async def handle_get_page_content(args: dict) -> str:
    """Obtiene contenido de una página"""
    tech = args.get('tech', '')
    path = args.get('path', '')
    
    if not tech or not path:
        return "Error: Se requiere 'tech' y 'path'"
    
    loop = asyncio.get_event_loop()
    
    try:
        content = await loop.run_in_executor(
            None,
            lambda: api.get_page(tech, path)
        )
    except Exception as e:
        return f"Error obteniendo {tech}/{path}: {str(e)}"
    
    # Truncar si es muy largo
    return truncate_text(content, max_length=50000)


async def handle_get_documentation_index(args: dict) -> str:
    """Obtiene estadísticas del índice"""
    tech = args.get('tech', '')
    
    if not tech:
        return "Error: Se requiere 'tech'"
    
    loop = asyncio.get_event_loop()
    
    try:
        stats = await loop.run_in_executor(
            None,
            lambda: api.get_index_stats(tech)
        )
    except Exception as e:
        return f"Error obteniendo índice de {tech}: {str(e)}"
    
    lines = [
        f"## Índice de {tech}\n",
        f"- **Total de entradas:** {stats['total_entries']:,}",
        f"- **Páginas únicas:** {stats['unique_pages']:,}",
        f"- **Tipos de contenido:** {', '.join(stats['types'][:10])}",
    ]
    
    if len(stats['types']) > 10:
        lines.append(f"  ... y {len(stats['types']) - 10} más")
    
    return '\n'.join(lines)


async def handle_get_cache_stats(args: dict) -> str:
    """Obtiene estadísticas del caché"""
    stats = cache.get_cache_stats()
    
    lines = [
        "## Estadísticas del Caché\n",
        f"- **Directorio:** `{stats['cache_dir']}`",
        f"- **Archivos totales:** {stats['total_files']:,}",
        f"- **Tamaño total:** {stats['total_size_mb']:.2f} MB",
        "\n### Documentaciones cacheadas:\n"
    ]
    
    for tech, info in stats['technologies'].items():
        lines.append(f"- **{tech}**: {info['files']} archivos ({info['size_mb']:.2f} MB)")
    
    if not stats['technologies']:
        lines.append("_No hay documentaciones en caché_")
    
    return '\n'.join(lines)


async def handle_clear_cache(args: dict) -> str:
    """Limpia el caché"""
    tech = args.get('tech')
    
    result = cache.clear_cache(tech)
    
    if result['status'] == 'ok':
        if result['cleared'] == 'all':
            return "✅ Caché completamente limpiado"
        else:
            return f"✅ Caché de '{result['cleared']}' limpiado"
    else:
        return f"⚠️ No se encontró caché para '{result['cleared']}'"


# ═══════════════════════════════════════════════════════════════
#                    NUEVOS HANDLERS
# ═══════════════════════════════════════════════════════════════

async def handle_get_multiple_pages(args: dict) -> str:
    """Obtiene múltiples páginas de documentación"""
    tech = args.get('tech', '')
    paths = args.get('paths', [])
    
    if not tech:
        return "Error: Parámetro 'tech' requerido"
    if not paths:
        return "Error: Parámetro 'paths' requerido (lista de paths)"
    
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, api.get_multiple_pages, tech, paths)
    
    lines = [f"## Múltiples páginas de {tech}\n"]
    lines.append(f"Solicitadas: {len(paths)} | Exitosas: {results['successful']} | Fallidas: {results['failed']}\n")
    
    for path, data in results['pages'].items():
        if data.get('error'):
            lines.append(f"\n### ❌ {path}\n")
            lines.append(f"Error: {data['error']}")
        else:
            lines.append(f"\n### ✅ {path}\n")
            content = data.get('content', '')
            # Limitar contenido para no saturar
            if len(content) > 3000:
                lines.append(content[:3000] + "\n\n... (contenido truncado)")
            else:
                lines.append(content)
    
    return '\n'.join(lines)


async def handle_search_across_docs(args: dict) -> str:
    """Busca en múltiples documentaciones"""
    query = args.get('query', '')
    techs = args.get('techs')
    limit_per_tech = args.get('limit_per_tech', 5)
    
    if not query:
        return "Error: Parámetro 'query' requerido"
    
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, api.search_across_docs, query, techs, limit_per_tech)
    
    lines = [f"## Búsqueda: '{query}'\n"]
    lines.append(f"Tecnologías buscadas: {results['searched_count']} | Total resultados: {results['total_results']}\n")
    
    for tech, data in results['results'].items():
        if data.get('error'):
            lines.append(f"\n### ⚠️ {tech}: Error - {data['error']}")
        elif data.get('entries'):
            lines.append(f"\n### 📚 {tech} ({len(data['entries'])} resultados)")
            for entry in data['entries'][:limit_per_tech]:
                name = entry.get('name', 'Unknown')
                path = entry.get('path', '')
                entry_type = entry.get('type', '')
                type_str = f" [{entry_type}]" if entry_type else ""
                lines.append(f"- **{name}**{type_str} → `{path}`")
    
    if results['total_results'] == 0:
        lines.append("\n_No se encontraron resultados_")
    
    return '\n'.join(lines)


async def handle_get_type_entries(args: dict) -> str:
    """Obtiene entradas por tipo"""
    tech = args.get('tech', '')
    entry_type = args.get('entry_type', '')
    limit = args.get('limit', 50)
    
    if not tech:
        return "Error: Parámetro 'tech' requerido"
    if not entry_type:
        return "Error: Parámetro 'entry_type' requerido"
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, api.get_type_entries, tech, entry_type, limit)
    
    if result.get('error'):
        return f"Error: {result['error']}"
    
    entries = result.get('entries', [])
    available_types = result.get('available_types', [])
    
    lines = [f"## {entry_type.title()}s en {tech}\n"]
    lines.append(f"Encontradas: {len(entries)}\n")
    
    if not entries:
        lines.append(f"\n⚠️ No se encontraron entradas de tipo '{entry_type}'")
        if available_types:
            lines.append(f"\n**Tipos disponibles:** {', '.join(sorted(available_types)[:20])}")
        return '\n'.join(lines)
    
    for entry in entries:
        name = entry.get('name', 'Unknown')
        path = entry.get('path', '')
        lines.append(f"- **{name}** → `{path}`")
    
    if len(entries) >= limit:
        lines.append(f"\n_Mostrando {limit} resultados. Usa `limit` mayor para ver más._")
    
    return '\n'.join(lines)


async def handle_get_examples(args: dict) -> str:
    """Extrae ejemplos de código de una página"""
    tech = args.get('tech', '')
    path = args.get('path', '')
    
    if not tech:
        return "Error: Parámetro 'tech' requerido"
    if not path:
        return "Error: Parámetro 'path' requerido"
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, api.get_examples_from_page, tech, path)
    
    if result.get('error'):
        return f"Error: {result['error']}"
    
    examples = result.get('examples', [])
    
    lines = [f"## Ejemplos de código: {path}\n"]
    lines.append(f"Encontrados: {len(examples)} bloques de código\n")
    
    if not examples:
        return '\n'.join(lines) + "\n_No se encontraron ejemplos de código en esta página_"
    
    for i, example in enumerate(examples, 1):
        lang = example.get('language', '')
        code = example.get('code', '')
        lang_str = f"```{lang}" if lang else "```"
        lines.append(f"### Ejemplo {i}")
        lines.append(f"{lang_str}\n{code}\n```\n")
    
    return '\n'.join(lines)


async def handle_export_documentation(args: dict) -> str:
    """Exporta documentación a archivos"""
    tech = args.get('tech', '')
    output_dir = args.get('output_dir', '')
    max_pages = args.get('max_pages')
    
    if not tech:
        return "Error: Parámetro 'tech' requerido"
    if not output_dir:
        return "Error: Parámetro 'output_dir' requerido"
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, api.export_documentation, tech, output_dir, max_pages)
    
    if result.get('error'):
        return f"Error: {result['error']}"
    
    lines = [
        f"## Exportación completada: {tech}\n",
        f"- **Directorio:** `{result['output_dir']}`",
        f"- **Páginas exportadas:** {result['exported']}",
        f"- **Errores:** {result['failed']}",
        f"- **Tamaño total:** {result['total_size_mb']:.2f} MB",
    ]
    
    return '\n'.join(lines)


async def handle_offline_mode_status(args: dict) -> str:
    """Muestra estado del modo offline"""
    loop = asyncio.get_event_loop()
    status = await loop.run_in_executor(None, api.get_offline_status)
    
    lines = [
        "## Estado Offline\n",
        f"- **Directorio caché:** `{status['cache_dir']}`",
        f"- **Tecnologías disponibles offline:** {status['available_offline_count']}",
        f"- **Tamaño total:** {status['total_size_mb']:.2f} MB",
    ]
    
    if status['technologies']:
        lines.append("\n### Documentaciones en caché:\n")
        for tech, info in status['technologies'].items():
            has_index = "✅" if info['has_index'] else "❌"
            lines.append(f"- **{tech}**: {info['pages_cached']} páginas ({info['size_mb']:.2f} MB) | Índice: {has_index}")
    else:
        lines.append("\n_No hay documentaciones en caché. Usa `get_page_content` o `get_documentation_index` para cachear._")
    
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
#                         MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Punto de entrada principal"""
    import sys
    
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
