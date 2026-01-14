#!/bin/bash
# ══════════════════════════════════════════════════════════════
#                Build DevDocs MCP Docker Image
# ══════════════════════════════════════════════════════════════
# Run this script from the project root directory:
#   ./scripts/docker-build.sh

echo "Building DevDocs MCP Docker image..."
docker build -t devdocs-mcp:latest -f docker/Dockerfile .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "To run interactively:"
    echo "  docker run -it --rm -v devdocs-cache:/root/.cache/devdocs-mcp devdocs-mcp:latest"
    echo ""
    echo "To use with Claude Desktop, add to your config:"
    cat << 'EOF'
  "devdocs": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "-v", "devdocs-cache:/root/.cache/devdocs-mcp", "devdocs-mcp:latest"]
  }
EOF
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
