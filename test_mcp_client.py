#!/usr/bin/env python
"""
MCP client to test the Universal Tool Server on Render
"""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    # MCP server URL - the MCP app is mounted at /mcp, SSE endpoint is at /sse within that
    url = "https://universal-tool-server-mcp.onrender.com/mcp/sse"
    
    print(f"Connecting to MCP server: {url}")
    
    try:
        async with sse_client(url=url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                print("✅ Connected to MCP server!")
                
                # Initialize the session
                await session.initialize()
                print("✅ Session initialized")
                
                # List available tools
                print("\n📋 Available tools:")
                tools = await session.list_tools()
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                print("\n🔧 Testing tools:")
                
                # Test echo tool
                print("\n1. Testing 'echo' tool...")
                result = await session.call_tool("echo", {"msg": "Hello MCP!"})
                print(f"   Result: {result.content[0].text}")
                
                # Test add tool
                print("\n2. Testing 'add' tool...")
                result = await session.call_tool("add", {"x": 15, "y": 27})
                print(f"   Result: {result.content[0].text}")
                
                # Test multiply tool
                print("\n3. Testing 'multiply' tool...")
                result = await session.call_tool("multiply", {"x": 3.5, "y": 2.0})
                print(f"   Result: {result.content[0].text}")
                
                # Test say_hello tool
                print("\n4. Testing 'say_hello' tool...")
                result = await session.call_tool("say_hello", {})
                print(f"   Result: {result.content[0].text}")
                
                print("\n🎉 All tests completed successfully!")
                
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the server is running")
        print("2. Check the URL is correct")
        print("3. Verify the server has MCP enabled")

if __name__ == "__main__":
    asyncio.run(main())