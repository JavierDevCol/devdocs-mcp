# 📚 DevDocs MCP Server

> **Model Context Protocol (MCP) Server** para acceder a la documentación de [DevDocs.io](https://devdocs.io) desde Claude Desktop, GitHub Copilot y otros clientes MCP.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.2.0+-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-JavierDevCol-purple.svg)](https://github.com/JavierDevCol)

---

## 📖 Tabla de Contenidos

- [¿Qué es MCP?](#-qué-es-mcp)
- [¿Qué es DevDocs MCP?](#-qué-es-devdocs-mcp)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Instalación](#-instalación)
  - [Opción 1: Docker (Recomendado)](#opción-1-docker-recomendado)
  - [Opción 2: Instalación Local](#opción-2-instalación-local)
- [Configuración](#-configuración)
  - [GitHub Copilot (VS Code)](#github-copilot-vs-code)
  - [Claude Desktop](#claude-desktop)
- [Herramientas Disponibles](#-herramientas-disponibles)
- [Ejemplos de Uso](#-ejemplos-de-uso)
- [Sistema de Caché](#-sistema-de-caché)
- [API de DevDocs](#-api-de-devdocs)
- [Desarrollo](#-desarrollo)
- [Solución de Problemas](#-solución-de-problemas)
- [Licencia](#-licencia)

---

## 🤖 ¿Qué es MCP?

**Model Context Protocol (MCP)** es un protocolo abierto creado por Anthropic que permite a los modelos de IA (como Claude o Copilot) interactuar con herramientas externas de forma segura y estructurada.

### Arquitectura MCP

```
┌─────────────────────────────────────────────────────────────────┐
│                        Cliente MCP                              │
│              (Claude Desktop, GitHub Copilot, etc.)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ JSON-RPC 2.0 (stdio)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Servidor MCP                              │
│                    (devdocs-mcp-server)                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Tools     │  │  Resources  │  │   Prompts   │             │
│  │ (funciones) │  │  (datos)    │  │ (plantillas)│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/HTTPS
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DevDocs.io API                             │
│                 (documents.devdocs.io)                          │
└─────────────────────────────────────────────────────────────────┘
```

### Comunicación stdio

MCP utiliza **stdio (Standard Input/Output)** para la comunicación:

```
┌──────────┐     stdin (JSON)      ┌──────────┐
│  Cliente │ ────────────────────▶ │ Servidor │
│   MCP    │                       │   MCP    │
│          │ ◀──────────────────── │          │
└──────────┘    stdout (JSON)      └──────────┘
```

- **stdin**: El cliente envía peticiones JSON-RPC al servidor
- **stdout**: El servidor responde con resultados JSON-RPC
- **Sin puertos HTTP**: La comunicación es directa entre procesos

---

## 📚 ¿Qué es DevDocs MCP?

**DevDocs MCP** es un servidor MCP que proporciona acceso a la documentación de más de **600 tecnologías** disponibles en DevDocs.io, incluyendo:

- **Lenguajes**: Python, JavaScript, TypeScript, Rust, Go, Java, C++, etc.
- **Frameworks**: React, Vue, Angular, Django, Spring Boot, Express, etc.
- **Herramientas**: Docker, Kubernetes, Git, Webpack, etc.
- **APIs**: Web APIs, Node.js, Deno, etc.

### ¿Por qué usar DevDocs MCP?

| Sin DevDocs MCP | Con DevDocs MCP |
|-----------------|-----------------|
| ❌ Copiar/pegar de documentación | ✅ IA accede directamente |
| ❌ Cambiar entre ventanas | ✅ Todo en el mismo chat |
| ❌ Buscar manualmente | ✅ Búsqueda integrada |
| ❌ Información desactualizada | ✅ Documentación oficial |
| ❌ Limitado al conocimiento del modelo | ✅ Acceso a docs actualizadas |

---

## ✨ Características

### 🔧 14 Herramientas Disponibles

| Herramienta | Descripción |
|-------------|-------------|
| `list_documentations` | Lista todas las ~600 documentaciones disponibles |
| `search_documentation` | Busca en el índice de una tecnología específica |
| `get_page_content` | Obtiene el contenido de una página de documentación |
| `get_documentation_index` | Obtiene el índice completo de una tecnología |
| `get_cache_stats` | Muestra estadísticas del caché local |
| `clear_cache` | Limpia el caché (todo o por tecnología) |
| `get_multiple_pages` | Obtiene varias páginas en una sola llamada |
| `search_across_docs` | Busca en múltiples documentaciones a la vez |
| `get_type_entries` | Filtra entradas por tipo (class, function, etc.) |
| `get_examples` | Extrae solo los bloques de código de una página |
| `export_documentation` | Exporta documentación completa a archivos locales |
| `offline_mode_status` | Muestra qué documentaciones están disponibles offline |
| `get_hybrid_status` | ⚡ Muestra estado del modo híbrido (local/remoto) |
| `configure_hybrid_mode` | ⚡ Configura modo híbrido y URL del servidor local |

### 💾 Sistema de Caché Inteligente

- **Caché persistente**: No re-descarga documentación ya obtenida
- **Sin TTL**: Las docs de DevDocs son versionadas, no cambian
- **Modo offline**: Funciona sin internet para docs cacheadas
- **Volumen Docker**: Persiste entre reinicios del contenedor

### 🐳 Docker Ready

- Imagen ligera (~233MB)
- Volumen para persistir caché
- Configuración simple
- Compatible con Claude Desktop y GitHub Copilot

---

## 🏗 Arquitectura

### Estructura del Proyecto

```
devdocs-mcp/
├── src/
│   └── devdocs_mcp/
│       ├── __init__.py      # Package initialization
│       ├── server.py        # MCP server (12 tools)
│       ├── api.py           # DevDocs API client
│       ├── cache.py         # Disk-based cache system
│       └── utils.py         # HTML to Markdown converter
├── docker/
│   ├── Dockerfile           # Docker image definition
│   └── docker-compose.yml   # Docker Compose config
├── scripts/
│   ├── docker-build.bat     # Build script (Windows)
│   └── docker-build.sh      # Build script (Linux/Mac)
├── config/
│   └── claude_config_example.json  # MCP config examples
├── tests/
│   ├── test_mcp.py          # MCP server tests
│   └── test_mcp_protocol.py # Protocol tests
├── pyproject.toml           # Python project config
├── LICENSE
└── README.md
```

### Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Copilot / Claude                            │
│                                                                     │
│  "¿Cómo uso asyncio.gather en Python?"                             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ 1. Llama tool: search_documentation
                                │    {tech: "python~3.10", query: "gather"}
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DevDocs MCP Server                             │
│                                                                     │
│  server.py ──▶ api.py ──▶ cache.py                                 │
│      │            │           │                                     │
│      │            │           ├──▶ ¿En caché? ──▶ Sí ──▶ Retorna   │
│      │            │           │                                     │
│      │            │           └──▶ No ──▶ Descarga ──▶ Guarda      │
│      │            │                                                 │
│      │            └──▶ utils.py (HTML → Markdown)                  │
│      │                                                              │
│      └──▶ Retorna resultado formateado                             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ 2. Llama tool: get_page_content
                                │    {tech: "python~3.10", path: "library/asyncio-task"}
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DevDocs.io API                               │
│                                                                     │
│  documents.devdocs.io/python~3.10/library/asyncio-task.html        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Instalación

### Opción 1: Docker (Recomendado)

#### Requisitos
- Docker Desktop instalado y corriendo

#### Pasos

```bash
# 1. Clonar o navegar al directorio
cd devdocs-mcp

# 2. Construir la imagen
docker build -t devdocs-mcp:latest -f docker/Dockerfile .

# 3. Verificar que se creó
docker images devdocs-mcp
```

#### Verificar funcionamiento

```bash
# Probar que el servidor responde
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | docker run -i --rm devdocs-mcp:latest
```

### Opción 2: Instalación Local

#### Requisitos
- Python 3.10 o superior
- pip

#### Pasos

```bash
# 1. Navegar al directorio
cd devdocs-mcp

# 2. Instalar en modo desarrollo
pip install -e .

# 3. Verificar instalación
python -c "from devdocs_mcp.server import main; print('OK')"
```

### Opción 3: Modo Híbrido (Máximo Rendimiento)

El modo híbrido combina un servidor DevDocs local con la API remota para obtener el mejor rendimiento:

| Fuente | Latencia | Uso |
|--------|----------|-----|
| **Local** | ~5ms | DevDocs Docker local |
| **Caché** | <1ms | Disco local |
| **Remoto** | ~300ms | API de devdocs.io |

#### ¿Por qué usar modo híbrido?

- ⚡ **60x más rápido** que la API remota
- 🔌 **Funciona offline** con documentaciones descargadas
- 💾 **Caché inteligente** - una vez descargado, siempre disponible

#### Instalación modo híbrido

```bash
# 1. Clonar o navegar al directorio
cd devdocs-mcp

# 2. Iniciar con Docker Compose (modo híbrido)
docker compose -f docker/docker-compose.hybrid.yml up -d

# 3. Acceder a DevDocs local para descargar documentaciones
# Abre http://localhost:9292 en tu navegador
# Haz clic en "Select documentation" y descarga las que necesites
```

#### Configuración para Claude/Copilot (modo híbrido)

```json
{
  "mcp": {
    "servers": {
      "devdocs": {
        "command": "docker",
        "args": [
          "run", "-i", "--rm",
          "--network", "devdocs-network",
          "-e", "DEVDOCS_HYBRID=true",
          "-e", "DEVDOCS_LOCAL_URL=http://devdocs-local:9292",
          "-v", "devdocs-cache:/root/.cache/devdocs-mcp",
          "devdocs-mcp:latest"
        ]
      }
    }
  }
}
```

#### Variables de entorno del modo híbrido

| Variable | Valores | Descripción |
|----------|---------|-------------|
| `DEVDOCS_HYBRID` | `true`/`false` | Habilitar modo híbrido |
| `DEVDOCS_LOCAL_URL` | URL | URL del servidor DevDocs local |
| `DEVDOCS_MODE` | `auto`, `local_only`, `remote_only`, `offline` | Modo de operación |

---

## ⚙️ Configuración

### GitHub Copilot (VS Code)

1. Abre VS Code
2. Presiona `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"
3. Busca la sección de MCP servers o créala
4. Añade la configuración:

#### Con Docker (Recomendado)

```json
{
  "mcp": {
    "servers": {
      "devdocs": {
        "command": "docker",
        "args": [
          "run", "-i", "--rm",
          "-v", "devdocs-cache:/root/.cache/devdocs-mcp",
          "devdocs-mcp:latest"
        ]
      }
    }
  }
}
```

#### Sin Docker (Local)

```json
{
  "mcp": {
    "servers": {
      "devdocs": {
        "command": "python",
        "args": ["-m", "devdocs_mcp.server"],
        "cwd": "E:/DevDocs/devdocs-mcp/src"
      }
    }
  }
}
```

5. Reinicia VS Code

### Claude Desktop

1. Abre el archivo de configuración:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. Añade la configuración:

```json
{
  "mcpServers": {
    "devdocs": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "devdocs-cache:/root/.cache/devdocs-mcp",
        "devdocs-mcp:latest"
      ]
    }
  }
}
```

3. Reinicia Claude Desktop

---

## 🔧 Herramientas Disponibles

### 1. `list_documentations`

Lista todas las documentaciones disponibles en DevDocs (~600).

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `filter` | string | No | Filtrar por nombre |

**Ejemplo de uso:**
> "Lista las documentaciones disponibles que contengan 'python'"

**Respuesta:**
```
## Documentaciones Disponibles (15 encontradas)

- **Python 3.10** (`python~3.10`) - v3.10
- **Python 3.11** (`python~3.11`) - v3.11
- **Python 3.12** (`python~3.12`) - v3.12
...
```

---

### 2. `search_documentation`

Busca en el índice de una tecnología específica.

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `tech` | string | Sí | Slug de la tecnología (ej: `python~3.10`) |
| `query` | string | Sí | Término de búsqueda |
| `limit` | integer | No | Máximo de resultados (default: 20) |

**Ejemplo de uso:**
> "Busca 'asyncio' en la documentación de Python 3.10"

**Respuesta:**
```
## Resultados para "asyncio" en python~3.10

Encontrados: 15 resultados

1. **asyncio** [Concurrent Execution]
   Path: `library/asyncio`

2. **asyncio.gather()** [Concurrent Execution]
   Path: `library/asyncio-task`
...
```

---

### 3. `get_page_content`

Obtiene el contenido completo de una página de documentación.

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `tech` | string | Sí | Slug de la tecnología |
| `path` | string | Sí | Path de la página |

**Ejemplo de uso:**
> "Dame el contenido de la página asyncio-task de Python 3.10"

**Respuesta:**
```markdown
# asyncio — Asynchronous I/O

asyncio is a library to write concurrent code using the async/await syntax.

## Running an asyncio Program

import asyncio

async def main():
    print('Hello')
    await asyncio.sleep(1)
    print('World')

asyncio.run(main())
...
```

---

### 4. `get_documentation_index`

Obtiene el índice completo de una documentación.

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `tech` | string | Sí | Slug de la tecnología |

**Ejemplo de uso:**
> "Dame el índice de Spring Boot"

---

### 5. `get_cache_stats`

Muestra estadísticas del caché local.

**Parámetros:** Ninguno

**Ejemplo de uso:**
> "¿Cuánto ocupa el caché de devdocs?"

**Respuesta:**
```
## Estadísticas del Caché

- **Directorio:** `/root/.cache/devdocs-mcp`
- **Archivos totales:** 156
- **Tamaño total:** 12.45 MB

### Documentaciones cacheadas:

- **python~3.10**: 45 archivos (3.2 MB)
- **spring_boot**: 89 archivos (8.1 MB)
- **react**: 22 archivos (1.15 MB)
```

---

### 6. `clear_cache`

Limpia el caché local.

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `tech` | string | No | Tecnología específica (vacío = todo) |

**Ejemplo de uso:**
> "Limpia el caché de Python 3.10"

---

### 7. `get_multiple_pages`

Obtiene múltiples páginas en una sola llamada.

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `tech` | string | Sí | Slug de la tecnología |
| `paths` | array | Sí | Lista de paths |

**Ejemplo de uso:**
> "Dame las páginas de asyncio, asyncio-task y asyncio-stream de Python"

---

### 8. `search_across_docs`

Busca en múltiples documentaciones a la vez.

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `query` | string | Sí | Término de búsqueda |
| `techs` | array | No | Lista de tecnologías (default: populares) |
| `limit_per_tech` | integer | No | Máximo por tecnología (default: 5) |

**Ejemplo de uso:**
> "Busca 'websocket' en Python, JavaScript y Node.js"

**Respuesta:**
```
## Búsqueda: 'websocket'

Tecnologías buscadas: 3 | Total resultados: 12

### 📚 python~3.10 (4 resultados)
- **websockets** → `library/websockets`
...

### 📚 javascript (5 resultados)
- **WebSocket** → `global_objects/websocket`
...

### 📚 node (3 resultados)
- **WebSocket** → `ws`
...
```

---

### 9. `get_type_entries`

Filtra entradas por tipo (class, function, method, etc.).

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `tech` | string | Sí | Slug de la tecnología |
| `entry_type` | string | Sí | Tipo a filtrar |
| `limit` | integer | No | Máximo de resultados (default: 50) |

**Ejemplo de uso:**
> "Lista todas las funciones built-in de Python 3.10"

---

### 10. `get_examples`

Extrae solo los bloques de código de una página.

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `tech` | string | Sí | Slug de la tecnología |
| `path` | string | Sí | Path de la página |

**Ejemplo de uso:**
> "Dame solo los ejemplos de código de asyncio.gather"

---

### 11. `export_documentation`

Exporta documentación completa a archivos locales.

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `tech` | string | Sí | Slug de la tecnología |
| `output_dir` | string | Sí | Directorio de salida |
| `max_pages` | integer | No | Límite de páginas |

**Ejemplo de uso:**
> "Exporta toda la documentación de React a ./react_docs"

⚠️ **Advertencia**: Puede tomar varios minutos para documentaciones grandes.

---

### 12. `offline_mode_status`

Muestra qué documentaciones están disponibles offline.

**Parámetros:** Ninguno

**Ejemplo de uso:**
> "¿Qué documentaciones tengo disponibles offline?"

**Respuesta:**
```
## Estado Offline

- **Directorio caché:** `/root/.cache/devdocs-mcp`
- **Tecnologías disponibles offline:** 3
- **Tamaño total:** 12.45 MB

### Documentaciones en caché:

- **python~3.10**: 45 páginas (3.2 MB) | Índice: ✅
- **spring_boot**: 89 páginas (8.1 MB) | Índice: ✅
- **react**: 22 páginas (1.15 MB) | Índice: ✅
```

---

### 13. `get_hybrid_status` ⚡ NEW

Muestra el estado del modo híbrido.

**Parámetros:** Ninguno

**Ejemplo de uso:**
> "¿Está habilitado el modo híbrido? ¿El servidor local está disponible?"

**Respuesta:**
```
## 🔄 Estado del Modo Híbrido

| Configuración | Valor |
|---------------|-------|
| **Modo Híbrido** | ✅ Habilitado |
| **Modo Actual** | `auto` - Local → Cache → Remote (fallback automático) |
| **Servidor Local** | ✅ http://devdocs-local:9292 |
| **Última Fuente** | `local` |

### 📦 Caché
- **Tamaño:** 12.45 MB
- **Archivos:** 156
```

---

### 14. `configure_hybrid_mode` ⚡ NEW

Configura el modo de operación híbrido.

**Parámetros:**
| Nombre | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `mode` | string | No | `auto`, `local_only`, `remote_only`, `offline` |
| `local_url` | string | No | URL del servidor DevDocs local |
| `enable` | boolean | No | Habilitar/deshabilitar modo híbrido |

**Modos disponibles:**
| Modo | Descripción |
|------|-------------|
| `auto` | Local → Cache → Remote (recomendado) |
| `local_only` | Solo servidor local, falla si no disponible |
| `remote_only` | Solo API remota (comportamiento original) |
| `offline` | Solo caché, nunca hace peticiones de red |

**Ejemplo de uso:**
> "Configura el modo híbrido para funcionar solo offline"

**Respuesta:**
```
## ⚙️ Configuración Actualizada

### Cambios aplicados:
- 🔄 Modo: `offline` (Solo caché)

### Estado actual:
- **Híbrido:** ✅ Habilitado
- **Modo:** `offline`
- **Local disponible:** ✅ Sí
```

---

## 💡 Ejemplos de Uso

### Caso 1: Aprender una nueva biblioteca

```
Usuario: "Necesito aprender a usar asyncio en Python. 
         ¿Puedes buscar la documentación y explicarme los conceptos básicos?"

Copilot: [Usa search_documentation para buscar asyncio]
         [Usa get_page_content para obtener la documentación]
         
         "Según la documentación oficial de Python 3.10..."
```

### Caso 2: Comparar implementaciones

```
Usuario: "¿Cómo se manejan las promesas en JavaScript vs Python?"

Copilot: [Usa search_across_docs con query="promise" en javascript y python]
         [Usa get_page_content para obtener detalles de cada uno]
         
         "Comparando ambas documentaciones..."
```

### Caso 3: Buscar ejemplos específicos

```
Usuario: "Dame ejemplos de código de cómo usar fetch en JavaScript"

Copilot: [Usa get_examples con tech="javascript" path="global_objects/fetch"]
         
         "Aquí tienes los ejemplos de la documentación oficial..."
```

### Caso 4: Trabajo offline

```
Usuario: "Voy a estar sin internet. ¿Puedes cachear la documentación de React?"

Copilot: [Usa get_documentation_index para cachear el índice]
         [Usa get_multiple_pages para cachear páginas principales]
         
         "Listo, la documentación de React está disponible offline."
```

---

## 💾 Sistema de Caché

### Estructura del Caché

```
~/.cache/devdocs-mcp/
├── docs_list.json           # Lista de todas las documentaciones
├── python~3.10/
│   ├── index.json           # Índice de Python 3.10
│   └── pages/
│       ├── library_asyncio.json
│       ├── library_asyncio-task.json
│       └── ...
├── spring_boot/
│   ├── index.json
│   └── pages/
│       └── ...
└── react/
    └── ...
```

### Política de Caché

| Aspecto | Comportamiento |
|---------|----------------|
| **TTL** | Sin expiración (las docs son versionadas) |
| **Persistencia** | Permanente hasta limpieza manual |
| **Ubicación** | `~/.cache/devdocs-mcp/` (local) o volumen Docker |
| **Formato** | JSON para índices, Markdown para contenido |

### Comandos útiles para el caché

```bash
# Ver contenido del caché (Docker)
docker run --rm -v devdocs-cache:/cache alpine ls -laR /cache

# Ver tamaño del volumen
docker system df -v | grep devdocs

# Limpiar volumen completamente
docker volume rm devdocs-cache
```

---

## 🌐 API de DevDocs

DevDocs MCP se conecta a la API pública de DevDocs:

### Endpoints

| Endpoint | Descripción |
|----------|-------------|
| `https://devdocs.io/docs.json` | Lista todas las documentaciones |
| `https://documents.devdocs.io/{tech}/index.json` | Índice de una tecnología |
| `https://documents.devdocs.io/{tech}/{path}.html` | Contenido HTML de una página |

### Estructura de docs.json

```json
[
  {
    "name": "Python",
    "slug": "python~3.10",
    "type": "python",
    "version": "3.10",
    "release": "3.10.0",
    "mtime": 1634567890,
    "db_size": 12345678
  }
]
```

### Estructura de index.json

```json
{
  "entries": [
    {
      "name": "asyncio",
      "path": "library/asyncio",
      "type": "Concurrent Execution"
    },
    {
      "name": "asyncio.gather()",
      "path": "library/asyncio-task#asyncio.gather",
      "type": "Concurrent Execution"
    }
  ],
  "types": [
    {"name": "Built-in Functions", "count": 69},
    {"name": "Concurrent Execution", "count": 45}
  ]
}
```

---

## 🛠 Desarrollo

### Ejecutar en modo desarrollo

```bash
cd devdocs-mcp

# Instalar dependencias
pip install -e .

# Ejecutar tests
python test_mcp.py

# Probar herramientas manualmente
python -c "
from devdocs_mcp.api import DevDocsAPI
api = DevDocsAPI()
results = api.search_in_index('python~3.10', 'asyncio', limit=5)
print(results)
"
```

### Estructura de archivos

| Archivo | Responsabilidad |
|---------|-----------------|
| `server.py` | Servidor MCP, definición de tools, handlers |
| `api.py` | Cliente HTTP para DevDocs API |
| `cache.py` | Sistema de caché en disco |
| `utils.py` | Conversión HTML → Markdown |

### Agregar una nueva herramienta

1. **Agregar método en `api.py`**:
```python
def mi_nueva_funcion(self, param: str) -> dict:
    """Descripción de la función"""
    # Implementación
    return resultado
```

2. **Agregar Tool en `server.py`**:
```python
Tool(
    name="mi_nueva_tool",
    description="Descripción para el modelo",
    inputSchema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "..."}
        },
        "required": ["param"]
    }
)
```

3. **Agregar handler en `server.py`**:
```python
elif name == "mi_nueva_tool":
    result = await handle_mi_nueva_tool(arguments)

async def handle_mi_nueva_tool(args: dict) -> str:
    param = args.get('param', '')
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, api.mi_nueva_funcion, param)
    return formatear_resultado(result)
```

---

## 🔧 Solución de Problemas

### El servidor no inicia

```bash
# Verificar que Docker está corriendo
docker info

# Verificar que la imagen existe
docker images devdocs-mcp

# Reconstruir la imagen
docker build -t devdocs-mcp:latest -f docker/Dockerfile .
```

### No aparecen las herramientas en Copilot

1. Verificar configuración MCP en VS Code settings
2. Reiniciar VS Code completamente
3. Verificar logs: `View > Output > GitHub Copilot`

### Error de conexión a DevDocs

```bash
# Verificar conectividad
curl https://devdocs.io/docs.json

# Verificar desde Docker
docker run --rm devdocs-mcp:latest python -c "
import httpx
r = httpx.get('https://devdocs.io/docs.json', follow_redirects=True)
print(f'Status: {r.status_code}')
"
```

### Caché corrupto

```bash
# Limpiar caché (Docker)
docker volume rm devdocs-cache

# Limpiar caché (Local)
rm -rf ~/.cache/devdocs-mcp
```

### Ver logs del servidor

```bash
# Ejecutar manualmente para ver errores
docker run -it --rm devdocs-mcp:latest

# Con más detalle
docker run -it --rm devdocs-mcp:latest python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from devdocs_mcp.server import main
main()
"
```

---

## 📊 Rendimiento

### Tiempos típicos

| Operación | Primera vez | Con caché |
|-----------|-------------|-----------|
| `list_documentations` | ~500ms | ~10ms |
| `search_documentation` | ~300ms | ~5ms |
| `get_page_content` | ~200ms | ~5ms |
| `search_across_docs` (9 techs) | ~2s | ~50ms |

### Tamaño de caché por tecnología

| Tecnología | Páginas | Tamaño aprox. |
|------------|---------|---------------|
| Python 3.10 | ~450 | ~15 MB |
| React | ~80 | ~3 MB |
| JavaScript | ~200 | ~8 MB |
| Spring Boot | ~150 | ~12 MB |

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 🙏 Agradecimientos

- [DevDocs.io](https://devdocs.io) por proporcionar la API de documentación
- [Anthropic](https://anthropic.com) por el protocolo MCP
- [Model Context Protocol](https://modelcontextprotocol.io) por la especificación

---

## 👨‍💻 Autor

<div align="center">

**Javier Garcia** · [@JavierDevCol](https://github.com/JavierDevCol)

[![GitHub](https://img.shields.io/badge/GitHub-JavierDevCol-181717?style=for-the-badge&logo=github)](https://github.com/JavierDevCol)

</div>

---

<div align="center">

**[⬆ Volver arriba](#-devdocs-mcp-server)**

Hecho con ❤️ para la comunidad de desarrolladores

</div>
