from typing import Annotated

from starlette.requests import Request

from open_tool_server import Server
from open_tool_server.tools import InjectedRequest

app = Server(enable_mcp=True)


@app.tool()
async def echo(msg: str) -> str:
    """Echo a message."""
    return msg + "!"


@app.tool
async def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y


@app.tool()
async def say_hello() -> str:
    """Say hello."""
    return "Hello"


@app.tool()
async def unavailable_tool(request: Annotated[Request, InjectedRequest]) -> str:
    """Tool not show up with MCP due to the injected request not being available."""
    return "Hello"
