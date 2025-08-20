#!/usr/bin/env python

import modal

# Create Modal image with dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("universal-tool-server")
)

app = modal.App("mcp-tool-server-simple")

@app.function(
    image=image,
    keep_warm=1,
    container_idle_timeout=600,
)
def serve_mcp():
    """Run the MCP server"""
    import uvicorn
    from universal_tool_server import Server
    
    # Create MCP-enabled server
    server_app = Server(enable_mcp=True)
    
    # Add tools
    @server_app.add_tool()
    async def echo(msg: str) -> str:
        """Echo a message."""
        return msg + "!"

    @server_app.add_tool()
    async def add(x: int, y: int) -> int:
        """Add two numbers."""
        return x + y

    @server_app.add_tool()
    async def say_hello() -> str:
        """Say hello."""
        return "Hello from Modal MCP Server!"
    
    # Run with uvicorn
    uvicorn.run(server_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    with app.run():
        serve_mcp.remote()