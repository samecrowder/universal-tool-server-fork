"""MCP client to test talking with the MCP app in the langchain-tools-server"""

import asyncio

from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    if len(sys.argv) < 2:
        print(
            "Usage: uv run client.py <URL of SSE MCP server (i.e. http://localhost:8080/mcp/sse)>"
        )
        sys.exit(1)

    url = sys.argv[1]

    if "mcp" not in url and "sse" not in url:
        raise ValueError("Use url format of [host]/mcp/sse")

    async with sse_client(url=url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(tools)
            result = await session.call_tool("echo", {"msg": "Hello, world!"})
            print(result)


if __name__ == "__main__":
    import sys

    asyncio.run(main())
