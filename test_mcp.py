"""Test rápido del DevDocs MCP"""
from devdocs_mcp.api import DevDocsAPI
from devdocs_mcp.cache import DevDocsCache

def test_api():
    print("=" * 60)
    print("  TEST: DevDocs MCP API")
    print("=" * 60)
    
    api = DevDocsAPI()
    
    # Test 1: Listar documentaciones
    print("\n1. Buscando documentaciones de Python...")
    docs = api.search_docs("python")
    print(f"   Encontradas: {len(docs)}")
    for doc in docs[:5]:
        print(f"   - {doc['slug']}")
    
    # Test 2: Obtener índice
    print("\n2. Obteniendo índice de python~3.10...")
    stats = api.get_index_stats("python~3.10")
    print(f"   Entradas totales: {stats['total_entries']:,}")
    print(f"   Páginas únicas: {stats['unique_pages']}")
    
    # Test 3: Buscar en índice
    print("\n3. Buscando 'asyncio' en python~3.10...")
    results = api.search_in_index("python~3.10", "asyncio", limit=5)
    for r in results:
        print(f"   - {r['name']} → {r['path']}")
    
    # Test 4: Obtener página
    print("\n4. Obteniendo contenido de 'library/asyncio'...")
    content = api.get_page("python~3.10", "library/asyncio")
    print(f"   Contenido: {len(content):,} caracteres")
    print(f"   Primeras líneas:")
    for line in content.split('\n')[:5]:
        print(f"   {line}")
    
    # Test 5: Estadísticas de caché
    print("\n5. Estadísticas del caché...")
    cache = DevDocsCache()
    stats = cache.get_cache_stats()
    print(f"   Directorio: {stats['cache_dir']}")
    print(f"   Archivos: {stats['total_files']}")
    print(f"   Tamaño: {stats['total_size_mb']:.2f} MB")
    
    print("\n" + "=" * 60)
    print("  ✅ TODOS LOS TESTS PASARON")
    print("=" * 60)


if __name__ == "__main__":
    test_api()
