#!/usr/bin/env python

import modal

# Create Modal image with dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("universal-tool-server")
)

app = modal.App("mcp-tool-server")

@app.function(
    image=image,
    keep_warm=1,
    container_idle_timeout=600,
)
@modal.web_endpoint(method="GET")
def health():
    return {"status": "ok"}

@app.function(
    image=image, 
    keep_warm=1,
    container_idle_timeout=600,
)
@modal.asgi_app()
def mcp_server():
    from universal_tool_server import Server
    
    # Create MCP-enabled server (no auth when using MCP)
    app_instance = Server(enable_mcp=True)
    
    # Add your tools
    @app_instance.add_tool()
    async def echo(msg: str) -> str:
        """Echo a message."""
        return msg + "!"

    @app_instance.add_tool()
    async def add(x: int, y: int) -> int:
        """Add two numbers."""
        return x + y

    @app_instance.add_tool()
    async def say_hello() -> str:
        """Say hello."""
        return "Hello from Modal MCP Server!"
    
    return app_instance