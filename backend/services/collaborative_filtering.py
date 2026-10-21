"""
collaborative_filtering.py
--------------------------
Matrix Factorization Collaborative Filtering using Truncated SVD.

Decomposes the sparse user-item interaction matrix R in R^(|U| x |I|) into:
    R approx U_k * Sigma_k * V_k^T
where:
    U_k is the user latent factor matrix
    V_k is the item latent factor matrix
    Predicted score r_hat(u, i) = user_factors[u] . item_factors[i]^T

Features:
- Handles sparse interaction matrices efficiently (scipy.sparse.csr_matrix).
- Excludes previously interacted items to ensure recommendation novelty.
- Provides latent item-item cosine similarity for item-based recommendations.
- Gracefully handles cold/unseen users by returning None to trigger fallback.
- Persistable using joblib.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

from .recommendation_engine import RecommendationItem


class CollaborativeFilteringRecommender:
    """
    Personalized Matrix Factorization Collaborative Filtering Recommender.
    """

    def __init__(self, n_components: int = 30, random_state: int = 42):
        self.n_components = int(n_components)
        self.random_state = int(random_state)
        self.svd: Optional[TruncatedSVD] = None
        self.user2idx: Dict[str, int] = {}
        self.idx2user: Dict[int, str] = {}
        self.item2idx: Dict[str, int] = {}
        self.idx2item: Dict[int, str] = {}
        self.user_latent: Optional[np.ndarray] = None  # Shape: (n_users, n_components)
        self.item_latent: Optional[np.ndarray] = None  # Shape: (n_items, n_components)
        self.item_latent_normalized: Optional[np.ndarray] = None
        self.product_meta: Dict[str, Dict[str, Any]] = {}
        self.user_interacted_items: Dict[str, Set[str]] = {}
        self.is_fitted: bool = False

    def fit(self, df_products: pd.DataFrame, df_interactions: pd.DataFrame) -> "CollaborativeFilteringRecommender":
        """
        Fit Truncated SVD model on user-item interaction matrix.
        """
        if df_products is None or df_products.empty:
            raise ValueError("df_products cannot be empty.")
        if df_interactions is None or df_interactions.empty:
            raise ValueError("df_interactions cannot be empty.")

        # Cache product metadata
        self.product_meta = {}
        for _, row in df_products.iterrows():
            pid = str(row["product_id"])
            self.product_meta[pid] = {
                "product_id": pid,
                "title": str(row.get("title", "")),
                "category": str(row.get("category", "")),
                "price": float(row.get("price", 0.0)),
                "rating": float(row.get("rating", 4.0)),
                "image_url": str(row.get("image_url", ""))
            }

        # Build mappings
        unique_users = df_interactions["user_id"].unique()
        # Include all products that have metadata so we can score full catalog
        unique_items = df_products["product_id"].unique()

        self.user2idx = {str(u): i for i, u in enumerate(unique_users)}
        self.idx2user = {i: str(u) for i, u in enumerate(unique_users)}
        self.item2idx = {str(it): i for i, it in enumerate(unique_items)}
        self.idx2item = {i: str(it) for i, it in enumerate(unique_items)}

        # Build interaction history cache per user
        self.user_interacted_items = {}
        for uid, group in df_interactions.groupby("user_id"):
            self.user_interacted_items[str(uid)] = set(group["product_id"].astype(str))

        # Build sparse user-item interaction matrix
        # Map IDs to indices, filtering interactions to items in catalog
        valid_interactions = df_interactions[df_interactions["product_id"].astype(str).isin(self.item2idx)].copy()
        row_indices = [self.user2idx[str(u)] for u in valid_interactions["user_id"]]
        col_indices = [self.item2idx[str(it)] for it in valid_interactions["product_id"]]
        ratings = valid_interactions["rating"].astype(float).values

        n_users = len(self.user2idx)
        n_items = len(self.item2idx)

        interaction_matrix = csr_matrix(
            (ratings, (row_indices, col_indices)),
            shape=(n_users, n_items),
            dtype=np.float32
        )

        # Truncated SVD dimensionality reduction
        # Clamp n_components if fewer users or items exist
        k = min(self.n_components, min(n_users, n_items) - 1)
        if k < 2:
            k = 2

        self.svd = TruncatedSVD(n_components=k, random_state=self.random_state)
        # user_latent: U * Sigma
        self.user_latent = self.svd.fit_transform(interaction_matrix)
        # item_latent: V
        self.item_latent = self.svd.components_.T  # Shape: (n_items, k)

        # Normalize item latent vectors for cosine similarity
        norms = np.linalg.norm(self.item_latent, axis=1, keepdims=True)
        norms[norms == 0] = 1e-12
        self.item_latent_normalized = self.item_latent / norms

        self.is_fitted = True
        return self

    def predict_all_items(self, user_id: str) -> Optional[np.ndarray]:
        """
        Compute predicted scores for all items in the catalog for a given user.
        Returns a 1D numpy array of shape (n_items,), or None if user is unknown.
        """
        if not self.is_fitted:
            raise RuntimeError("CollaborativeFilteringRecommender is not fitted.")

        user_id_str = str(user_id)
        if user_id_str not in self.user2idx:
            return None

        u_idx = self.user2idx[user_id_str]
        user_vector = self.user_latent[u_idx]  # Shape: (k,)
        # Dot product with all item vectors: user_vector . item_latent^T
        scores = np.dot(self.item_latent, user_vector)  # Shape: (n_items,)
        return scores

    def recommend(
        self,
        user_id: str,
        top_n: int = 10,
        exclude_interacted: bool = True
    ) -> Optional[List[RecommendationItem]]:
        """
        Generate top_n personalized recommendations for user_id.
        Returns None for cold/unseen users.
        """
        scores = self.predict_all_items(user_id)
        if scores is None:
            return None

        scores = scores.copy()
        user_id_str = str(user_id)

        # Mask previously interacted items
        if exclude_interacted and user_id_str in self.user_interacted_items:
            interacted_items = self.user_interacted_items[user_id_str]
            for it in interacted_items:
                if it in self.item2idx:
                    scores[self.item2idx[it]] = -1e9

        # Get top item indices
        top_indices = np.argsort(scores)[::-1][:top_n]

        results: List[RecommendationItem] = []
        for rank, idx in enumerate(top_indices, start=1):
            score_val = float(scores[idx])
            if score_val <= -1e8:
                continue

            product_id = self.idx2item[idx]
            meta = self.product_meta.get(product_id, {})
            results.append(RecommendationItem(
                product_id=product_id,
                title=meta.get("title", f"Product {product_id}"),
                category=meta.get("category", "General"),
                price=float(meta.get("price", 0.0)),
                rating=float(meta.get("rating", 4.0)),
                image_url=meta.get("image_url", ""),
                score=score_val,
                rank=rank,
                algorithm="collaborative_filtering",
                explanation="Recommended because shoppers with similar taste liked this"
            ))

        return results

    def recommend_similar_items(self, product_id: str, top_n: int = 10) -> Optional[List[RecommendationItem]]:
        """
        Find items with highest cosine similarity in the latent factor space.
        """
        if not self.is_fitted:
            raise RuntimeError("CollaborativeFilteringRecommender is not fitted.")

        pid_str = str(product_id)
        if pid_str not in self.item2idx:
            return None

        it_idx = self.item2idx[pid_str]
        target_vector = self.item_latent_normalized[it_idx]  # Shape: (k,)
        # Cosine similarity against all items
        sim_scores = np.dot(self.item_latent_normalized, target_vector)
        # Exclude self
        sim_scores[it_idx] = -1.0

        top_indices = np.argsort(sim_scores)[::-1][:top_n]

        results: List[RecommendationItem] = []
        for rank, idx in enumerate(top_indices, start=1):
            sim_val = float(sim_scores[idx])
            sim_pid = self.idx2item[idx]
            meta = self.product_meta.get(sim_pid, {})
            results.append(RecommendationItem(
                product_id=sim_pid,
                title=meta.get("title", f"Product {sim_pid}"),
                category=meta.get("category", "General"),
                price=float(meta.get("price", 0.0)),
                rating=float(meta.get("rating", 4.0)),
                image_url=meta.get("image_url", ""),
                score=sim_val,
                rank=rank,
                algorithm="collaborative_similarity",
                explanation=f"Co-rated product similar to {meta.get('title', 'viewed item')[:35]}"
            ))

        return results

    def save(self, filepath: str | Path) -> None:
        """Persist model artifact using joblib."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted model.")
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str | Path) -> "CollaborativeFilteringRecommender":
        """Load persisted model artifact from disk."""
        model = joblib.load(filepath)
        if not isinstance(model, cls):
            raise TypeError(f"Loaded object is not an instance of {cls.__name__}")
        return model
