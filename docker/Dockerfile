# ══════════════════════════════════════════════════════════════
#                    DevDocs MCP Server
#                    Docker Container
# ══════════════════════════════════════════════════════════════

FROM python:3.12-slim

LABEL maintainer="DevDocs MCP Team"
LABEL description="MCP server for querying DevDocs API documentation"

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos del proyecto
COPY pyproject.toml .
COPY src/ ./src/

# Instalar el paquete
RUN pip install --no-cache-dir -e .

# Crear directorio para caché persistente
RUN mkdir -p /root/.cache/devdocs-mcp

# Volumen para persistir el caché
VOLUME ["/root/.cache/devdocs-mcp"]

# El servidor MCP usa stdio, no expone puertos HTTP
# Se comunica via stdin/stdout

# Comando por defecto
CMD ["devdocs-mcp"]
