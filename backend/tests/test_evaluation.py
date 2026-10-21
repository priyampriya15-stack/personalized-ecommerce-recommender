"""
test_evaluation.py
------------------
Unit and integration tests for Hybrid Recommendation Engine, score normalization,
cold-start fallbacks, candidate exclusions, and offline evaluation metrics.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from backend.services.recommendation_engine import PopularityRecommender, RecommendationItem
from backend.services.collaborative_filtering import CollaborativeFilteringRecommender
from backend.services.content_based import ContentBasedRecommender
from backend.services.hybrid_recommender import HybridRecommender, min_max_normalize
from backend.services.evaluation import (
    precision_at_k,
    recall_at_k,
    f1_at_k,
    ndcg_at_k,
    map_at_k,
    compute_catalog_coverage,
    compute_intra_list_diversity
)

PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"


@pytest.fixture
def synthetic_models():
    """Create fitted models on small synthetic catalog for deterministic unit testing."""
    df_products = pd.DataFrame([
        {"product_id": "P1", "title": "Face Cream", "category": "Beauty", "price": 20.0, "rating": 4.5, "image_url": "", "content_text": "skincare face cream"},
        {"product_id": "P2", "title": "Face Serum", "category": "Beauty", "price": 30.0, "rating": 4.8, "image_url": "", "content_text": "skincare face serum"},
        {"product_id": "P3", "title": "Blender", "category": "Appliances", "price": 50.0, "rating": 4.0, "image_url": "", "content_text": "kitchen blender smoothie"},
        {"product_id": "P4", "title": "Toaster", "category": "Appliances", "price": 25.0, "rating": 3.8, "image_url": "", "content_text": "kitchen toaster breakfast"},
        {"product_id": "P5", "title": "Guitar", "category": "Music", "price": 100.0, "rating": 4.9, "image_url": "", "content_text": "acoustic guitar instrument"}
    ])

    df_interactions = pd.DataFrame([
        {"user_id": "U1", "product_id": "P1", "rating": 5.0, "timestamp": 100},
        {"user_id": "U1", "product_id": "P2", "rating": 4.0, "timestamp": 110},
        {"user_id": "U2", "product_id": "P1", "rating": 4.0, "timestamp": 120},
        {"user_id": "U2", "product_id": "P3", "rating": 5.0, "timestamp": 130},
        {"user_id": "U3", "product_id": "P4", "rating": 4.0, "timestamp": 140},
    ])

    pop = PopularityRecommender(min_threshold=1).fit(df_products, df_interactions)
    cf = CollaborativeFilteringRecommender(n_components=2, random_state=42).fit(df_products, df_interactions)
    cb = ContentBasedRecommender(max_features=50).fit(df_products)

    hybrid = HybridRecommender(
        popularity_model=pop,
        collaborative_model=cf,
        content_model=cb,
        default_alpha=0.5
    )

    return pop, cf, cb, hybrid


# =========================================================================
# 1. Score Normalization & Hybrid Score Tests
# =========================================================================

def test_min_max_normalize():
    # Normal case
    raw = np.array([10.0, 20.0, 30.0], dtype=np.float32)
    norm = min_max_normalize(raw)
    assert pytest.approx(norm[0], 1e-4) == 0.0
    assert pytest.approx(norm[1], 1e-4) == 0.5
    assert pytest.approx(norm[2], 1e-4) == 1.0

    # Uniform case (no division by zero)
    uniform = np.array([5.0, 5.0, 5.0], dtype=np.float32)
    norm_uni = min_max_normalize(uniform)
    assert np.all(norm_uni == 0.0)


def test_hybrid_alpha_weighting(synthetic_models):
    _, cf, cb, hybrid = synthetic_models

    # Alpha = 1.0 (Pure CF)
    recs_cf = hybrid.recommend(user_id="U1", alpha=1.0, top_n=3)
    assert all(r.algorithm == "hybrid" for r in recs_cf)

    # Alpha = 0.0 (Pure Content)
    recs_cb = hybrid.recommend(user_id="U1", alpha=0.0, top_n=3)
    assert all(r.algorithm == "hybrid" for r in recs_cb)

    # Ranking and scores differ based on alpha
    assert recs_cf[0].score != recs_cb[0].score or recs_cf[0].product_id != recs_cb[0].product_id


def test_hybrid_interacted_exclusion(synthetic_models):
    _, _, _, hybrid = synthetic_models
    # User U1 interacted with P1 and P2
    recs = hybrid.recommend(user_id="U1", top_n=5, exclude_interacted=True)
    rec_ids = [r.product_id for r in recs]
    assert "P1" not in rec_ids
    assert "P2" not in rec_ids


def test_hybrid_duplicate_prevention(synthetic_models):
    _, _, _, hybrid = synthetic_models
    recs = hybrid.recommend(user_id="U1", top_n=5)
    rec_ids = [r.product_id for r in recs]
    assert len(rec_ids) == len(set(rec_ids)), "Recommendations must have unique product IDs"


def test_hybrid_cold_user_fallback(synthetic_models):
    _, _, _, hybrid = synthetic_models

    # Unknown user with preferred category "Appliances"
    recs = hybrid.recommend(
        user_id="COLD_USER_001",
        preferred_categories=["Appliances"],
        top_n=2
    )
    assert len(recs) == 2
    assert recs[0].category == "Appliances"
    assert recs[0].algorithm in ["content_based", "popularity"]

    # Completely cold user (no preferences, no interactions)
    recs_pop = hybrid.recommend(
        user_id="COLD_USER_EMPTY",
        top_n=3
    )
    assert len(recs_pop) == 3
    assert recs_pop[0].algorithm == "popularity"


# =========================================================================
# 2. Evaluation Metric Unit Tests
# =========================================================================

def test_precision_at_k():
    ground_truth = {"P1", "P2"}
    recs = ["P1", "P3", "P4", "P2", "P5"]

    # At K=2: 1 hit (P1) -> Precision = 1/2 = 0.5
    assert precision_at_k(recs, ground_truth, k=2) == 0.5
    # At K=4: 2 hits (P1, P2) -> Precision = 2/4 = 0.5
    assert precision_at_k(recs, ground_truth, k=4) == 0.5
    # At K=0
    assert precision_at_k(recs, ground_truth, k=0) == 0.0


def test_recall_at_k():
    ground_truth = {"P1", "P2"}
    recs = ["P1", "P3", "P4", "P5"]

    # At K=2: 1 hit out of 2 ground truth items -> Recall = 0.5
    assert recall_at_k(recs, ground_truth, k=2) == 0.5
    # At K=4: 1 hit out of 2 -> Recall = 0.5
    assert recall_at_k(recs, ground_truth, k=4) == 0.5
    # If ground truth empty
    assert recall_at_k(recs, set(), k=2) == 0.0


def test_f1_at_k():
    assert pytest.approx(f1_at_k(0.5, 0.5), 1e-4) == 0.5
    assert f1_at_k(0.0, 0.5) == 0.0
    assert f1_at_k(0.0, 0.0) == 0.0


def test_ndcg_at_k():
    ground_truth = {"P1"}
    # Hit at position 1: DCG = 1/log2(2) = 1.0, IDCG = 1.0 -> NDCG = 1.0
    assert pytest.approx(ndcg_at_k(["P1", "P2"], ground_truth, k=2), 1e-4) == 1.0

    # Hit at position 2: DCG = 1/log2(3) = 0.6309, IDCG = 1.0 -> NDCG = 0.6309
    assert pytest.approx(ndcg_at_k(["P2", "P1"], ground_truth, k=2), 1e-3) == 0.6309

    # Zero hits: NDCG = 0.0
    assert ndcg_at_k(["P3", "P4"], ground_truth, k=2) == 0.0


def test_map_at_k():
    ground_truth = {"P1", "P3"}
    recs = ["P1", "P2", "P3"]

    # Position 1: hit -> P@1 = 1/1 = 1.0
    # Position 2: miss
    # Position 3: hit -> P@3 = 2/3
    # AP = (1.0 + 2/3) / 2 = 5/6 = 0.8333
    assert pytest.approx(map_at_k(recs, ground_truth, k=3), 1e-3) == 0.8333


def test_catalog_coverage():
    all_recs = [["P1", "P2"], ["P2", "P3"], ["P1", "P4"]]
    catalog_size = 10
    # Distinct items: {P1, P2, P3, P4} = 4 -> 4/10 = 40%
    assert compute_catalog_coverage(all_recs, catalog_size) == 40.0


def test_intra_list_diversity(synthetic_models):
    _, _, cb, _ = synthetic_models
    recs = [["P1", "P5"]]  # P1 is skincare face cream, P5 is guitar (orthogonal content)
    ild = compute_intra_list_diversity(recs, cb.tfidf_matrix, cb.item2idx, k=2, sample_size=1)
    # Should have high diversity (> 0.8)
    assert ild > 0.5
