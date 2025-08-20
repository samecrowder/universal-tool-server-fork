from __future__ import annotations

import json
from itertools import chain
from typing import TYPE_CHECKING, Any, Sequence

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from universal_tool_server.tools import CallToolRequest, ToolHandler

if TYPE_CHECKING:
    from mcp.types import EmbeddedResource, ImageContent, TextContent

MCP_APP_PREFIX = "/mcp"


def _convert_to_content(
    result: Any,
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Convert a result to a sequence of content objects."""
    # This code comes directly from the FastMCP server.
    # Imported here as it is a private function.
    import pydantic_core
    from mcp.server.fastmcp.utilities.types import Image
    from mcp.types import EmbeddedResource, ImageContent, TextContent

    if result is None:
        return []

    if isinstance(result, (TextContent, ImageContent, EmbeddedResource)):
        return [result]

    if isinstance(result, Image):
        return [result.to_image_content()]

    if isinstance(result, (list, tuple)):
        return list(chain.from_iterable(_convert_to_content(item) for item in result))

    if not isinstance(result, str):
        try:
            result = json.dumps(pydantic_core.to_jsonable_python(result))
        except Exception:
            result = str(result)

    return [TextContent(type="text", text=result)]


def create_mcp_router(tool_handler: ToolHandler) -> APIRouter:
    """Create a FastAPI router for MCP endpoints."""
    
    router = APIRouter()

    @router.get("")
    async def mcp_get_handler():
        """Handle GET requests to MCP root - capabilities endpoint"""
        return JSONResponse({
            "jsonrpc": "2.0", 
            "result": {
                "capabilities": {
                    "tools": {}
                }
            }
        })

    @router.post("")
    async def mcp_post_handler(request: Request):
        """Handle POST requests - MCP JSON-RPC messages"""
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }, status_code=400)

        method = body.get("method")
        request_id = body.get("id")

        if method == "initialize":
            # Handle MCP initialization
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "Universal Tool Server",
                        "version": "1.0.0"
                    }
                }
            })

        elif method == "notifications/initialized":
            # Handle initialization notification (no response needed)
            return JSONResponse({"jsonrpc": "2.0"})

        elif method == "tools/list":
            # Return list of available tools
            tools_list = []
            
            # Get tools from the tool handler
            tools = await tool_handler.list_tools(request=None)
            
            for tool in tools:
                # Only return latest version of each tool
                if tool_handler.latest_version[tool["name"]]["id"] == tool["id"]:
                    tools_list.append({
                        "name": tool["name"],
                        "description": tool["description"],
                        "inputSchema": tool["input_schema"]
                    })

            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools_list
                }
            })

        elif method == "tools/call":
            # Execute tool
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            try:
                # Call the tool using the tool handler
                call_tool_request: CallToolRequest = {
                    "tool_id": tool_name,
                    "input": arguments,
                }
                response = await tool_handler.call_tool(call_tool_request, request=None)
                
                if not response["success"]:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution failed: {response.get('error', 'Unknown error')}"
                        }
                    })

                # Convert result to MCP content format
                content_items = _convert_to_content(response["value"])
                
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": item.type,
                                "text": item.text
                            }
                            for item in content_items
                        ]
                    }
                })

            except Exception as e:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution failed: {str(e)}"
                    }
                })

        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }, status_code=400)
    
    return router