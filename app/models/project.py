from datetime import datetime
from app.extensions import db


class Project(db.Model):
    """Capstone portfolio project specifications and source files."""
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    badge = db.Column(db.String(40), default="Capstone")
    difficulty = db.Column(db.String(30), default="Intermediate")  # Beginner, Intermediate, Advanced
    objectives = db.Column(db.JSON, default=list)
    requirements = db.Column(db.JSON, default=list)
    architecture_mermaid = db.Column(db.Text, default="")
    dependencies = db.Column(db.JSON, default=list)
    run_instructions_markdown = db.Column(db.Text, default="")
    troubleshooting_markdown = db.Column(db.Text, default="")
    extension_challenges = db.Column(db.JSON, default=list)
    status = db.Column(db.String(30), default="not_started")  # not_started, in_progress, completed
    order = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Project files
    files = db.relationship(
        "ProjectFile", 
        backref="project", 
        lazy="joined", 
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "badge": self.badge,
            "difficulty": self.difficulty,
            "status": self.status,
            "order": self.order,
            "file_count": len(self.files),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ProjectFile(db.Model):
    """Source code file associated with a project workspace."""
    __tablename__ = "project_files"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = db.Column(db.String(120), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False, default="")
    language = db.Column(db.String(40), default="python")
    is_entry_point = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "language": self.language,
            "is_entry_point": self.is_entry_point,
            "size_bytes": len(self.content.encode("utf-8")),
        }
