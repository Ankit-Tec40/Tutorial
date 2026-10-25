from datetime import datetime
from app.extensions import db


class LearningModule(db.Model):
    """A module representing a high-level subject area in the curriculum."""
    __tablename__ = "learning_modules"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default="bi-journal-code")
    order = db.Column(db.Integer, default=1, nullable=False)
    estimated_hours = db.Column(db.Float, default=2.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    lessons = db.relationship(
        "Lesson", 
        backref="module", 
        lazy="joined", 
        order_by="Lesson.order", 
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "icon": self.icon,
            "order": self.order,
            "estimated_hours": self.estimated_hours,
            "lesson_count": len(self.lessons),
        }


class Lesson(db.Model):
    """An individual lesson containing structured educational material, code, and quiz."""
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("learning_modules.id", ondelete="CASCADE"), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=1, nullable=False)
    estimated_minutes = db.Column(db.Integer, default=30)
    
    # 19-section interactive lesson fields
    prerequisites = db.Column(db.JSON, default=list)  # list of strings
    objectives = db.Column(db.JSON, default=list)     # list of strings
    explanation_markdown = db.Column(db.Text, nullable=False)
    real_world_use_cases = db.Column(db.JSON, default=list)  # list of strings
    mermaid_diagram = db.Column(db.Text, default="")
    walkthrough_markdown = db.Column(db.Text, default="")
    
    # Runnable code & playground parameters
    code_example = db.Column(db.Text, nullable=False)
    code_language = db.Column(db.String(30), default="python")
    code_explanation_markdown = db.Column(db.Text, default="")
    default_parameters = db.Column(db.JSON, default=dict)
    expected_output = db.Column(db.Text, default="")
    common_errors_markdown = db.Column(db.Text, default="")
    
    # Hands-on exercise & challenge
    exercise_prompt = db.Column(db.Text, default="")
    exercise_starter_code = db.Column(db.Text, default="")
    exercise_hint = db.Column(db.Text, default="")
    exercise_solution = db.Column(db.Text, default="")
    challenge_task = db.Column(db.Text, default="")
    key_takeaways = db.Column(db.JSON, default=list)
    doc_links = db.Column(db.JSON, default=list)  # list of {"title": str, "url": str}

    # Associated lab identifier if this lesson is attached to a runnable lab service
    lab_id = db.Column(db.String(60), nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    quizzes = db.relationship("QuizQuestion", backref="lesson", lazy="dynamic", cascade="all, delete-orphan")
    progress_records = db.relationship("LessonProgress", backref="lesson", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "module_id": self.module_id,
            "module_slug": self.module.slug if self.module else None,
            "module_title": self.module.title if self.module else None,
            "slug": self.slug,
            "title": self.title,
            "summary": self.summary,
            "order": self.order,
            "estimated_minutes": self.estimated_minutes,
            "objectives": self.objectives or [],
            "prerequisites": self.prerequisites or [],
            "lab_id": self.lab_id,
        }
