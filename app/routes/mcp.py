from flask import Blueprint, render_template, request, jsonify
from app.services.mcp.service import MCPManagerService
from app.services.providers.factory import get_providers_status

mcp_bp = Blueprint("mcp", __name__)


@mcp_bp.route("/mcp")
def mcp_inspector():
    """Renders the Model Context Protocol visual inspector dashboard."""
    mcp_service = MCPManagerService()
    meta = mcp_service.get_server_metadata()
    tools = mcp_service.list_tools()
    resources = mcp_service.list_resources()
    provider_status = get_providers_status()

    return render_template(
        "mcp.html",
        server_meta=meta,
        tools=tools,
        resources=resources,
        provider_status=provider_status,
    )


@mcp_bp.route("/api/mcp/tools")
def get_mcp_tools():
    """Returns discovered tools from the MCP server."""
    mcp_service = MCPManagerService()
    return jsonify({
        "server": mcp_service.get_server_metadata(),
        "tools": mcp_service.list_tools(),
        "resources": mcp_service.list_resources(),
    })


@mcp_bp.route("/api/mcp/invoke", methods=["POST"])
def invoke_mcp_tool():
    """Invokes a discovered MCP tool and returns timing and output."""
    data = request.get_json() or {}
    tool_name = data.get("tool_name")
    arguments = data.get("arguments", {})

    if not tool_name:
        return jsonify({"error": "Tool name is required."}), 400

    mcp_service = MCPManagerService()
    result = mcp_service.invoke_tool(tool_name=tool_name, arguments=arguments)
    return jsonify(result)
