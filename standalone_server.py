#!/usr/bin/env python
"""
Standalone Universal Tool Server for Render deployment
Contains all code inline to avoid dependency on published package
"""

import asyncio
import inspect
import json
import os
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar

from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from langchain_core.tools import BaseTool
from pydantic import BaseModel
import uvicorn

T = TypeVar("T", bound=Callable)

# Tool handler - simplified version
class CallToolRequest(BaseModel):
    tool_id: str
    input: Dict[str, Any]

class ToolHandler:
    def __init__(self):
        self.tools = {}
        self.latest_version = {}
        
    def add(self, fn: Callable, permissions: List[str] = None, version: str = "1.0.0"):
        tool_name = fn.__name__
        tool_id = f"{tool_name}_{version}"
        
        # Get function signature for input schema
        sig = inspect.signature(fn)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            param_type = param.annotation
            if param_type == int:
                json_type = "integer"
            elif param_type == float:
                json_type = "number"
            elif param_type == bool:
                json_type = "boolean"
            else:
                json_type = "string"
            
            properties[param_name] = {"type": json_type}
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        input_schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
        self.tools[tool_id] = {
            "id": tool_id,
            "name": tool_name,
            "description": fn.__doc__ or f"{tool_name} tool",
            "input_schema": input_schema,
            "function": fn,
            "permissions": permissions or []
        }
        
        self.latest_version[tool_name] = {"id": tool_id}
    
    async def list_tools(self, request=None):
        return list(self.tools.values())
    
    async def call_tool(self, call_request: CallToolRequest, request=None):
        tool_name = call_request.tool_id
        
        # Find tool by name
        tool = None
        for t in self.tools.values():
            if t["name"] == tool_name:
                tool = t
                break
        
        if not tool:
            return {"success": False, "error": f"Tool {tool_name} not found"}
        
        try:
            result = tool["function"](**call_request.input)
            if asyncio.iscoroutine(result):
                result = await result
            return {"success": True, "value": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

# MCP Router
def create_mcp_router(tool_handler: ToolHandler) -> APIRouter:
    """Create a FastAPI router for MCP endpoints."""
    
    router = APIRouter()

    @router.get("/mcp")
    @router.get("/mcp/")
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

    @router.post("/mcp")
    @router.post("/mcp/")
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
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "Universal Tool Server",
                        "version": "1.0.0"
                    }
                }
            })

        elif method == "notifications/initialized":
            return JSONResponse({"jsonrpc": "2.0"})

        elif method == "tools/list":
            tools_list = []
            tools = await tool_handler.list_tools(request=None)
            
            for tool in tools:
                if tool_handler.latest_version[tool["name"]]["id"] == tool["id"]:
                    tools_list.append({
                        "name": tool["name"],
                        "description": tool["description"],
                        "inputSchema": tool["input_schema"]
                    })

            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools_list}
            })

        elif method == "tools/call":
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            try:
                call_tool_request = CallToolRequest(tool_id=tool_name, input=arguments)
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

                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": str(response["value"])}]
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

# Main FastAPI app
app = FastAPI(title="Universal Tool Server", version="1.0.0")
tool_handler = ToolHandler()

# Add MCP router
mcp_router = create_mcp_router(tool_handler)
app.include_router(mcp_router)

# Tool decorator
def add_tool(permissions: List[str] = None, version: str = "1.0.0"):
    def decorator(fn):
        tool_handler.add(fn, permissions=permissions, version=version)
        return fn
    return decorator

# Define tools
@add_tool()
async def echo(msg: str) -> str:
    """Echo a message with exclamation."""
    return msg + "!"

@add_tool()
async def add(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y

@add_tool()
async def say_hello() -> str:
    """Say hello message."""
    return "Hello from Standalone Universal Tool Server!"

@add_tool()
async def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Universal Tool Server", "mcp_endpoint": "/mcp"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)