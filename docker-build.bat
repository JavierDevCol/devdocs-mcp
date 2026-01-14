@echo off
REM ══════════════════════════════════════════════════════════════
REM                Build DevDocs MCP Docker Image
REM ══════════════════════════════════════════════════════════════

echo Building DevDocs MCP Docker image...
docker build -t devdocs-mcp:latest .

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build successful!
    echo.
    echo To run interactively:
    echo   docker run -it --rm -v devdocs-cache:/root/.cache/devdocs-mcp devdocs-mcp:latest
    echo.
    echo To use with Claude Desktop, add to your config:
    echo   "devdocs": {
    echo     "command": "docker",
    echo     "args": ["run", "-i", "--rm", "-v", "devdocs-cache:/root/.cache/devdocs-mcp", "devdocs-mcp:latest"]
    echo   }
) else (
    echo.
    echo ❌ Build failed!
)
