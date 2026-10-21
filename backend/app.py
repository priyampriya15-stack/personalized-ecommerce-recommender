"""
app.py
------
Flask application factory and main server entry point.
Configures extensions, recommendation services, error handlers, and route blueprints.
"""

import os
import sys
import re
import logging
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import config_by_name, Config
from backend.models.database_models import db
from backend.models.schemas import error_response, success_response
from backend.routes import (
    auth_bp,
    products_bp,
    recommendations_bp,
    interactions_bp,
    cart_bp,
    orders_bp,
    admin_bp
)
from backend.services.recommendation_engine import PopularityRecommender
from backend.services.collaborative_filtering import CollaborativeFilteringRecommender
from backend.services.content_based import ContentBasedRecommender
from backend.services.hybrid_recommender import HybridRecommender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("flask_app")


def load_recommendation_models(app: Flask):
    """Load serialized ML models from models/ directory into application context."""
    models_dir = app.config.get("MODELS_DIR") or Config.MODELS_DIR
    app.recommendation_services = {}

    pop_path = models_dir / "popularity_baseline.joblib"
    cf_path = models_dir / "collaborative_svd.joblib"
    cb_path = models_dir / "content_tfidf.joblib"

    try:
        if pop_path.exists():
            pop_model = PopularityRecommender.load(pop_path)
            app.recommendation_services["popularity"] = pop_model
            logger.info("Loaded Popularity model.")
        else:
            logger.warning(f"Popularity model not found at {pop_path}")

        if cf_path.exists():
            cf_model = CollaborativeFilteringRecommender.load(cf_path)
            app.recommendation_services["collaborative"] = cf_model
            logger.info("Loaded Collaborative Filtering model.")
        else:
            logger.warning(f"Collaborative model not found at {cf_path}")

        if cb_path.exists():
            cb_model = ContentBasedRecommender.load(cb_path)
            app.recommendation_services["content_based"] = cb_model
            logger.info("Loaded Content-Based model.")
        else:
            logger.warning(f"Content-Based model not found at {cb_path}")

        if "popularity" in app.recommendation_services and \
           "collaborative" in app.recommendation_services and \
           "content_based" in app.recommendation_services:
            hybrid_engine = HybridRecommender(
                popularity_model=app.recommendation_services["popularity"],
                collaborative_model=app.recommendation_services["collaborative"],
                content_model=app.recommendation_services["content_based"],
                default_alpha=app.config.get("DEFAULT_HYBRID_ALPHA", 0.5)
            )
            app.recommendation_services["hybrid"] = hybrid_engine
            logger.info("Initialized Hybrid Recommendation Engine.")

    except Exception as e:
        logger.error(f"Error loading recommendation models: {e}")


def create_app(config_name: str = "development") -> Flask:
    """Create and configure Flask application instance."""
    app = Flask(__name__)
    config_class = config_by_name.get(config_name, config_by_name["development"])
    app.config.from_object(config_class)

    # Initialize extensions with production CORS configuration
    frontend_url = os.environ.get("FRONTEND_URL")
    cors_origin = os.environ.get("CORS_ORIGIN")
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://personalized-ecommerce-recommender-lrhaki.vercel.app",
        "https://personalized-ecommerce-recommender.vercel.app",
        re.compile(r"^https:\/\/.*\.vercel\.app$"),
        "https://personalized-ecommerce-frontend.onrender.com",
    ]
    if frontend_url:
        for f_url in frontend_url.split(","):
            clean_url = f_url.strip().rstrip("/")
            if clean_url.endswith("/api"):
                clean_url = clean_url[:-4].rstrip("/")
            if clean_url and clean_url not in allowed_origins:
                allowed_origins.append(clean_url)
    if cors_origin and cors_origin != "*":
        for c_url in cors_origin.split(","):
            clean_url = c_url.strip().rstrip("/")
            if clean_url.endswith("/api"):
                clean_url = clean_url[:-4].rstrip("/")
            if clean_url and clean_url not in allowed_origins:
                allowed_origins.append(clean_url)

    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        max_age=86400
    )

    # Ensure SQLite directory exists and path is normalized before SQLAlchemy connects
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        path_part = db_uri.replace("sqlite:///", "", 1)
        if path_part != ":memory:":
            sqlite_path = Path(path_part)
            posix_str = sqlite_path.as_posix()
            if not sqlite_path.is_absolute() or posix_str.startswith("/data/"):
                if posix_str.startswith("/data/"):
                    rel_path = posix_str.lstrip("/")
                    sqlite_path = (BASE_DIR / rel_path).resolve()
                else:
                    sqlite_path = (BASE_DIR / sqlite_path).resolve()
            else:
                sqlite_path = sqlite_path.resolve()
            try:
                sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError):
                sqlite_path = (BASE_DIR / "data" / sqlite_path.name).resolve()
                sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path.as_posix()}"

    db.init_app(app)

    # Load recommendation services
    load_recommendation_models(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(interactions_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)

    # Health Check Endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return success_response({
            "status": "healthy",
            "environment": config_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": list(app.recommendation_services.keys())
        }, "E-Commerce Recommendation System API operational.", 200)

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return error_response(getattr(error, "description", "Bad Request"), "BAD_REQUEST", 400)

    @app.errorhandler(401)
    def unauthorized(error):
        return error_response(getattr(error, "description", "Unauthorized access"), "UNAUTHORIZED", 401)

    @app.errorhandler(403)
    def forbidden(error):
        return error_response(getattr(error, "description", "Forbidden"), "FORBIDDEN", 403)

    @app.errorhandler(404)
    def not_found(error):
        return error_response("Endpoint or resource not found.", "NOT_FOUND", 404)

    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response("Method not allowed on this endpoint.", "METHOD_NOT_ALLOWED", 405)

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return error_response("An unexpected internal server error occurred.", "INTERNAL_SERVER_ERROR", 500)

    return app


if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development")
    app = create_app(env)
    # Ensure tables exist
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=(env == "development"))
