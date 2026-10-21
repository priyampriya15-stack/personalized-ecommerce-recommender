"""
init_production.py
------------------
Idempotent production initialization script for Render deployment.
1. Ensures database tables exist via SQLAlchemy db.create_all().
2. Populates SQLite catalog with 8,337 real Amazon products from processed dataset if not yet imported.
3. Seeds default production accounts (Admin, Demo User, Active User).
4. Verifies or trains machine learning recommendation models (Popularity, SVD, TF-IDF).
"""

import sys
import os
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.models.database_models import db, Product, User
from backend.scripts.import_products import import_products_catalog, seed_users, seed_active_user_with_interactions
from backend.scripts.train_models import train_and_persist_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("init_production")


def initialize_production():
    logger.info("=== Running Production Deployment Initialization ===")
    
    # 0. Ensure application data, processed, and models directories exist
    data_dir = (BASE_DIR / "data").resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)
    
    models_dir = (BASE_DIR / "models").resolve()
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Resolve and ensure database parent directory exists BEFORE app creation or connection
    raw_db_url = os.environ.get("DATABASE_URL")
    if raw_db_url and raw_db_url.startswith("sqlite:///"):
        path_part = raw_db_url.replace("sqlite:///", "", 1)
        if path_part != ":memory:":
            db_path = Path(path_part)
            posix_str = db_path.as_posix()
            if not db_path.is_absolute() or posix_str.startswith("/data/"):
                if posix_str.startswith("/data/"):
                    rel_path = posix_str.lstrip("/")
                    db_path = (BASE_DIR / rel_path).resolve()
                else:
                    db_path = (BASE_DIR / db_path).resolve()
            else:
                db_path = db_path.resolve()
            try:
                db_path.parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError):
                db_path = (BASE_DIR / "data" / db_path.name).resolve()
                db_path.parent.mkdir(parents=True, exist_ok=True)
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
            logger.info(f"Verified SQLite database directory: {db_path.parent} -> {db_path}")
    elif not raw_db_url:
        default_db = (data_dir / "ecommerce.db").resolve()
        default_db.parent.mkdir(parents=True, exist_ok=True)
        os.environ["DATABASE_URL"] = f"sqlite:///{default_db.as_posix()}"
        logger.info(f"Verified default SQLite database directory: {default_db.parent} -> {default_db}")

    env = os.environ.get("FLASK_ENV", "production")
    app = create_app(env)
    
    with app.app_context():
        # 1. Create all database tables
        logger.info(f"Initializing database schema at: {app.config['SQLALCHEMY_DATABASE_URI']}")
        db.create_all()
        logger.info("Database schema initialized successfully.")
        
        # 2. Check if product catalog is populated
        product_count = Product.query.count()
        logger.info(f"Current catalog product count: {product_count}")
        
        data_processed_dir = Path(app.config.get("DATA_DIR", BASE_DIR / "data")) / "processed"
        products_parquet = data_processed_dir / "products.parquet"
        products_csv = data_processed_dir / "products.csv"
        train_parquet = data_processed_dir / "train_interactions.parquet"
        train_csv = data_processed_dir / "train_interactions.csv"
        
        if product_count == 0:
            if products_parquet.exists() or products_csv.exists():
                logger.info("Importing real Amazon Reviews 2023 product catalog...")
                import_products_catalog()
                logger.info("Product catalog imported successfully.")
            else:
                logger.warning(
                    f"Processed catalog files not found at {data_processed_dir}. "
                    "Database schema created; catalog will be populated once dataset is available."
                )
        else:
            logger.info(f"Database catalog already contains {product_count} products. Skipping import.")

        # Always ensure seed accounts and active user interactions exist (idempotent)
        seed_users()
        if (train_parquet.exists() or train_csv.exists()) and (products_parquet.exists() or products_csv.exists()):
            import pandas as pd
            df_train = pd.read_parquet(train_parquet) if train_parquet.exists() else pd.read_csv(train_csv)
            df_products = pd.read_parquet(products_parquet) if products_parquet.exists() else pd.read_csv(products_csv)
            seed_active_user_with_interactions(df_train, df_products)
            
        # 3. Check ML model artifacts
        models_dir = Path(app.config.get("MODELS_DIR", BASE_DIR / "models"))
        models_dir.mkdir(parents=True, exist_ok=True)
        
        pop_file = models_dir / "popularity_baseline.joblib"
        cf_file = models_dir / "collaborative_svd.joblib"
        cb_file = models_dir / "content_tfidf.joblib"
        
        models_exist = pop_file.exists() and cf_file.exists() and cb_file.exists()
        if not models_exist:
            if products_parquet.exists() and (data_processed_dir / "interactions.parquet").exists():
                logger.info("Training missing ML recommendation models from processed dataset...")
                train_and_persist_all()
                logger.info("ML recommendation models successfully trained and serialized.")
            else:
                logger.info("Model training skipped: Processed interactions dataset not present on local container.")
        else:
            logger.info("All recommendation model artifacts (.joblib) are present.")
            
    logger.info("=== Production Initialization Complete ===")


if __name__ == "__main__":
    initialize_production()
