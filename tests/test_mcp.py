from app.services.mcp.service import MCPManagerService


def test_mcp_manager_discovery():
    """Verifies MCP Server tool discovery."""
    service = MCPManagerService()
    tools = service.list_tools()
    assert len(tools) > 0
    tool_names = [t["name"] for t in tools]
    assert "calculator" in tool_names
    assert "notes_search" in tool_names


def test_mcp_tool_invocation():
    """Tests invoking an MCP tool through the official SDK."""
    service = MCPManagerService()
    result = service.invoke_tool("calculator", {"expression": "500 * 2"})
    assert result["success"] is True
    assert "1000" in result["result"]
    assert result["duration_ms"] >= 0
