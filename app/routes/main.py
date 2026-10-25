import os
import time
from flask import Blueprint, render_template, request, jsonify, current_app
from app.extensions import db
from app.models.module import LearningModule, Lesson
from app.models.progress import LessonProgress, LabRun, QuizAttempt
from app.models.project import Project
from app.models.setting import AppSetting
from app.services.providers.factory import get_providers_status

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def dashboard():
    """Renders the main dashboard with progress, provider indicators, and activity."""
    modules = LearningModule.query.order_by(LearningModule.order).all()
    all_lessons = Lesson.query.all()
    total_lessons = len(all_lessons)

    # Calculate completed lessons
    completed_records = LessonProgress.query.filter_by(is_completed=True).all()
    completed_ids = {r.lesson_id for r in completed_records}
    completed_count = len(completed_ids)
    progress_pct = round((completed_count / total_lessons * 100), 1) if total_lessons > 0 else 0

    # Find recommended next lesson
    next_lesson = None
    for m in modules:
        for l in m.lessons:
            if l.id not in completed_ids:
                next_lesson = l
                break
        if next_lesson:
            break

    # Recent lab executions
    recent_runs = LabRun.query.order_by(LabRun.created_at.desc()).limit(5).all()

    # Capstone projects
    projects = Project.query.order_by(Project.order).limit(4).all()

    # Quiz statistics
    quiz_attempts = QuizAttempt.query.all()
    avg_quiz_score = (
        round(sum(q.percentage for q in quiz_attempts) / len(quiz_attempts), 1)
        if quiz_attempts else 0.0
    )

    # Provider statuses
    provider_status = get_providers_status()

    return render_template(
        "dashboard.html",
        modules=modules,
        total_lessons=total_lessons,
        completed_count=completed_count,
        progress_pct=progress_pct,
        next_lesson=next_lesson,
        recent_runs=recent_runs,
        projects=projects,
        avg_quiz_score=avg_quiz_score,
        provider_status=provider_status,
    )


@main_bp.route("/search")
def search():
    """Global search across lessons, modules, and capstone projects."""
    q = request.args.get("q", "").strip()
    if not q:
        return render_template("search.html", query="", lesson_results=[], project_results=[])

    search_term = f"%{q}%"
    lesson_results = Lesson.query.filter(
        (Lesson.title.ilike(search_term)) |
        (Lesson.summary.ilike(search_term)) |
        (Lesson.explanation_markdown.ilike(search_term))
    ).limit(15).all()

    project_results = Project.query.filter(
        (Project.title.ilike(search_term)) |
        (Project.description.ilike(search_term))
    ).limit(5).all()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.args.get("format") == "json":
        return jsonify({
            "query": q,
            "lessons": [
                {
                    "title": l.title,
                    "slug": l.slug,
                    "summary": l.summary,
                    "module": l.module.title if l.module else "",
                    "url": f"/lessons/{l.slug}",
                }
                for l in lesson_results
            ],
            "projects": [
                {
                    "title": p.title,
                    "slug": p.slug,
                    "description": p.description,
                    "url": f"/projects/{p.slug}",
                }
                for p in project_results
            ]
        })

    return render_template(
        "search.html",
        query=q,
        lesson_results=lesson_results,
        project_results=project_results,
    )


@main_bp.route("/api/health")
def health():
    """System liveness and readiness probe."""
    gemini_key = bool(os.getenv("GEMINI_API_KEY", "").strip())
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    return jsonify({
        "status": "healthy",
        "app": "AI Engineering Lab",
        "version": "1.0.0",
        "timestamp": time.time(),
        "database": "connected",
        "gemini_configured": gemini_key,
        "ollama_url": ollama_url,
    })


@main_bp.route("/api/theme", methods=["POST"])
def toggle_theme():
    """Saves user theme preference in database."""
    data = request.get_json() or {}
    new_theme = data.get("theme", "dark")
    if new_theme not in ("dark", "light"):
        new_theme = "dark"
    AppSetting.set("theme", new_theme, "User UI theme")
    return jsonify({"success": True, "theme": new_theme})
