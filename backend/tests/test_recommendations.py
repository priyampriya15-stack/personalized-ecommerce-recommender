"""
test_recommendations.py
-----------------------
Unit and integration tests for Popularity, Collaborative Filtering (Truncated SVD),
and Content-Based (TF-IDF) recommendation models.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from backend.services.recommendation_engine import PopularityRecommender, RecommendationItem
from backend.services.collaborative_filtering import CollaborativeFilteringRecommender
from backend.services.content_based import ContentBasedRecommender

PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"


@pytest.fixture
def synthetic_data():
    """Create small controlled synthetic dataset for deterministic unit testing."""
    df_products = pd.DataFrame([
        {
            "product_id": "P1",
            "title": "Hydrating Face Cream Skincare",
            "category": "Beauty",
            "price": 20.0,
            "rating": 4.5,
            "image_url": "http://example.com/p1.jpg",
            "content_text": "Hydrating Face Cream Skincare daily moisturizing lotion"
        },
        {
            "product_id": "P2",
            "title": "Anti-Aging Face Serum Skincare",
            "category": "Beauty",
            "price": 35.0,
            "rating": 4.8,
            "image_url": "http://example.com/p2.jpg",
            "content_text": "Anti-Aging Face Serum Skincare retinol hyaluronic acid beauty treatment"
        },
        {
            "product_id": "P3",
            "title": "Compact Electric Blender Kitchen Appliance",
            "category": "Appliances",
            "price": 50.0,
            "rating": 4.2,
            "image_url": "http://example.com/p3.jpg",
            "content_text": "Compact Electric Blender Kitchen Appliance smoothie maker high speed"
        },
        {
            "product_id": "P4",
            "title": "Stainless Steel Toaster 2-Slice",
            "category": "Appliances",
            "price": 30.0,
            "rating": 3.9,
            "image_url": "http://example.com/p4.jpg",
            "content_text": "Stainless Steel Toaster 2-Slice kitchen bread breakfast appliance"
        },
        {
            "product_id": "P5",
            "title": "Acoustic Guitar Strings Set",
            "category": "Music",
            "price": 12.0,
            "rating": 4.7,
            "image_url": "http://example.com/p5.jpg",
            "content_text": "Acoustic Guitar Strings Set phosphor bronze light gauge music"
        }
    ])

    df_interactions = pd.DataFrame([
        {"user_id": "U1", "product_id": "P1", "rating": 5.0, "timestamp": 100},
        {"user_id": "U1", "product_id": "P2", "rating": 4.0, "timestamp": 110},
        {"user_id": "U2", "product_id": "P1", "rating": 4.0, "timestamp": 120},
        {"user_id": "U2", "product_id": "P3", "rating": 5.0, "timestamp": 130},
        {"user_id": "U3", "product_id": "P3", "rating": 4.0, "timestamp": 140},
        {"user_id": "U3", "product_id": "P4", "rating": 3.0, "timestamp": 150},
        {"user_id": "U4", "product_id": "P5", "rating": 5.0, "timestamp": 160},
        {"user_id": "U4", "product_id": "P1", "rating": 5.0, "timestamp": 170},
    ])

    return df_products, df_interactions


# =========================================================================
# 1. Popularity Recommender Tests
# =========================================================================

def test_popularity_bayesian_ranking(synthetic_data):
    df_products, df_interactions = synthetic_data
    model = PopularityRecommender(min_threshold=2)
    model.fit(df_products, df_interactions)

    recs = model.recommend(top_n=5)
    assert len(recs) == 5
    assert all(isinstance(r, RecommendationItem) for r in recs)
    # Ranks must be consecutive starting from 1
    assert [r.rank for r in recs] == [1, 2, 3, 4, 5]
    # Scores must be strictly non-increasing
    scores = [r.score for r in recs]
    assert scores == sorted(scores, reverse=True)
    # Algorithm name must match
    assert all(r.algorithm == "popularity" for r in recs)


def test_popularity_category_filter(synthetic_data):
    df_products, df_interactions = synthetic_data
    model = PopularityRecommender(min_threshold=1)
    model.fit(df_products, df_interactions)

    beauty_recs = model.recommend(top_n=10, category="Beauty")
    assert len(beauty_recs) == 2
    assert all(r.category == "Beauty" for r in beauty_recs)


def test_popularity_interacted_exclusion(synthetic_data):
    df_products, df_interactions = synthetic_data
    model = PopularityRecommender(min_threshold=1)
    model.fit(df_products, df_interactions)

    top_prod = model.recommend(top_n=1)[0].product_id
    recs_excluded = model.recommend(top_n=5, exclude_items={top_prod})
    assert top_prod not in [r.product_id for r in recs_excluded]


# =========================================================================
# 2. Collaborative Filtering Tests (Truncated SVD)
# =========================================================================

def test_collaborative_filtering_recommendation(synthetic_data):
    df_products, df_interactions = synthetic_data
    model = CollaborativeFilteringRecommender(n_components=2, random_state=42)
    model.fit(df_products, df_interactions)

    # User U1 interacted with P1 and P2
    recs = model.recommend(user_id="U1", top_n=3, exclude_interacted=True)
    assert recs is not None
    assert len(recs) > 0
    # Interacted items must be excluded
    rec_ids = {r.product_id for r in recs}
    assert "P1" not in rec_ids
    assert "P2" not in rec_ids
    assert all(r.algorithm == "collaborative_filtering" for r in recs)


def test_collaborative_filtering_cold_user(synthetic_data):
    df_products, df_interactions = synthetic_data
    model = CollaborativeFilteringRecommender(n_components=2, random_state=42)
    model.fit(df_products, df_interactions)

    # Unknown user should return None gracefully without throwing exception
    recs = model.recommend(user_id="UNKNOWN_USER_999", top_n=5)
    assert recs is None


def test_collaborative_filtering_latent_similarity(synthetic_data):
    df_products, df_interactions = synthetic_data
    model = CollaborativeFilteringRecommender(n_components=2, random_state=42)
    model.fit(df_products, df_interactions)

    similar = model.recommend_similar_items(product_id="P1", top_n=2)
    assert similar is not None
    assert len(similar) <= 2
    # Target item must not be recommended to itself
    assert "P1" not in [r.product_id for r in similar]


# =========================================================================
# 3. Content-Based Filtering Tests (TF-IDF & Cosine Similarity)
# =========================================================================

def test_content_based_similar_product(synthetic_data):
    df_products, _ = synthetic_data
    model = ContentBasedRecommender(max_features=100)
    model.fit(df_products)

    # Similar to P1 (Face cream) should be P2 (Anti-aging facial serum)
    recs = model.recommend_similar_to_product(product_id="P1", top_n=2)
    assert recs is not None
    assert len(recs) == 2
    assert "P1" not in [r.product_id for r in recs]
    # Most similar item should be P2 (both Beauty skincare items)
    assert recs[0].product_id == "P2"


def test_content_based_user_profile(synthetic_data):
    df_products, _ = synthetic_data
    model = ContentBasedRecommender(max_features=100)
    model.fit(df_products)

    # User who likes kitchen appliances
    user_history = [("P3", 5.0)]
    recs = model.recommend_for_user_profile(
        interacted_items=user_history,
        top_n=2,
        exclude_interacted=True
    )
    assert len(recs) > 0
    # P3 should be excluded
    assert "P3" not in [r.product_id for r in recs]
    # P4 (Toaster - kitchen appliance) should be top match
    assert recs[0].product_id == "P4"


def test_content_based_onboarding_categories(synthetic_data):
    df_products, _ = synthetic_data
    model = ContentBasedRecommender(max_features=100)
    model.fit(df_products)

    # New user with no interaction history but preferred category "Music"
    recs = model.recommend_for_user_profile(
        interacted_items=[],
        preferred_categories=["Music"],
        top_n=3
    )
    assert len(recs) > 0
    # Top match should be P5 (Guitar strings)
    assert recs[0].product_id == "P5"


# =========================================================================
# 4. Model Persistence & Reloading Tests
# =========================================================================

def test_model_persistence_roundtrip(tmp_path, synthetic_data):
    df_products, df_interactions = synthetic_data

    # 1. Popularity
    pop = PopularityRecommender().fit(df_products, df_interactions)
    pop_file = tmp_path / "pop.joblib"
    pop.save(pop_file)
    pop_loaded = PopularityRecommender.load(pop_file)
    assert [r.product_id for r in pop.recommend(top_n=3)] == [r.product_id for r in pop_loaded.recommend(top_n=3)]

    # 2. Collaborative Filtering
    cf = CollaborativeFilteringRecommender(n_components=2).fit(df_products, df_interactions)
    cf_file = tmp_path / "cf.joblib"
    cf.save(cf_file)
    cf_loaded = CollaborativeFilteringRecommender.load(cf_file)
    assert [r.product_id for r in cf.recommend("U1", top_n=2)] == [r.product_id for r in cf_loaded.recommend("U1", top_n=2)]

    # 3. Content-Based
    cb = ContentBasedRecommender(max_features=50).fit(df_products)
    cb_file = tmp_path / "cb.joblib"
    cb.save(cb_file)
    cb_loaded = ContentBasedRecommender.load(cb_file)
    assert [r.product_id for r in cb.recommend_similar_to_product("P1", top_n=2)] == [r.product_id for r in cb_loaded.recommend_similar_to_product("P1", top_n=2)]


# =========================================================================
# 5. Integration Tests with Actual Processed Dataset
# =========================================================================

@pytest.mark.skipif(not (PROCESSED_DIR / "products.parquet").exists(), reason="Processed data missing")
def test_real_dataset_models_integration():
    """Verify algorithms on real Amazon Reviews 2023 preprocessed data."""
    df_products = pd.read_parquet(PROCESSED_DIR / "products.parquet")
    df_train = pd.read_parquet(PROCESSED_DIR / "train_interactions.parquet")

    # Popularity Recommender
    pop = PopularityRecommender(min_threshold=3).fit(df_products, df_train)
    pop_recs = pop.recommend(top_n=5)
    assert len(pop_recs) == 5
    assert pop_recs[0].score >= pop_recs[1].score

    # Collaborative Filtering
    cf = CollaborativeFilteringRecommender(n_components=10).fit(df_products, df_train)
    active_user = df_train["user_id"].iloc[0]
    cf_recs = cf.recommend(active_user, top_n=5)
    assert cf_recs is not None
    assert len(cf_recs) == 5

    # Content-Based
    cb = ContentBasedRecommender(max_features=500).fit(df_products.head(500))
    sample_pid = df_products["product_id"].iloc[0]
    cb_recs = cb.recommend_similar_to_product(sample_pid, top_n=5)
    assert cb_recs is not None
    assert len(cb_recs) == 5
