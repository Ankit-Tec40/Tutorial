import ast
import operator
import os
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel, Field

# Supported safe arithmetic operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval_expr(expr: str) -> float:
    """Evaluates an arithmetic expression safely using Python's AST without eval()."""
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        else:
            raise ValueError(f"Unsafe or invalid syntax in expression: {type(node).__name__}")

    try:
        parsed = ast.parse(expr.strip(), mode="eval")
        return float(_eval(parsed.body))
    except Exception as e:
        raise ValueError(f"Arithmetic evaluation error: {str(e)}")


# Tool Implementations
def tool_calculator(expression: str) -> Dict[str, Any]:
    """Safely calculates arithmetic expressions (e.g. '25 * 4 + 10')."""
    try:
        res = safe_eval_expr(expression)
        return {"expression": expression, "result": res, "status": "success"}
    except Exception as e:
        return {"expression": expression, "error": str(e), "status": "error"}


def tool_current_time(timezone: str = "UTC") -> Dict[str, Any]:
    """Returns current date, time, day of week, and ISO timestamp."""
    now = datetime.utcnow()
    return {
        "utc_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "iso_timestamp": now.isoformat() + "Z",
        "day_of_week": now.strftime("%A"),
        "timezone": timezone,
    }


def tool_simulated_weather(location: str) -> Dict[str, Any]:
    """Provides weather data (clearly tagged as simulated demonstration data)."""
    clean_loc = location.strip().title()
    # Deterministic simulation based on location hash
    temp_c = 18 + (hash(clean_loc) % 15)
    temp_f = round((temp_c * 9/5) + 32, 1)
    conditions = ["Sunny", "Partly Cloudy", "Mild Breezes", "Overcast", "Light Rain"]
    cond = conditions[abs(hash(clean_loc)) % len(conditions)]

    return {
        "location": clean_loc,
        "temperature_celsius": temp_c,
        "temperature_fahrenheit": temp_f,
        "condition": cond,
        "humidity_percent": 55 + (abs(hash(clean_loc)) % 30),
        "_notice": "SIMULATED_DATA: This is a safe simulated mock service for AI tool-calling experiments.",
    }


def tool_search_documents(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Searches indexed documents in the local RAG knowledge base."""
    from app.services.rag.pipeline import RAGPipeline
    pipeline = RAGPipeline()
    results = pipeline.retrieve(query=query, top_k=max_results)
    return {
        "query": query,
        "match_count": len(results),
        "matches": [
            {
                "filename": r["filename"],
                "excerpt": r["content"][:200] + ("..." if len(r["content"]) > 200 else ""),
                "score": r["score"],
            }
            for r in results
        ],
    }


def tool_list_sandbox_files(subdir: str = "") -> Dict[str, Any]:
    """Lists files inside the approved sandbox filesystem."""
    from flask import current_app
    sandbox_base = current_app.config["SANDBOX_DIR"]
    target_dir = (sandbox_base / subdir).resolve()

    # Security check: must not escape sandbox directory
    if not str(target_dir).startswith(str(sandbox_base.resolve())):
        return {"error": "Access denied: Path escapes sandbox boundary.", "status": "forbidden"}

    if not target_dir.exists():
        return {"files": [], "directory": str(subdir), "message": "Directory does not exist."}

    entries = []
    for item in target_dir.iterdir():
        entries.append({
            "name": item.name,
            "is_dir": item.is_dir(),
            "size_bytes": item.stat().st_size if item.is_file() else 0,
            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
        })

    return {"files": entries, "directory": str(subdir), "total": len(entries)}


def tool_write_sandbox_file(filename: str, content: str, requires_approval: bool = True) -> Dict[str, Any]:
    """Writes a text file inside the safe sandbox directory (Sensitive Action)."""
    from flask import current_app
    sandbox_base = current_app.config["SANDBOX_DIR"]
    clean_name = os.path.basename(filename)
    target_file = sandbox_base / clean_name

    target_file.write_text(content, encoding="utf-8")
    return {
        "filename": clean_name,
        "bytes_written": len(content.encode("utf-8")),
        "status": "success",
        "action": "file_written",
    }


# Tool Registry
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "calculator": {
        "name": "calculator",
        "description": "Performs exact arithmetic calculations. Supports +, -, *, /, %, ** operations.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression, e.g. '120 * 1.15 + 45'"},
            },
            "required": ["expression"],
        },
        "handler": tool_calculator,
        "is_sensitive": False,
    },
    "current_time": {
        "name": "current_time",
        "description": "Returns current UTC date and time information.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "description": "Timezone name, default UTC", "default": "UTC"},
            },
        },
        "handler": tool_current_time,
        "is_sensitive": False,
    },
    "simulated_weather": {
        "name": "simulated_weather",
        "description": "Retrieves weather conditions and temperatures for a specified city or location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or region name, e.g. 'Tokyo' or 'San Francisco'"},
            },
            "required": ["location"],
        },
        "handler": tool_simulated_weather,
        "is_sensitive": False,
    },
    "search_documents": {
        "name": "search_documents",
        "description": "Searches the local RAG knowledge base for excerpts matching the given query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query terms"},
                "max_results": {"type": "integer", "description": "Max matching documents", "default": 3},
            },
            "required": ["query"],
        },
        "handler": tool_search_documents,
        "is_sensitive": False,
    },
    "list_sandbox_files": {
        "name": "list_sandbox_files",
        "description": "Lists files and metadata within the dedicated, secure sandbox directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "subdir": {"type": "string", "description": "Optional subdirectory relative to sandbox root", "default": ""},
            },
        },
        "handler": tool_list_sandbox_files,
        "is_sensitive": False,
    },
    "write_sandbox_file": {
        "name": "write_sandbox_file",
        "description": "Writes text content into a file located strictly inside the isolated sandbox directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Target file name, e.g. 'summary.txt'"},
                "content": {"type": "string", "description": "Text content to save into the file"},
            },
            "required": ["filename", "content"],
        },
        "handler": tool_write_sandbox_file,
        "is_sensitive": True,  # Triggers human approval workflow
    },
}
