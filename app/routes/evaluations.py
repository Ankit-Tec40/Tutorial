import time
from flask import Blueprint, render_template, request, jsonify
from app.extensions import db
from app.models.evaluation import EvaluationRun
from app.services.providers.factory import get_provider, get_providers_status

eval_bp = Blueprint("evaluations", __name__)

DEFAULT_TEST_CASES = [
    {
        "id": 1,
        "input": "Explain what an LLM token is in one concise sentence.",
        "expected_keywords": ["token", "character", "subword"],
    },
    {
        "id": 2,
        "input": "What is the primary difference between zero-shot and few-shot prompting?",
        "expected_keywords": ["example", "exemplar", "context"],
    },
    {
        "id": 3,
        "input": "What does RAG stand for in artificial intelligence?",
        "expected_keywords": ["retrieval", "augmented", "generation"],
    },
    {
        "id": 4,
        "input": "Name two core principles of the Model Context Protocol (MCP).",
        "expected_keywords": ["tool", "resource", "json-rpc"],
    },
]


@eval_bp.route("/evaluations")
def eval_dashboard():
    """Renders the AI Evaluation & Benchmark dashboard."""
    past_runs = EvaluationRun.query.order_by(EvaluationRun.created_at.desc()).limit(10).all()
    provider_status = get_providers_status()
    return render_template(
        "evaluations.html",
        past_runs=past_runs,
        default_test_cases=DEFAULT_TEST_CASES,
        provider_status=provider_status,
    )


@eval_bp.route("/api/evaluations/run", methods=["POST"])
def run_evaluation():
    """Executes an automated evaluation across golden test cases."""
    data = request.get_json() or {}
    title = data.get("title", "Prompt Benchmark Run")
    provider_name = data.get("provider", "gemini")
    model_name = data.get("model")
    test_cases = data.get("test_cases", DEFAULT_TEST_CASES)

    start_suite = time.perf_counter()
    provider = get_provider(provider_name=provider_name, model_name=model_name)

    results = []
    passed_count = 0
    total_latency = 0.0

    for tc in test_cases:
        prompt_text = tc.get("input", "")
        keywords = tc.get("expected_keywords", [])

        tc_start = time.perf_counter()
        try:
            resp = provider.generate(prompt=prompt_text, temperature=0.1)
            elapsed_ms = (time.perf_counter() - tc_start) * 1000.0
            actual_text = resp.content

            matched = [k for k in keywords if k.lower() in actual_text.lower()]
            missing = [k for k in keywords if k.lower() not in actual_text.lower()]
            tc_passed = len(missing) == 0

            if tc_passed:
                passed_count += 1
            total_latency += elapsed_ms

            results.append({
                "test_case_id": tc.get("id"),
                "input": prompt_text,
                "output": actual_text,
                "passed": tc_passed,
                "matched_keywords": matched,
                "missing_keywords": missing,
                "latency_ms": round(elapsed_ms, 2),
            })
        except Exception as e:
            elapsed_ms = (time.perf_counter() - tc_start) * 1000.0
            total_latency += elapsed_ms
            results.append({
                "test_case_id": tc.get("id"),
                "input": prompt_text,
                "output": f"Error: {str(e)}",
                "passed": False,
                "error": str(e),
                "latency_ms": round(elapsed_ms, 2),
            })

    total_tests = len(test_cases)
    pass_rate = round((passed_count / total_tests * 100), 1) if total_tests > 0 else 0
    avg_latency = round(total_latency / total_tests, 2) if total_tests > 0 else 0

    run_record = EvaluationRun(
        title=title,
        eval_type="golden_dataset",
        provider=provider.name,
        model=provider.model_name,
        test_cases=test_cases,
        results=results,
        metrics={
            "total_tests": total_tests,
            "passed": passed_count,
            "pass_rate": pass_rate,
            "avg_latency_ms": avg_latency,
            "total_duration_ms": round((time.perf_counter() - start_suite) * 1000.0, 2),
        },
        status="completed",
    )
    db.session.add(run_record)
    db.session.commit()

    return jsonify({
        "run_id": run_record.id,
        "title": title,
        "provider": provider.name,
        "model": provider.model_name,
        "metrics": run_record.metrics,
        "results": results,
    })
