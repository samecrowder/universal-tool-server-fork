#!/usr/bin/env python
"""
Test client for Streamable HTTP MCP server
"""

import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.streamable_http import StreamableHTTPTransport

async def main():
    # Streamable HTTP MCP server URL - no /sse suffix needed!
    url = "http://localhost:8001/mcp"
    
    print(f"Connecting to Streamable HTTP MCP server: {url}")
    
    try:
        # Create Streamable HTTP transport
        transport = StreamableHTTPTransport(url)
        
        # Connect and get streams
        async with transport.connect() as (read_stream, write_stream):
            # Create MCP client session with the streams
            client = ClientSession(read_stream, write_stream)
            
            # Initialize the session
            await client.initialize()
            print("✅ Connected to MCP server!")
            
            # List available tools
            print("\n📋 Available tools:")
            tools_result = await client.list_tools()
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            print("\n🔧 Testing tools:")
            
            # Test echo tool
            print("\n1. Testing 'echo' tool...")
            result = await client.call_tool("echo", {"msg": "Hello Streamable HTTP!"})
            print(f"   Result: {result.content[0].text}")
            
            # Test add tool
            print("\n2. Testing 'add' tool...")
            result = await client.call_tool("add", {"x": 25, "y": 17})
            print(f"   Result: {result.content[0].text}")
            
            # Test multiply tool
            print("\n3. Testing 'multiply' tool...")
            result = await client.call_tool("multiply", {"x": 4.5, "y": 3.0})
            print(f"   Result: {result.content[0].text}")
            
            # Test say_hello tool
            print("\n4. Testing 'say_hello' tool...")
            result = await client.call_tool("say_hello", {})
            print(f"   Result: {result.content[0].text}")
            
            print("\n🎉 All Streamable HTTP tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Make sure the server is running on localhost:8001")
        print("2. Check that the server supports Streamable HTTP at /mcp")
        print("3. Verify the server logs for any errors")

if __name__ == "__main__":
    asyncio.run(main())