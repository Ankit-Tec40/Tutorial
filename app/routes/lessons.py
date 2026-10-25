from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, abort
from app.extensions import db
from app.models.module import LearningModule, Lesson
from app.models.progress import LessonProgress, QuizQuestion, QuizAttempt, LabRun
from app.services.execution.runner import execute_lab_example
from app.services.providers.factory import get_providers_status

lessons_bp = Blueprint("lessons", __name__)


@lessons_bp.route("/lessons")
def catalog():
    """Renders the comprehensive curriculum course catalog."""
    modules = LearningModule.query.order_by(LearningModule.order).all()
    completed_records = LessonProgress.query.filter_by(is_completed=True).all()
    completed_ids = {r.lesson_id for r in completed_records}

    return render_template(
        "lessons_catalog.html",
        modules=modules,
        completed_ids=completed_ids,
    )


@lessons_bp.route("/lessons/<slug>")
def lesson_detail(slug: str):
    """Renders the 19-section interactive lesson page."""
    lesson = Lesson.query.filter_by(slug=slug).first_or_404()
    module = lesson.module

    # Get user progress record
    progress = LessonProgress.query.filter_by(lesson_id=lesson.id).first()
    is_completed = progress.is_completed if progress else False

    # Record visit
    if not progress:
        progress = LessonProgress(lesson_id=lesson.id, is_completed=False)
        db.session.add(progress)
    progress.last_visited_at = datetime.utcnow()
    db.session.commit()

    # Quizzes
    quizzes = lesson.quizzes.all()

    # Find Previous and Next lessons
    all_lessons = Lesson.query.join(LearningModule).order_by(LearningModule.order, Lesson.order).all()
    curr_idx = next((i for i, l in enumerate(all_lessons) if l.id == lesson.id), -1)
    prev_lesson = all_lessons[curr_idx - 1] if curr_idx > 0 else None
    next_lesson = all_lessons[curr_idx + 1] if curr_idx != -1 and curr_idx < len(all_lessons) - 1 else None

    provider_status = get_providers_status()

    return render_template(
        "lesson.html",
        lesson=lesson,
        module=module,
        is_completed=is_completed,
        quizzes=quizzes,
        prev_lesson=prev_lesson,
        next_lesson=next_lesson,
        provider_status=provider_status,
    )


@lessons_bp.route("/api/lessons/<int:lesson_id>/complete", methods=["POST"])
def toggle_complete(lesson_id: int):
    """Toggles lesson completion status."""
    lesson = Lesson.query.get_or_404(lesson_id)
    progress = LessonProgress.query.filter_by(lesson_id=lesson.id).first()

    data = request.get_json() or {}
    forced_state = data.get("completed")

    if not progress:
        progress = LessonProgress(lesson_id=lesson.id)
        db.session.add(progress)

    if forced_state is not None:
        progress.is_completed = bool(forced_state)
    else:
        progress.is_completed = not progress.is_completed

    if progress.is_completed:
        progress.completed_at = datetime.utcnow()
    else:
        progress.completed_at = None

    db.session.commit()
    return jsonify({
        "success": True,
        "lesson_id": lesson.id,
        "is_completed": progress.is_completed,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
    })


@lessons_bp.route("/api/lessons/<int:lesson_id>/quiz", methods=["POST"])
def submit_quiz(lesson_id: int):
    """Evaluates multiple-choice quiz submission and saves attempt history."""
    lesson = Lesson.query.get_or_404(lesson_id)
    questions = lesson.quizzes.all()

    if not questions:
        return jsonify({"success": False, "error": "No quiz questions found for this lesson."}), 400

    data = request.get_json() or {}
    submitted_answers = data.get("answers", {})  # {str(question_id): int(selected_index)}

    score = 0
    feedback = []

    for q in questions:
        q_id_str = str(q.id)
        user_choice = submitted_answers.get(q_id_str)
        is_correct = (user_choice == q.correct_index)
        if is_correct:
            score += 1

        feedback.append({
            "question_id": q.id,
            "user_choice": user_choice,
            "correct_index": q.correct_index,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })

    total = len(questions)
    percentage = round((score / total) * 100, 1)
    passed = percentage >= 70.0

    attempt = QuizAttempt(
        user_id="default_user",
        lesson_id=lesson.id,
        score=score,
        total_questions=total,
        percentage=percentage,
        passed=passed,
        answers=submitted_answers,
    )
    db.session.add(attempt)

    # If passed quiz, automatically mark lesson complete!
    if passed:
        prog = LessonProgress.query.filter_by(lesson_id=lesson.id).first()
        if not prog:
            prog = LessonProgress(lesson_id=lesson.id)
            db.session.add(prog)
        prog.is_completed = True
        prog.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "score": score,
        "total": total,
        "percentage": percentage,
        "passed": passed,
        "feedback": feedback,
    })


@lessons_bp.route("/api/labs/<lab_id>/run", methods=["POST"])
def run_lab(lab_id: str):
    """Executes a pre-defined safe lab routine with user-supplied parameters."""
    params = request.get_json() or {}
    try:
        result = execute_lab_example(lab_id=lab_id, parameters=params)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "lab_id": lab_id}), 400
