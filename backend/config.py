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


class Config:
    """Base configuration with sensible defaults."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "super_secure_secret_key_change_in_production_personalized_ecommerce_system_2026")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super_secure_jwt_secret_key_personalized_rec_hybrid_system_2026_token_auth")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = 24
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DATA_DIR / 'ecommerce.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Recommendation System Defaults
    DEFAULT_HYBRID_ALPHA = float(os.environ.get("DEFAULT_HYBRID_ALPHA", 0.5))
    DEFAULT_RECOMMENDATION_K = int(os.environ.get("DEFAULT_RECOMMENDATION_K", 10))
    
    # CORS
    CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*")
    
    # Paths
    DATA_DIR = DATA_DIR
    MODELS_DIR = MODELS_DIR
    REPORTS_DIR = REPORTS_DIR


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
