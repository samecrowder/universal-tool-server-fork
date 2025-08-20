#!/usr/bin/env python
"""
Universal Tool Server with Streamable HTTP MCP support for deployment
"""

from universal_tool_server import Server
import os

# Create MCP-enabled server
app = Server(enable_mcp=True)

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
    return "Hello from Universal Tool Server with Streamable HTTP MCP!"

@app.add_tool()
async def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)