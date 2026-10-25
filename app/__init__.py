import os
import logging
from flask import Flask, render_template, request, g
from app.config import config_by_name, Config
from app.extensions import db, migrate
from app.models.setting import AppSetting
from app.models.module import LearningModule
from app.models.progress import LessonProgress
from app.services.providers.factory import get_providers_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger("ai_engineering_lab")


def create_app(config_name: str = None) -> Flask:
    """Application factory pattern for AI Engineering Lab."""
    if not config_name:
        config_name = os.getenv("FLASK_ENV", "development")

    config_class = config_by_name.get(config_name, Config)

    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.lessons import lessons_bp
    from app.routes.chat import chat_bp
    from app.routes.rag import rag_bp
    from app.routes.tools import tools_bp
    from app.routes.agents import agents_bp
    from app.routes.mcp import mcp_bp
    from app.routes.projects import projects_bp
    from app.routes.evaluations import eval_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(lessons_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(rag_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(mcp_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(eval_bp)
    app.register_blueprint(settings_bp)

    # Context processor for global navigation and status
    @app.context_processor
    def inject_global_state():
        try:
            modules = LearningModule.query.order_by(LearningModule.order).all()
            completed_records = LessonProgress.query.filter_by(is_completed=True).all()
            completed_lesson_ids = {r.lesson_id for r in completed_records}
            theme = AppSetting.get("theme", "dark")
            active_provider = AppSetting.get("active_provider", "gemini")
        except Exception:
            modules = []
            completed_lesson_ids = set()
            theme = "dark"
            active_provider = "gemini"

        return {
            "nav_modules": modules,
            "completed_lesson_ids": completed_lesson_ids,
            "current_theme": theme,
            "active_provider_name": active_provider,
        }

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error("Internal Server Error: %s", e)
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def file_too_large(e):
        return render_template("errors/413.html"), 413

    # CLI Commands
    @app.cli.command("seed-lessons")
    def seed_lessons_command():
        """Seeds curriculum, quizzes, and capstone projects."""
        with app.app_context():
            from app.lessons.seed_data import seed_database
            seed_database()
            print("Successfully seeded all 15 curriculum modules, quizzes, and projects!")

    @app.cli.command("init-db")
    def init_db_command():
        """Creates all database tables."""
        with app.app_context():
            db.create_all()
            print("Database tables initialized successfully!")

    return app
