from flask import Blueprint, render_template, request, jsonify
from app.services.agents.framework import CustomAgent
from app.services.agents.tools import TOOL_REGISTRY
from app.services.providers.factory import get_providers_status

agents_bp = Blueprint("agents", __name__)


@agents_bp.route("/agents")
def agents_lab():
    """Renders the AI Agent workbench and execution visualizer."""
    provider_status = get_providers_status()
    tools = [
        {"name": k, "description": v["description"], "is_sensitive": v.get("is_sensitive", False)}
        for k, v in TOOL_REGISTRY.items()
    ]
    return render_template(
        "agents.html",
        provider_status=provider_status,
        tools=tools,
    )


@agents_bp.route("/api/agents/run", methods=["POST"])
def run_agent():
    """Starts or resumes a multi-step agent loop."""
    data = request.get_json() or {}
    goal = data.get("goal", "").strip()
    provider_name = data.get("provider")
    model_name = data.get("model")
    max_iters = int(data.get("max_iterations", 5))

    human_approval = bool(data.get("human_approval_granted", False))
    approved_action = data.get("approved_action")

    if not goal:
        return jsonify({"error": "Goal cannot be empty."}), 400

    agent = CustomAgent(
        provider_name=provider_name,
        model_name=model_name,
        max_iterations=max_iters,
    )

    result = agent.run(
        goal=goal,
        human_approval_granted=human_approval,
        approved_action=approved_action,
    )
    return jsonify(result)
