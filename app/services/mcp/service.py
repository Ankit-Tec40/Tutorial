import asyncio
import time
import logging
from typing import Dict, Any, List
from mcp_servers.lab_mcp_server import server as lab_server

logger = logging.getLogger(__name__)


class MCPManagerService:
    """Manages MCP Server discovery and safe client invocation for the visual inspector."""

    def __init__(self):
        self.server = lab_server

    def get_server_metadata(self) -> Dict[str, Any]:
        """Returns MCP server info, capabilities, and connection status."""
        return {
            "name": self.server.name,
            "version": getattr(self.server, "version", "1.0.0"),
            "description": getattr(self.server, "description", "Educational MCP Server"),
            "transport": "In-Process / stdio Subprocess",
            "status": "connected",
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Discovers and inspects all registered tools and their JSON schemas."""
        try:
            tools = asyncio.run(self.server.list_tools())
            discovered = []
            for t in tools:
                discovered.append({
                    "name": t.name,
                    "description": t.description or "No description provided.",
                    "input_schema": t.input_schema or {},
                })
            return discovered
        except Exception as e:
            logger.error("Error listing MCP tools: %s", e)
            return []

    def list_resources(self) -> List[Dict[str, Any]]:
        """Discovers registered MCP resources."""
        try:
            resources = asyncio.run(self.server.list_resources())
            discovered = []
            for r in resources:
                discovered.append({
                    "uri": str(r.uri),
                    "name": getattr(r, "name", str(r.uri)),
                    "description": getattr(r, "description", ""),
                })
            return discovered
        except Exception as e:
            logger.error("Error listing MCP resources: %s", e)
            return []

    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invokes an MCP tool with validation, duration tracking, and structured result."""
        start_time = time.perf_counter()
        try:
            result = asyncio.run(self.server.call_tool(tool_name, arguments))
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            content_text = ""
            if result.content:
                parts = []
                for item in result.content:
                    if hasattr(item, "text"):
                        parts.append(item.text)
                    else:
                        parts.append(str(item))
                content_text = "\n".join(parts)

            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "success": not getattr(result, "is_error", False),
                "result": content_text,
                "duration_ms": round(elapsed_ms, 2),
                "error": None,
            }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("MCP tool invocation error (%s): %s", tool_name, e)
            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "success": False,
                "result": None,
                "duration_ms": round(elapsed_ms, 2),
                "error": str(e),
            }
