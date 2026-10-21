"""
config.py
---------
Configuration management for the Flask application and recommendation backend.
Supports Development, Testing, and Production environments.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"


def resolve_database_uri() -> str:
    """
    Resolve and construct a Render-compatible, absolute SQLite or PostgreSQL URI.
    Guarantees that the parent directory exists on disk before SQLAlchemy connects.
    """
    raw_uri = os.environ.get("DATABASE_URL")
    
    if not raw_uri:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        db_file = DATA_DIR / "ecommerce.db"
        return f"sqlite:///{db_file.as_posix()}"
    
    # Handle SQLite URLs
    if raw_uri.startswith("sqlite:///"):
        path_part = raw_uri.replace("sqlite:///", "", 1)
        if path_part == ":memory:":
            return "sqlite:///:memory:"
        
        sqlite_path = Path(path_part)
        posix_str = sqlite_path.as_posix()
        # Handle relative paths or root /data (ephemeral/non-writable on Render)
        if not sqlite_path.is_absolute() or posix_str.startswith("/data/"):
            if posix_str.startswith("/data/"):
                rel_path = posix_str.lstrip("/")
                sqlite_path = (BASE_DIR / rel_path).resolve()
            else:
                sqlite_path = (BASE_DIR / sqlite_path).resolve()
        else:
            sqlite_path = sqlite_path.resolve()
        
        # Ensure parent directory exists before any connection attempt
        try:
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            sqlite_path = (BASE_DIR / "data" / sqlite_path.name).resolve()
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            
        return f"sqlite:///{sqlite_path.as_posix()}"
    
    # Render PostgreSQL compatibility (postgres:// -> postgresql://)
    if raw_uri.startswith("postgres://"):
        raw_uri = raw_uri.replace("postgres://", "postgresql://", 1)
        
    return raw_uri


class Config:
    """Base configuration with sensible defaults."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "super_secure_secret_key_change_in_production_personalized_ecommerce_system_2026")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super_secure_jwt_secret_key_personalized_rec_hybrid_system_2026_token_auth")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = 24
    
    # Database (Render-compatible absolute path with directory auto-creation)
    SQLALCHEMY_DATABASE_URI = resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Recommendation System Defaults
    DEFAULT_HYBRID_ALPHA = float(os.environ.get("DEFAULT_HYBRID_ALPHA", 0.25))
    DEFAULT_RECOMMENDATION_K = int(os.environ.get("DEFAULT_RECOMMENDATION_K", 10))
    
    # CORS & Frontend URLs
    CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    
    # Paths (configurable via environment for persistent disk mounts)
    DATA_DIR = Path(os.environ.get("DATA_DIR", str(DATA_DIR)))
    MODELS_DIR = Path(os.environ.get("MODELS_DIR", str(MODELS_DIR)))
    REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", str(REPORTS_DIR)))


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "super_secure_test_jwt_secret_key_for_testing_purposes_only_32_chars"


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}
