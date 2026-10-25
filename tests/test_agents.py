import pytest
from app.services.agents.tools import safe_eval_expr, TOOL_REGISTRY, tool_calculator, tool_current_time
from app.services.agents.framework import CustomAgent


def test_safe_ast_calculator():
    """Verifies that the safe calculator performs exact math and rejects unsafe code."""
    assert safe_eval_expr("120 * 4 + 10") == 490.0
    assert safe_eval_expr("(50 / 2) - 5") == 20.0
    assert safe_eval_expr("2 ** 8") == 256.0

    # Unsafe code injection must raise ValueError
    with pytest.raises(ValueError):
        safe_eval_expr("__import__('os').system('dir')")


def test_tool_registry():
    """Verifies required safe tools are registered."""
    assert "calculator" in TOOL_REGISTRY
    assert "current_time" in TOOL_REGISTRY
    assert "search_documents" in TOOL_REGISTRY

    res = tool_current_time()
    assert "utc_time" in res
    assert "day_of_week" in res


def test_agent_iteration_limit():
    """Verifies that CustomAgent honors max_iterations limits."""
    agent = CustomAgent(max_iterations=2)
    assert agent.max_iterations == 2
