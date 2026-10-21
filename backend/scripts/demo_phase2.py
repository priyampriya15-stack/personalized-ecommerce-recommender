"""
demo_phase2.py
--------------
Generates representative recommendation outputs from the real processed
Amazon Reviews 2023 dataset using the persisted models.
"""

import sys
import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.services.recommendation_engine import PopularityRecommender
from backend.services.collaborative_filtering import CollaborativeFilteringRecommender
from backend.services.content_based import ContentBasedRecommender

MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data" / "processed"


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f" {title} ")
    print("=" * 80)


def print_recs(recs):
    if not recs:
        print("  (No recommendations returned)")
        return
    for r in recs:
        d = r.to_dict()
        print(f"  #{d['rank']} [{d['algorithm']}] Score: {d['score']:.4f} | {d['product_id']} | {d['category']} | ${d['price']:.2f} | {d['rating']} stars")
        print(f"      Title: {d['title'][:65]}")
        print(f"      Reason: {d['explanation']}")


def run_demo():
    print("Loading datasets and trained models from disk...")
    df_products = pd.read_parquet(DATA_DIR / "products.parquet")
    df_train = pd.read_parquet(DATA_DIR / "train_interactions.parquet")

    pop_model = PopularityRecommender.load(MODELS_DIR / "popularity_baseline.joblib")
    cf_model = CollaborativeFilteringRecommender.load(MODELS_DIR / "collaborative_svd.joblib")
    cb_model = ContentBasedRecommender.load(MODELS_DIR / "content_tfidf.joblib")

    # 1. Popularity Baseline Recommendations (Catalog-wide)
    print_section("1. POPULARITY RECOMMENDER: Top 3 Across Catalog")
    pop_top3 = pop_model.recommend(top_n=3)
    print_recs(pop_top3)

    # 2. Popularity Category Filtered (e.g. "All Beauty")
    print_section("2. POPULARITY RECOMMENDER: Top 3 in 'All Beauty'")
    pop_beauty = pop_model.recommend(top_n=3, category="All Beauty")
    print_recs(pop_beauty)

    # 3. Collaborative Filtering for a Real Active User
    # Pick user with highest training interactions
    user_counts = df_train["user_id"].value_counts()
    sample_user_id = user_counts.index[0]
    user_interaction_count = user_counts.iloc[0]

    print_section(f"3. COLLABORATIVE FILTERING: Real User {sample_user_id} ({user_interaction_count} past interactions)")
    cf_recs = cf_model.recommend(sample_user_id, top_n=3, exclude_interacted=True)
    print_recs(cf_recs)

    # 4. Content-Based: Similar Products to a Real Item
    sample_product_id = df_products[df_products["category"] == "Appliances"]["product_id"].iloc[0]
    sample_product_title = df_products[df_products["product_id"] == sample_product_id]["title"].iloc[0]
    print_section(f"4. CONTENT-BASED: Products Similar to '{sample_product_title[:45]}...' ({sample_product_id})")
    cb_similar = cb_model.recommend_similar_to_product(sample_product_id, top_n=3)
    print_recs(cb_similar)

    # 5. Content-Based: User Profile (Onboarding categories: ["All Beauty", "Appliances"])
    print_section("5. CONTENT-BASED: User Profile (Preferences: 'All Beauty', 'Appliances')")
    cb_profile = cb_model.recommend_for_user_profile(
        interacted_items=[],
        preferred_categories=["All Beauty", "Appliances"],
        top_n=3
    )
    print_recs(cb_profile)


if __name__ == "__main__":
    run_demo()
