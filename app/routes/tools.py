import time
from flask import Blueprint, render_template, request, jsonify
from app.services.agents.tools import TOOL_REGISTRY
from app.services.providers.factory import get_provider, get_providers_status

tools_bp = Blueprint("tools", __name__)


@tools_bp.route("/tools")
def tools_lab():
    """Renders the interactive AI Tool & Function Calling playground."""
    tool_list = []
    for k, v in TOOL_REGISTRY.items():
        tool_list.append({
            "name": k,
            "description": v["description"],
            "parameters": v["parameters"],
            "is_sensitive": v.get("is_sensitive", False),
        })

    provider_status = get_providers_status()
    return render_template(
        "tools.html",
        tools=tool_list,
        provider_status=provider_status,
    )


@tools_bp.route("/api/tools/list")
def list_tools():
    """Returns JSON array of registered safe tools with parameter schemas."""
    return jsonify([
        {
            "name": k,
            "description": v["description"],
            "parameters": v["parameters"],
            "is_sensitive": v.get("is_sensitive", False),
        }
        for k, v in TOOL_REGISTRY.items()
    ])


@tools_bp.route("/api/tools/execute", methods=["POST"])
def execute_tool():
    """Directly executes a safe tool from the registry with duration tracking."""
    data = request.get_json() or {}
    tool_name = data.get("tool_name")
    tool_args = data.get("arguments", {})

    if tool_name not in TOOL_REGISTRY:
        return jsonify({"error": f"Unknown tool: '{tool_name}'"}), 404

    handler = TOOL_REGISTRY[tool_name]["handler"]
    start_time = time.perf_counter()
    try:
        if isinstance(tool_args, dict):
            res = handler(**tool_args)
        else:
            res = handler(tool_args)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return jsonify({
            "success": True,
            "tool_name": tool_name,
            "arguments": tool_args,
            "result": res,
            "latency_ms": round(elapsed_ms, 2),
        })
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return jsonify({
            "success": False,
            "tool_name": tool_name,
            "error": str(e),
            "latency_ms": round(elapsed_ms, 2),
        }), 400
