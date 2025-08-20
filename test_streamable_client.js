#!/usr/bin/env node

/**
 * Test client for Streamable HTTP MCP server using JavaScript SDK
 * This mirrors exactly what OAP does
 */

const { StreamableHTTPClientTransport } = require("@modelcontextprotocol/sdk/client/streamableHttp.js");
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");

async function main() {
  // Streamable HTTP MCP server URL - matches what OAP expects
  const url = "http://localhost:8001/mcp";
  
  console.log(`Connecting to Streamable HTTP MCP server: ${url}`);
  
  try {
    // Create transport exactly like OAP does
    const connectionClient = new StreamableHTTPClientTransport(new URL(url));
    const mcp = new Client({
      name: "test-client",
      version: "1.0.0",
    });

    // Connect like OAP does
    await mcp.connect(connectionClient);
    console.log("✅ Connected to MCP server!");
    
    // List available tools
    console.log("\n📋 Available tools:");
    const tools = await mcp.listTools();
    for (const tool of tools.tools) {
      console.log(`  - ${tool.name}: ${tool.description}`);
    }
    
    console.log("\n🔧 Testing tools:");
    
    // Test echo tool
    console.log("\n1. Testing 'echo' tool...");
    const result1 = await mcp.callTool({
      name: "echo",
      arguments: { msg: "Hello Streamable HTTP from JS!" }
    });
    console.log(`   Result: ${result1.content[0].text}`);
    
    // Test add tool
    console.log("\n2. Testing 'add' tool...");
    const result2 = await mcp.callTool({
      name: "add",
      arguments: { x: 25, y: 17 }
    });
    console.log(`   Result: ${result2.content[0].text}`);
    
    // Test multiply tool
    console.log("\n3. Testing 'multiply' tool...");
    const result3 = await mcp.callTool({
      name: "multiply", 
      arguments: { x: 4.5, y: 3.0 }
    });
    console.log(`   Result: ${result3.content[0].text}`);
    
    // Test say_hello tool
    console.log("\n4. Testing 'say_hello' tool...");
    const result4 = await mcp.callTool({
      name: "say_hello",
      arguments: {}
    });
    console.log(`   Result: ${result4.content[0].text}`);
    
    console.log("\n🎉 All Streamable HTTP tests completed successfully!");
    
    // Close the connection
    await mcp.close();
    
  } catch (error) {
    console.log(`❌ Error connecting to MCP server: ${error.message}`);
    console.log(`   Error type: ${error.constructor.name}`);
    console.error(error);
    console.log("\nTroubleshooting:");
    console.log("1. Make sure the server is running on localhost:8001");
    console.log("2. Check that the server supports Streamable HTTP at /mcp");
    console.log("3. Verify the server logs for any errors");
    console.log("4. Make sure you have @modelcontextprotocol/sdk installed");
  }
}

if (require.main === module) {
  main();
}