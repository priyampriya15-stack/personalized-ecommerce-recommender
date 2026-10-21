"""
hybrid_recommender.py
---------------------
Hybrid Recommendation Engine combining Collaborative Filtering and Content-Based Filtering.

Mathematical Formula:
    Hybrid Score = alpha * CF_norm + (1 - alpha) * CB_norm
where:
    alpha in [0.0, 1.0] is a configurable weighting parameter (default 0.5).
    CF_norm is the min-max normalized collaborative filtering predicted score.
    CB_norm is the min-max normalized content-based cosine similarity score.

Cold-Start Resolution Strategy:
1. Warm User (Interactions present):
   Hybrid scoring blending collaborative latent vectors and content profiles.
2. Cold User with Onboarding Preferences:
   Content-Based profile matching preferred categories + Popularity blend.
3. Completely Cold User (No interactions, no preferences):
   Bayesian Popularity Recommender baseline.
4. Cold / Unreviewed Product:
   Evaluated via Content-Based metadata similarity.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from .recommendation_engine import RecommendationItem, PopularityRecommender
from .collaborative_filtering import CollaborativeFilteringRecommender
from .content_based import ContentBasedRecommender


def min_max_normalize(scores: np.ndarray) -> np.ndarray:
    """
    Min-Max scale a score vector into [0.0, 1.0].
    Handles zero-variance vectors safely without dividing by zero.
    """
    s = np.asarray(scores, dtype=np.float32)
    s_min = float(np.min(s))
    s_max = float(np.max(s))

    diff = s_max - s_min
    if diff <= 1e-9:
        # Uniform vector: return zeros
        return np.zeros_like(s)

    return (s - s_min) / (diff + 1e-9)


class HybridRecommender:
    """
    Production-ready Hybrid Recommendation Engine.
    Combines Collaborative Filtering, Content-Based, and Popularity Fallbacks.
    """

    def __init__(
        self,
        popularity_model: PopularityRecommender,
        collaborative_model: CollaborativeFilteringRecommender,
        content_model: ContentBasedRecommender,
        default_alpha: float = 0.5
    ):
        self.popularity_model = popularity_model
        self.collaborative_model = collaborative_model
        self.content_model = content_model
        self.default_alpha = float(min(max(default_alpha, 0.0), 1.0))

    def set_alpha(self, alpha: float) -> None:
        """Update the default hybrid weighting parameter."""
        self.default_alpha = float(min(max(alpha, 0.0), 1.0))

    def get_alpha(self) -> float:
        """Return the current default hybrid weighting parameter."""
        return self.default_alpha

    def recommend(
        self,
        user_id: Optional[str] = None,
        viewed_product_id: Optional[str] = None,
        preferred_categories: Optional[List[str]] = None,
        user_history: Optional[List[Tuple[str, float]]] = None,
        top_n: int = 10,
        alpha: Optional[float] = None,
        exclude_interacted: bool = True
    ) -> List[RecommendationItem]:
        """
        Generate ranked personalized recommendations using the hybrid fusion formula.

        Parameters:
        - user_id: ID of the user requesting recommendations
        - viewed_product_id: Optional product ID currently viewed in browsing session
        - preferred_categories: Optional list of categories selected during onboarding
        - user_history: Optional list of (product_id, rating/weight) pairs
        - top_n: Number of recommendations to return
        - alpha: Optional override for the hybrid weight [0.0, 1.0]
        - exclude_interacted: Whether to filter out previously interacted products
        """
        eff_alpha = self.default_alpha if alpha is None else float(min(max(alpha, 0.0), 1.0))
        n_items = len(self.content_model.item2idx)

        # 1. Gather Excluded Items
        excluded_items: Set[str] = set()
        user_id_str = str(user_id) if user_id is not None else None

        if exclude_interacted:
            if user_id_str and user_id_str in self.collaborative_model.user_interacted_items:
                excluded_items.update(self.collaborative_model.user_interacted_items[user_id_str])
            if user_history:
                for pid, _ in user_history:
                    excluded_items.add(str(pid))

        if viewed_product_id:
            excluded_items.add(str(viewed_product_id))

        # 2. Collaborative Filtering Component
        cf_raw = None
        has_cf = False
        if user_id_str:
            cf_raw = self.collaborative_model.predict_all_items(user_id_str)
            if cf_raw is not None and not np.all(cf_raw == 0):
                has_cf = True

        cf_norm = min_max_normalize(cf_raw) if has_cf else np.zeros(n_items, dtype=np.float32)

        # 3. Content-Based Filtering Component
        # Combine user interaction history
        active_history: List[Tuple[str, float]] = []
        if user_history:
            active_history.extend(user_history)
        elif user_id_str and user_id_str in self.collaborative_model.user_interacted_items:
            # Reconstruct history from known training interactions with unit weights
            active_history.extend([(pid, 1.0) for pid in self.collaborative_model.user_interacted_items[user_id_str]])

        cb_profile_scores = self.content_model.predict_all_items_for_profile(
            interacted_items=active_history,
            preferred_categories=preferred_categories
        )

        # If a product is currently viewed, blend item-level content similarity
        if viewed_product_id:
            viewed_sim = self.content_model.get_item_similarity_vector(viewed_product_id)
            if viewed_sim is not None:
                cb_profile_scores += 1.5 * viewed_sim

        has_cb = not np.all(cb_profile_scores == 0)
        cb_norm = min_max_normalize(cb_profile_scores) if has_cb else np.zeros(n_items, dtype=np.float32)

        # 4. Hybrid Combination & Cold-Start Strategy
        if has_cf and has_cb:
            hybrid_scores = eff_alpha * cf_norm + (1.0 - eff_alpha) * cb_norm
            algo_label = "hybrid"
        elif has_cf and not has_cb:
            hybrid_scores = cf_norm
            algo_label = "collaborative_filtering"
        elif not has_cf and has_cb:
            hybrid_scores = cb_norm
            algo_label = "content_based"
        else:
            # Completely Cold Start -> Popularity Recommender
            primary_cat = preferred_categories[0] if (preferred_categories and len(preferred_categories) > 0) else None
            return self.popularity_model.recommend(
                top_n=top_n,
                category=primary_cat,
                exclude_items=excluded_items
            )

        # 5. Mask Excluded Items
        for it in excluded_items:
            if it in self.content_model.item2idx:
                hybrid_scores[self.content_model.item2idx[it]] = -1e9

        # 6. Rank Candidates
        top_indices = np.argsort(hybrid_scores)[::-1][:top_n]

        results: List[RecommendationItem] = []
        for rank, idx in enumerate(top_indices, start=1):
            score_val = float(hybrid_scores[idx])
            if score_val <= -1e8:
                continue

            pid = self.content_model.idx2item[idx]
            meta = self.content_model.product_meta.get(pid, {})
            cat = meta.get("category", "General")

            # Explanation strictly derived from active signals
            if algo_label == "hybrid":
                explanation = f"Matches shoppers with similar taste (CF) & aligns with your {cat} interests (CB)"
            elif algo_label == "collaborative_filtering":
                explanation = "Recommended because shoppers with similar taste liked this"
            elif algo_label == "content_based":
                if viewed_product_id:
                    explanation = "Similar in features and category to the product you are viewing"
                elif preferred_categories:
                    explanation = f"Recommended based on your preferred category: {cat}"
                else:
                    explanation = "Matches items in your browsing and rating history"
            else:
                explanation = "Trending top-rated item in catalog"

            results.append(RecommendationItem(
                product_id=pid,
                title=meta.get("title", f"Product {pid}"),
                category=cat,
                price=float(meta.get("price", 0.0)),
                rating=float(meta.get("rating", 4.0)),
                image_url=meta.get("image_url", ""),
                score=score_val,
                rank=rank,
                algorithm=algo_label,
                explanation=explanation
            ))

        # If not enough results due to heavy exclusions, pad with popularity
        if len(results) < top_n:
            seen_ids = {r.product_id for r in results}.union(excluded_items)
            fallback_items = self.popularity_model.recommend(
                top_n=top_n - len(results),
                exclude_items=seen_ids
            )
            for item in fallback_items:
                item.rank = len(results) + 1
                results.append(item)

        return results

    def save(self, filepath: str | Path) -> None:
        """Persist hybrid model configuration using joblib."""
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str | Path) -> "HybridRecommender":
        """Load persisted hybrid model from disk."""
        model = joblib.load(filepath)
        if not isinstance(model, cls):
            raise TypeError(f"Loaded object is not an instance of {cls.__name__}")
        return model
