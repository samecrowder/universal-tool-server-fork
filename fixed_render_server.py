#!/usr/bin/env python
"""
Fixed MCP-enabled Universal Tool Server for Render deployment
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route

from universal_tool_server import __version__
from universal_tool_server.auth import Auth
from universal_tool_server.splash import SPLASH
from universal_tool_server.tools import ToolHandler, create_tools_router
from universal_tool_server import root

# Create a custom MCP app with fixed routing
def create_fixed_mcp_app(tool_handler: ToolHandler) -> Starlette:
    """Create a Starlette app for an MCP server with fixed routing."""
    from mcp.server.lowlevel import Server as MCPServer
    from mcp.server.sse import SseServerTransport
    from mcp.types import Tool
    from universal_tool_server.mcp import _convert_to_content, CallToolRequest

    # Use relative path for SSE transport - this fixes the double /mcp issue
    sse = SseServerTransport("/messages/")
    server = MCPServer(name="MCP Server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        tools = []
        for tool in await tool_handler.list_tools(request=None):
            if tool_handler.latest_version[tool["name"]]["id"] != tool["id"]:
                continue
            tools.append(
                Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["input_schema"],
                )
            )
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Call a tool by name with arguments."""
        call_tool_request: CallToolRequest = {
            "tool_id": name,
            "input": arguments,
        }
        response = await tool_handler.call_tool(call_tool_request, request=None)
        if not response["success"]:
            raise NotImplementedError("Support for error messages is not yet implemented.")
        return _convert_to_content(response["value"])

    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())

    starlette_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )
    return starlette_app

# Create the main server
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(SPLASH)
    yield

app = FastAPI(
    version=__version__,
    lifespan=lifespan,
    title="Universal Tool Server",
)

# Add root routes
app.include_router(root.router)

# Create tool handler and tools router
tool_handler = ToolHandler()
tools_router = create_tools_router(tool_handler)
app.include_router(tools_router, prefix="/tools")

# Mount the fixed MCP app
app.mount("/mcp", create_fixed_mcp_app(tool_handler))

# Add example tools
async def echo(msg: str) -> str:
    """Echo a message with exclamation."""
    return msg + "!"

async def add(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y

async def say_hello() -> str:
    """Say hello message."""
    return "Hello from Universal Tool Server on Render!"

async def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y

# Register the tools
tool_handler.add(echo)
tool_handler.add(add) 
tool_handler.add(say_hello)
tool_handler.add(multiply)

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)