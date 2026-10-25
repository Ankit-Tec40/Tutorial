import time
import json
import logging
from typing import Dict, Any, Optional
from app.extensions import db
from app.models.progress import LabRun
from app.services.providers.factory import get_provider
from app.services.embeddings.service import EmbeddingService, cosine_similarity
from app.services.rag.pipeline import RAGPipeline
from app.services.agents.framework import CustomAgent
from app.services.mcp.service import MCPManagerService

logger = logging.getLogger(__name__)


# --- Safe Lab Handlers ---

def run_lab_module1(params: Dict[str, Any]) -> Dict[str, Any]:
    """Module 1 Lab: Command-line and Web LLM Client tester."""
    prompt = params.get("prompt", "Explain what an LLM token is in 2 sentences.")
    temp = float(params.get("temperature", 0.7))
    provider_name = params.get("provider", "gemini")
    model_name = params.get("model")

    provider = get_provider(provider_name=provider_name, model_name=model_name)
    resp = provider.generate(prompt=prompt, temperature=temp)

    return {
        "output": resp.content,
        "provider": resp.provider,
        "model": resp.model,
        "tokens": {"prompt": resp.prompt_tokens, "completion": resp.completion_tokens, "total": resp.total_tokens},
        "latency_ms": resp.latency_ms,
    }


def run_lab_module2(params: Dict[str, Any]) -> Dict[str, Any]:
    """Module 2 Lab: Prompt-Testing Workbench (system vs user, temperature comparison)."""
    system_prompt = params.get("system_prompt", "You are an expert AI software architect. Be precise and concise.")
    user_prompt = params.get("user_prompt", "Compare zero-shot vs few-shot prompting.")
    temperature = float(params.get("temperature", 0.3))
    json_mode = bool(params.get("json_mode", False))
    provider_name = params.get("provider", "gemini")
    model_name = params.get("model")

    provider = get_provider(provider_name=provider_name, model_name=model_name)
    resp = provider.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        json_mode=json_mode,
    )

    return {
        "output": resp.content,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "temperature": temperature,
        "json_mode": json_mode,
        "tokens": {"prompt": resp.prompt_tokens, "completion": resp.completion_tokens, "total": resp.total_tokens},
        "latency_ms": resp.latency_ms,
    }


def run_lab_module3(params: Dict[str, Any]) -> Dict[str, Any]:
    """Module 3 Lab: Gemini Research Assistant with Structured Output."""
    topic = params.get("topic", "Vector Databases")
    provider = get_provider(provider_name="gemini")
    prompt = (
        f"Generate a structured research summary about: {topic}.\n"
        "Return a valid JSON object with keys: 'summary', 'key_advantages' (list), and 'top_use_cases' (list)."
    )
    resp = provider.generate(prompt=prompt, json_mode=True, temperature=0.2)
    return {
        "output": resp.content,
        "topic": topic,
        "provider": "gemini",
        "model": resp.model,
        "latency_ms": resp.latency_ms,
    }


def run_lab_module4(params: Dict[str, Any]) -> Dict[str, Any]:
    """Module 4 Lab: Local Ollama Assistant."""
    prompt = params.get("prompt", "How does local quantization affect LLM memory usage?")
    model_name = params.get("model")
    provider = get_provider(provider_name="ollama", model_name=model_name)
    resp = provider.generate(prompt=prompt, temperature=0.5)
    return {
        "output": resp.content,
        "provider": "ollama",
        "model": resp.model,
        "tokens": {"prompt": resp.prompt_tokens, "completion": resp.completion_tokens, "total": resp.total_tokens},
        "latency_ms": resp.latency_ms,
    }


def run_lab_module5(params: Dict[str, Any]) -> Dict[str, Any]:
    """Module 5 Lab: Semantic Search & Cosine Similarity."""
    query = params.get("query", "How do neural embeddings work?")
    documents = params.get("documents", [
        "Embeddings map words and sentences into dense vectors in continuous vector space.",
        "SQL databases organize structured data using relational tables and ACID transactions.",
        "Vector search uses cosine similarity to measure the angle between semantic vector representations.",
        "Docker containers package applications with all operating system dependencies.",
    ])

    embed_service = EmbeddingService()
    query_vec = embed_service.embed(query)

    scored = []
    for doc in documents:
        doc_vec = embed_service.embed(doc)
        score = cosine_similarity(query_vec, doc_vec)
        scored.append({"document": doc, "score": round(score, 4)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {
        "query": query,
        "rankings": scored,
        "vector_dimensions": len(query_vec),
    }


def run_lab_module6(params: Dict[str, Any]) -> Dict[str, Any]:
    """Module 6 Lab: Retrieval-Augmented Generation Grounded Question-Answering."""
    query = params.get("query", "What is the primary role of an AI agent loop?")
    provider_name = params.get("provider", "gemini")
    model_name = params.get("model")

    rag = RAGPipeline()
    result = rag.query_rag(query=query, provider_name=provider_name, model_name=model_name)
    return result


def run_lab_module7(params: Dict[str, Any]) -> Dict[str, Any]:
    """Module 7 Lab: Safe Tool & Function Calling."""
    tool_name = params.get("tool_name", "calculator")
    tool_args = params.get("tool_args", {"expression": "250 * 4 + 75"})

    from app.services.agents.tools import TOOL_REGISTRY
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Tool '{tool_name}' is not in the safe tool registry.")

    handler = TOOL_REGISTRY[tool_name]["handler"]
    start_time = time.perf_counter()
    res = handler(**tool_args)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "tool_name": tool_name,
        "arguments": tool_args,
        "execution_result": res,
        "latency_ms": round(elapsed_ms, 2),
    }


def run_lab_module8(params: Dict[str, Any]) -> Dict[str, Any]:
    """Module 8 Lab: Autonomous AI Agent ReAct Loop."""
    goal = params.get("goal", "Find the current UTC time and calculate 365 * 24.")
    provider_name = params.get("provider", "gemini")
    model_name = params.get("model")
    max_iters = int(params.get("max_iterations", 5))

    agent = CustomAgent(provider_name=provider_name, model_name=model_name, max_iterations=max_iters)
    return agent.run(goal=goal)


def run_lab_module9(params: Dict[str, Any]) -> Dict[str, Any]:
    """Module 9 Lab: Model Context Protocol Tool Discovery and Invocation."""
    tool_name = params.get("tool_name", "calculator")
    tool_args = params.get("arguments", {"expression": "1000 / 8"})

    mcp_service = MCPManagerService()
    return mcp_service.invoke_tool(tool_name=tool_name, arguments=tool_args)


# Registry of verified safe lab runners
LAB_DISPATCHER: Dict[str, Any] = {
    "lab-module1": run_lab_module1,
    "lab-module2": run_lab_module2,
    "lab-module3": run_lab_module3,
    "lab-module4": run_lab_module4,
    "lab-module5": run_lab_module5,
    "lab-module6": run_lab_module6,
    "lab-module7": run_lab_module7,
    "lab-module8": run_lab_module8,
    "lab-module9": run_lab_module9,
}


def execute_lab_example(lab_id: str, parameters: Dict[str, Any], user_id: str = "default_user") -> Dict[str, Any]:
    """Dispatches lab execution to a secure pre-defined handler and logs execution."""
    if lab_id not in LAB_DISPATCHER:
        # Check prefix match for modular lesson IDs (e.g. lab-module1-client -> lab-module1)
        matched_handler = None
        for k, handler in LAB_DISPATCHER.items():
            if lab_id.startswith(k):
                matched_handler = handler
                break
        if not matched_handler:
            raise ValueError(f"Unrecognized or unauthorized lab ID: '{lab_id}'.")
        runner_fn = matched_handler
    else:
        runner_fn = LAB_DISPATCHER[lab_id]

    start_time = time.perf_counter()
    status = "success"
    error_msg = None
    output = {}

    provider_used = parameters.get("provider", "local")
    model_used = parameters.get("model", "default")

    try:
        output = runner_fn(parameters)
    except Exception as e:
        status = "error"
        error_msg = str(e)
        output = {"error": error_msg}
        logger.error("Lab execution error for %s: %s", lab_id, e)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # Persist execution run in database
    try:
        run_record = LabRun(
            user_id=user_id,
            lab_id=lab_id,
            provider=str(provider_used),
            model=str(model_used),
            parameters=parameters,
            input_payload=parameters,
            output_result=output,
            execution_time_ms=round(elapsed_ms, 2),
            status=status,
            error_message=error_msg,
        )
        db.session.add(run_record)
        db.session.commit()
    except Exception as db_err:
        db.session.rollback()
        logger.warning("Could not persist LabRun record: %s", db_err)

    return {
        "lab_id": lab_id,
        "status": status,
        "output": output,
        "error": error_msg,
        "execution_time_ms": round(elapsed_ms, 2),
    }
