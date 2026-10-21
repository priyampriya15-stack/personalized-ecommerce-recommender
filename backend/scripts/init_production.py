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
    
    env = os.environ.get("FLASK_ENV", "production")
    app = create_app(env)
    
    with app.app_context():
        # 1. Create all database tables
        logger.info("Verifying database schema...")
        db.create_all()
        
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
                seed_users()
                
                # Check train interactions for active user seeding
                if train_parquet.exists() or train_csv.exists():
                    import pandas as pd
                    df_train = pd.read_parquet(train_parquet) if train_parquet.exists() else pd.read_csv(train_csv)
                    df_products = pd.read_parquet(products_parquet) if products_parquet.exists() else pd.read_csv(products_csv)
                    seed_active_user_with_interactions(df_train, df_products)
                logger.info("Product catalog and seed accounts imported successfully.")
            else:
                logger.warning(
                    f"Processed catalog files not found at {data_processed_dir}. "
                    "Database schema created; catalog will be populated once dataset is available."
                )
                seed_users()
        else:
            logger.info(f"Database catalog already contains {product_count} products. Skipping import.")
            
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
