"""Lab MCP Server implementation using official Model Context Protocol SDK.

Run via stdio:
    python mcp_servers/lab_mcp_server.py
"""

import sys
import os
from pathlib import Path
from mcp.server.mcpserver import MCPServer

# Initialize MCP Server
server = MCPServer(
    name="ai-engineering-lab-mcp",
    version="1.0.0",
    description="Educational MCP server demonstrating safe tools, resources, and prompts."
)

BASE_DIR = Path(__file__).resolve().parent.parent
SANDBOX_DIR = BASE_DIR / "sandbox_fs"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


# --- Safe Tools ---

@server.tool(name="calculator", description="Safely evaluates basic arithmetic expressions (+, -, *, /, %).")
def tool_calc(expression: str) -> str:
    """Safe arithmetic calculator."""
    import ast
    import operator
    ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Mod: operator.mod, ast.Pow: operator.pow
    }
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            return ops[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -_eval(node.operand)
        raise ValueError("Unsupported operation")

    try:
        res = _eval(ast.parse(expression.strip(), mode="eval").body)
        return f"Result: {res}"
    except Exception as e:
        return f"Calculation Error: {str(e)}"


@server.tool(name="notes_search", description="Searches local engineering study notes for a specific topic.")
def tool_notes(keyword: str) -> str:
    """Searches engineering notes."""
    notes = {
        "mcp": "Model Context Protocol (MCP) standardizes how AI applications connect to external data sources and tools via JSON-RPC 2.0.",
        "rag": "Retrieval-Augmented Generation enhances LLM responses with relevant passages retrieved from vector databases or semantic indexes.",
        "agent": "Autonomous AI agents use iterative ReAct or plan-and-solve loops to decompose goals into steps, execute tools, and reflect on observations.",
        "gemini": "Google Gemini offers high-speed multimodal reasoning and structured outputs through the google-genai Python SDK.",
        "ollama": "Ollama provides local, private LLM execution without external network calls, supporting open-weights models like llama3.2.",
    }
    clean_k = keyword.lower().strip()
    matches = [f"[{k.upper()}]: {v}" for k, v in notes.items() if clean_k in k or clean_k in v.lower()]
    if matches:
        return "\n\n".join(matches)
    return f"No notes found matching keyword: '{keyword}'."


@server.tool(name="approved_dir_listing", description="Lists files located strictly inside the safe sandbox workspace.")
def tool_files(subpath: str = "") -> str:
    """Restricted directory listing."""
    target = (SANDBOX_DIR / subpath).resolve()
    if not str(target).startswith(str(SANDBOX_DIR.resolve())):
        return "Access Denied: Path escapes the authorized sandbox directory."
    if not target.exists():
        return f"Directory does not exist: {subpath}"

    items = []
    for p in target.iterdir():
        kind = "DIR" if p.is_dir() else "FILE"
        items.append(f"[{kind}] {p.name} ({p.stat().st_size} bytes)")

    return "\n".join(items) if items else "Directory is empty."


# --- Resources ---

@server.resource(uri="resource://docs/intro", description="Lab Overview Documentation")
def resource_intro() -> str:
    return "AI Engineering Lab MCP Server v1.0.0. Provides educational tools for building agentic architectures."


# --- Main entry point for stdio transport ---

if __name__ == "__main__":
    import asyncio
    print("Starting AI Engineering Lab MCP Server via stdio...", file=sys.stderr)
    asyncio.run(server.run_stdio_async())
