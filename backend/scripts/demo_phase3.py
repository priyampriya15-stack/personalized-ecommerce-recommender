"""
demo_phase3.py
--------------
Demonstration script for Phase 3 Hybrid Recommendation Engine.
Tests all scenarios (warm users, cold users with category onboarding,
contextual viewed item blending, and guest fallback) on real Amazon data.
"""

import sys
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.services.recommendation_engine import PopularityRecommender
from backend.services.collaborative_filtering import CollaborativeFilteringRecommender
from backend.services.content_based import ContentBasedRecommender
from backend.services.hybrid_recommender import HybridRecommender

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
        print(f"      Explanation: {d['explanation']}")


def run_demo():
    print("Loading hybrid recommendation engine from disk...")
    df_products = pd.read_parquet(DATA_DIR / "products.parquet")
    df_train = pd.read_parquet(DATA_DIR / "train_interactions.parquet")

    pop_model = PopularityRecommender.load(MODELS_DIR / "popularity_baseline.joblib")
    cf_model = CollaborativeFilteringRecommender.load(MODELS_DIR / "collaborative_svd.joblib")
    cb_model = ContentBasedRecommender.load(MODELS_DIR / "content_tfidf.joblib")

    hybrid_engine = HybridRecommender(
        popularity_model=pop_model,
        collaborative_model=cf_model,
        content_model=cb_model,
        default_alpha=0.5
    )

    # Pick real active user
    active_user = df_train["user_id"].value_counts().index[0]
    user_n_train = df_train[df_train["user_id"] == active_user].shape[0]

    # Scenario 1: Warm Active User (Hybrid alpha=0.5)
    print_section(f"SCENARIO 1: Warm User {active_user} (Hybrid alpha=0.5, {user_n_train} interactions)")
    recs_warm_05 = hybrid_engine.recommend(user_id=active_user, top_n=3, alpha=0.5)
    print_recs(recs_warm_05)

    # Scenario 2: Warm Active User (Optimal alpha=0.25 from empirical evaluation)
    print_section(f"SCENARIO 2: Warm User {active_user} (Empirical Optimal alpha=0.25)")
    recs_warm_025 = hybrid_engine.recommend(user_id=active_user, top_n=3, alpha=0.25)
    print_recs(recs_warm_025)

    # Scenario 3: Contextual Browsing (User viewing an Appliance while having Music history)
    viewed_appliance = df_products[df_products["category"] == "Appliances"]["product_id"].iloc[0]
    appliance_title = df_products[df_products["product_id"] == viewed_appliance]["title"].iloc[0]
    print_section(f"SCENARIO 3: Contextual Blending (User viewing '{appliance_title[:40]}...')")
    recs_contextual = hybrid_engine.recommend(
        user_id=active_user,
        viewed_product_id=viewed_appliance,
        top_n=3,
        alpha=0.5
    )
    print_recs(recs_contextual)

    # Scenario 4: Cold Start New User with Onboarding Category Preferences
    print_section("SCENARIO 4: Cold User with Onboarding Preferences (['All Beauty', 'Appliances'])")
    recs_cold_pref = hybrid_engine.recommend(
        user_id="NEW_USER_SESSION_999",
        preferred_categories=["All Beauty", "Appliances"],
        top_n=3
    )
    print_recs(recs_cold_pref)

    # Scenario 5: Completely Cold Guest User (No interactions, no preferences)
    print_section("SCENARIO 5: Completely Cold Guest User (Pure Popularity Fallback)")
    recs_guest = hybrid_engine.recommend(
        user_id=None,
        top_n=3
    )
    print_recs(recs_guest)


if __name__ == "__main__":
    run_demo()
