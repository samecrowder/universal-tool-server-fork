#!/usr/bin/env python
"""
MCP-enabled Universal Tool Server for Render deployment
"""

from universal_tool_server import Server

# Create MCP-enabled server (no auth when using MCP)
app = Server(enable_mcp=True)

# Add example tools
@app.add_tool()
async def echo(msg: str) -> str:
    """Echo a message with exclamation."""
    return msg + "!"

@app.add_tool()
async def add(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y

@app.add_tool()
async def say_hello() -> str:
    """Say hello message."""
    return "Hello from Universal Tool Server on Render!"

@app.add_tool()
async def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)