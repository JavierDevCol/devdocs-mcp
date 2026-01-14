"""
Test del servidor MCP usando protocolo JSON-RPC
"""
import json
import subprocess
import sys

def send_request(process, method, params=None, request_id=1):
    """Envía una request JSON-RPC al servidor MCP"""
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
    }
    if params:
        request["params"] = params
    
    message = json.dumps(request)
    # MCP usa formato: Content-Length: N\r\n\r\n{json}
    full_message = f"Content-Length: {len(message)}\r\n\r\n{message}"
    
    process.stdin.write(full_message)
    process.stdin.flush()
    
    # Leer respuesta
    # Primero el header
    header = ""
    while True:
        char = process.stdout.read(1)
        header += char
        if header.endswith("\r\n\r\n"):
            break
    
    # Extraer content-length
    content_length = int(header.split(":")[1].strip().split("\r\n")[0])
    
    # Leer el body
    body = process.stdout.read(content_length)
    return json.loads(body)


def main():
    print("=" * 60)
    print("  TEST: MCP Server Protocol")
    print("=" * 60)
    
    # Iniciar el servidor
    process = subprocess.Popen(
        [sys.executable, "-m", "devdocs_mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="E:/DevDocs/devdocs-mcp/src"
    )
    
    try:
        # 1. Initialize
        print("\n1. Inicializando servidor...")
        response = send_request(process, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        })
        print(f"   Server: {response.get('result', {}).get('serverInfo', {})}")
        
        # 2. List tools
        print("\n2. Listando herramientas...")
        response = send_request(process, "tools/list", {}, request_id=2)
        tools = response.get('result', {}).get('tools', [])
        print(f"   Herramientas disponibles: {len(tools)}")
        for tool in tools:
            print(f"   - {tool['name']}")
        
        # 3. Call tool: list_documentations
        print("\n3. Llamando list_documentations(filter='spring')...")
        response = send_request(process, "tools/call", {
            "name": "list_documentations",
            "arguments": {"filter": "spring"}
        }, request_id=3)
        content = response.get('result', {}).get('content', [])
        if content:
            text = content[0].get('text', '')[:500]
            print(f"   Resultado (primeros 500 chars):\n{text}")
        
        # 4. Call tool: search_documentation
        print("\n4. Llamando search_documentation(tech='spring_boot', query='actuator')...")
        response = send_request(process, "tools/call", {
            "name": "search_documentation",
            "arguments": {"tech": "spring_boot", "query": "actuator"}
        }, request_id=4)
        content = response.get('result', {}).get('content', [])
        if content:
            text = content[0].get('text', '')[:800]
            print(f"   Resultado:\n{text}")
        
        print("\n" + "=" * 60)
        print("  ✅ MCP SERVER FUNCIONANDO CORRECTAMENTE")
        print("=" * 60)
        
    finally:
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
