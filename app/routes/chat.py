import json
import time
from flask import Blueprint, render_template, request, jsonify, Response, stream_with_context
from app.extensions import db
from app.models.chat import ChatSession, ChatMessage
from app.services.providers.factory import get_provider, get_providers_status

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat")
def workbench():
    """Renders the global AI Chat & Experimentation Workbench."""
    sessions = ChatSession.query.order_by(ChatSession.updated_at.desc()).all()
    provider_status = get_providers_status()
    return render_template(
        "chat.html",
        sessions=sessions,
        provider_status=provider_status,
    )


@chat_bp.route("/api/chat", methods=["POST"])
def send_chat():
    """Synchronous chat endpoint with conversation persistence."""
    data = request.get_json() or {}
    message_text = data.get("message", "").strip()
    session_id = data.get("session_id")
    provider_name = data.get("provider", "gemini")
    model_name = data.get("model")
    system_prompt = data.get("system_prompt", "You are an expert AI engineering assistant.")
    temperature = float(data.get("temperature", 0.7))

    if not message_text:
        return jsonify({"error": "Message cannot be empty."}), 400

    # Retrieve or create session
    session = ChatSession.query.get(session_id) if session_id else None
    if not session:
        session = ChatSession(
            title=message_text[:35] + ("..." if len(message_text) > 35 else ""),
            provider=provider_name,
            model=model_name or "default",
            system_prompt=system_prompt,
            temperature=temperature,
        )
        db.session.add(session)
        db.session.flush()

    # Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=message_text)
    db.session.add(user_msg)
    db.session.commit()

    # Gather conversation history
    history = [
        {"role": m.role, "content": m.content}
        for m in session.messages
    ]

    provider = get_provider(provider_name=provider_name, model_name=model_name)
    start_time = time.perf_counter()

    try:
        resp = provider.generate(
            prompt=message_text,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=resp.content,
            latency_ms=round(elapsed_ms, 2),
            token_usage={
                "prompt": resp.prompt_tokens,
                "completion": resp.completion_tokens,
                "total": resp.total_tokens,
            },
            tool_calls=resp.tool_calls,
        )
        db.session.add(assistant_msg)
        session.updated_at = db.func.now()
        db.session.commit()

        return jsonify({
            "session_id": session.id,
            "response": resp.content,
            "latency_ms": round(elapsed_ms, 2),
            "tokens": assistant_msg.token_usage,
            "provider": resp.provider,
            "model": resp.model,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "provider": provider_name}), 500


@chat_bp.route("/api/chat/stream", methods=["POST"])
def stream_chat():
    """Server-Sent Events (SSE) streaming chat endpoint."""
    data = request.get_json() or {}
    message_text = data.get("message", "").strip()
    provider_name = data.get("provider", "gemini")
    model_name = data.get("model")
    system_prompt = data.get("system_prompt", "You are an AI assistant.")
    temperature = float(data.get("temperature", 0.7))
    messages = data.get("messages", [{"role": "user", "content": message_text}])

    def generate_sse():
        try:
            provider = get_provider(provider_name=provider_name, model_name=model_name)
            for chunk in provider.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
            ):
                payload = json.dumps({"chunk": chunk})
                yield f"data: {payload}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            err_payload = json.dumps({"error": str(e), "done": True})
            yield f"data: {err_payload}\n\n"

    return Response(
        stream_with_context(generate_sse()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@chat_bp.route("/api/chat/compare", methods=["POST"])
def compare_models():
    """Side-by-side comparison of prompt generation across two providers/models."""
    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    system_prompt = data.get("system_prompt", "")
    temperature = float(data.get("temperature", 0.7))

    p1_name = data.get("provider1", "gemini")
    p1_model = data.get("model1")

    p2_name = data.get("provider2", "ollama")
    p2_model = data.get("model2")

    def run_one(p_name, m_name):
        start = time.perf_counter()
        try:
            prov = get_provider(provider_name=p_name, model_name=m_name)
            resp = prov.generate(prompt=prompt, system_prompt=system_prompt, temperature=temperature)
            elapsed = (time.perf_counter() - start) * 1000.0
            return {
                "success": True,
                "content": resp.content,
                "latency_ms": round(elapsed, 2),
                "tokens": resp.total_tokens,
                "model": resp.model,
                "provider": resp.provider,
            }
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000.0
            return {
                "success": False,
                "error": str(e),
                "latency_ms": round(elapsed, 2),
                "model": m_name or "default",
                "provider": p_name,
            }

    result1 = run_one(p1_name, p1_model)
    result2 = run_one(p2_name, p2_model)

    return jsonify({
        "prompt": prompt,
        "results": {
            "first": result1,
            "second": result2,
        }
    })
