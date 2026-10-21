"""
train_models.py
---------------
Trains the Popularity baseline, Collaborative Filtering (Truncated SVD),
and Content-Based (TF-IDF) recommendation models on the processed dataset,
persisting the serialized artifacts under models/ for runtime API consumption.
"""

import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np

# Adjust path for running script directly
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.services.recommendation_engine import PopularityRecommender
from backend.services.collaborative_filtering import CollaborativeFilteringRecommender
from backend.services.content_based import ContentBasedRecommender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("train_models")

DATA_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_and_persist_all():
    logger.info("=== Starting Model Training Pipeline ===")

    # 1. Load Processed Data
    products_path = DATA_DIR / "products.parquet"
    train_path = DATA_DIR / "train_interactions.parquet"
    all_interactions_path = DATA_DIR / "interactions.parquet"

    logger.info(f"Loading data from {DATA_DIR}...")
    df_products = pd.read_parquet(products_path) if products_path.exists() else pd.read_csv(DATA_DIR / "products.csv")
    df_train = pd.read_parquet(train_path) if train_path.exists() else pd.read_csv(DATA_DIR / "train_interactions.csv")
    df_interactions_all = pd.read_parquet(all_interactions_path) if all_interactions_path.exists() else pd.read_csv(DATA_DIR / "interactions.csv")

    logger.info(f"Loaded {len(df_products)} products, {len(df_train)} train interactions, {len(df_interactions_all)} total interactions.")

    # 2. Train Popularity Recommender
    logger.info("Training Popularity Recommender (Bayesian Weighted Baseline)...")
    pop_recommender = PopularityRecommender(min_threshold=3)
    # Fit on all interactions for complete popularity baseline
    pop_recommender.fit(df_products, df_interactions_all)
    pop_path = MODELS_DIR / "popularity_baseline.joblib"
    pop_recommender.save(pop_path)
    logger.info(f"Saved Popularity model to {pop_path} ({pop_path.stat().st_size / 1024:.1f} KB)")

    # 3. Train Collaborative Filtering Recommender (Truncated SVD)
    logger.info("Training Collaborative Filtering Recommender (Truncated SVD)...")
    cf_recommender = CollaborativeFilteringRecommender(n_components=30, random_state=42)
    # Fit strictly on train_interactions to adhere to offline evaluation protocol
    cf_recommender.fit(df_products, df_train)
    cf_path = MODELS_DIR / "collaborative_svd.joblib"
    cf_recommender.save(cf_path)
    logger.info(f"Saved Collaborative Filtering model to {cf_path} ({cf_path.stat().st_size / 1024:.1f} KB)")

    # 4. Train Content-Based Recommender (TF-IDF)
    logger.info("Training Content-Based Recommender (TF-IDF Vectorizer)...")
    cb_recommender = ContentBasedRecommender(max_features=5000)
    cb_recommender.fit(df_products)
    cb_path = MODELS_DIR / "content_tfidf.joblib"
    cb_recommender.save(cb_path)
    logger.info(f"Saved Content-Based model to {cb_path} ({cb_path.stat().st_size / 1024:.1f} KB)")

    # 5. Model Validation & Smoke Test
    logger.info("Validating reloaded models...")
    pop_loaded = PopularityRecommender.load(pop_path)
    pop_recs = pop_loaded.recommend(top_n=3)
    logger.info(f"Sample Popularity Rec 1: {pop_recs[0].title} (Score: {pop_recs[0].score:.2f})")

    cf_loaded = CollaborativeFilteringRecommender.load(cf_path)
    # Sample active user
    sample_user = df_train["user_id"].iloc[0]
    cf_recs = cf_loaded.recommend(sample_user, top_n=3)
    if cf_recs:
        logger.info(f"Sample CF Rec for {sample_user}: {cf_recs[0].title} (Score: {cf_recs[0].score:.4f})")

    cb_loaded = ContentBasedRecommender.load(cb_path)
    sample_product = df_products["product_id"].iloc[0]
    cb_recs = cb_loaded.recommend_similar_to_product(sample_product, top_n=3)
    if cb_recs:
        logger.info(f"Sample Content Rec similar to {sample_product}: {cb_recs[0].title} (Score: {cb_recs[0].score:.4f})")

    # 6. Save Training Metadata
    metadata = {
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "popularity": {
                "artifact": "popularity_baseline.joblib",
                "min_threshold": pop_recommender.min_threshold,
                "global_mean_rating": round(pop_recommender.global_mean, 4),
                "ranked_catalog_count": len(pop_recommender.ranked_products)
            },
            "collaborative_filtering": {
                "artifact": "collaborative_svd.joblib",
                "algorithm": "TruncatedSVD",
                "n_components": cf_recommender.n_components,
                "users_in_matrix": len(cf_recommender.user2idx),
                "items_in_matrix": len(cf_recommender.item2idx)
            },
            "content_based": {
                "artifact": "content_tfidf.joblib",
                "algorithm": "TF-IDF + Cosine Similarity",
                "max_features": cb_recommender.max_features,
                "vocabulary_size": len(cb_recommender.vectorizer.vocabulary_),
                "catalog_items": cb_recommender.tfidf_matrix.shape[0]
            }
        }
    }

    meta_path = MODELS_DIR / "training_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Training metadata recorded in {meta_path}")
    logger.info("=== Model Training Completed Successfully ===")
    return metadata


if __name__ == "__main__":
    train_and_persist_all()
