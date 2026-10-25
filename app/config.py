import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-fallback-secret-key-change-me")
    
    # Instance folder & database
    INSTANCE_DIR = BASE_DIR / "instance"
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Ensure absolute path with forward slashes for SQLite on Windows
    raw_db_url = os.getenv("DATABASE_URL", "")
    if not raw_db_url or "instance/ai_engineering_lab.db" in raw_db_url or raw_db_url == "sqlite:///ai_engineering_lab.db":
        db_path = (INSTANCE_DIR / "ai_engineering_lab.db").resolve().as_posix()
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    else:
        SQLALCHEMY_DATABASE_URI = raw_db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Provider Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    
    # Lab & Sandbox paths
    SANDBOX_DIR = BASE_DIR / "sandbox_fs"
    UPLOADS_DIR = BASE_DIR / "uploads"
    VECTOR_STORE_DIR = BASE_DIR / "vector_store"
    
    # Request limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    
    # Execution timeouts (seconds)
    PROVIDER_TIMEOUT = 45
    LAB_TIMEOUT = 30
    
    @classmethod
    def init_app(cls, app):
        """Ensure necessary directories exist."""
        cls.INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        cls.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        cls.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        cls.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
