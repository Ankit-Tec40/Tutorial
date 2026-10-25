from datetime import datetime
from app.extensions import db


class LessonProgress(db.Model):
    """Tracks user completion and study state for a lesson."""
    __tablename__ = "lesson_progress"
    __table_args__ = (
        db.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), default="default_user", nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_visited_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lesson_id": self.lesson_id,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_visited_at": self.last_visited_at.isoformat() if self.last_visited_at else None,
        }


class QuizQuestion(db.Model):
    """Multiple choice questions attached to a lesson for knowledge verification."""
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)  # list of 4 option strings
    correct_index = db.Column(db.Integer, nullable=False)  # 0-indexed
    explanation = db.Column(db.Text, nullable=False)

    def to_dict(self, include_correct=False):
        data = {
            "id": self.id,
            "lesson_id": self.lesson_id,
            "question_text": self.question_text,
            "options": self.options,
        }
        if include_correct:
            data["correct_index"] = self.correct_index
            data["explanation"] = self.explanation
        return data


class QuizAttempt(db.Model):
    """User record of a completed quiz submission."""
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), default="default_user", nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    passed = db.Column(db.Boolean, default=False, nullable=False)
    answers = db.Column(db.JSON, default=dict)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lesson_id": self.lesson_id,
            "score": self.score,
            "total_questions": self.total_questions,
            "percentage": self.percentage,
            "passed": self.passed,
            "attempted_at": self.attempted_at.isoformat(),
        }


class LabRun(db.Model):
    """Log of practical lab executions."""
    __tablename__ = "lab_runs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), default="default_user", nullable=False, index=True)
    lab_id = db.Column(db.String(60), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    provider = db.Column(db.String(40), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    parameters = db.Column(db.JSON, default=dict)
    input_payload = db.Column(db.JSON, default=dict)
    output_result = db.Column(db.JSON, default=dict)
    execution_time_ms = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default="success")  # 'success', 'error'
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lab_id": self.lab_id,
            "provider": self.provider,
            "model": self.model,
            "parameters": self.parameters,
            "execution_time_ms": self.execution_time_ms,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }
