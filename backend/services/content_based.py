"""
content_based.py
----------------
Content-Based Recommendation Engine using TF-IDF Vectorization and Cosine Similarity.

Combines product attributes (Title, Category, Features, Description, Store) into a rich
textual representation. Constructs user profile vectors from interaction history and
preferred categories to compute semantic similarity scores.

Features:
- Handles empty or missing text fields gracefully.
- Similar product recommendations (Item-to-Item Content Similarity).
- User profile-based recommendations (User-to-Item Content Matching).
- Fast cosine similarity using linear_kernel on L2-normalized TF-IDF sparse matrices.
- Persistable using joblib.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from .recommendation_engine import RecommendationItem


class ContentBasedRecommender:
    """
    Content-Based Recommender utilizing TF-IDF and Cosine Similarity.
    """

    def __init__(self, max_features: int = 5000):
        self.max_features = int(max_features)
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None  # scipy.sparse.csr_matrix of shape (n_items, max_features)
        self.item2idx: Dict[str, int] = {}
        self.idx2item: Dict[int, str] = {}
        self.product_meta: Dict[str, Dict[str, Any]] = {}
        self.category_map: Dict[str, List[int]] = {}
        self.is_fitted: bool = False

    def fit(self, df_products: pd.DataFrame) -> "ContentBasedRecommender":
        """
        Fit TF-IDF vectorizer and compute content matrix from product metadata.
        """
        if df_products is None or df_products.empty:
            raise ValueError("df_products cannot be empty.")

        # Cache product metadata and indices
        self.product_meta = {}
        self.item2idx = {}
        self.idx2item = {}
        self.category_map = {}

        corpus: List[str] = []
        for idx, (_, row) in enumerate(df_products.iterrows()):
            pid = str(row["product_id"])
            self.item2idx[pid] = idx
            self.idx2item[idx] = pid

            cat = str(row.get("category", "General"))
            self.category_map.setdefault(cat.lower(), []).append(idx)

            self.product_meta[pid] = {
                "product_id": pid,
                "title": str(row.get("title", "")),
                "category": cat,
                "price": float(row.get("price", 0.0)),
                "rating": float(row.get("rating", 4.0)),
                "image_url": str(row.get("image_url", ""))
            }

            # Prepare text for vectorizer
            text = row.get("content_text")
            if text is None or pd.isna(text) or not str(text).strip():
                # Fallback to combining available text fields
                title = str(row.get("title", ""))
                desc = str(row.get("description", ""))
                feat = str(row.get("features", ""))
                text = f"{title} {cat} {feat} {desc}".strip()

            corpus.append(str(text) if text else "product")

        # Initialize TF-IDF Vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words="english",
            sublinear_tf=True,
            ngram_range=(1, 2)
        )

        # L2-normalized TF-IDF matrix
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True
        return self

    def recommend_similar_to_product(
        self,
        product_id: str,
        top_n: int = 10
    ) -> Optional[List[RecommendationItem]]:
        """
        Recommend top_n products most similar in content to target product_id.
        """
        if not self.is_fitted:
            raise RuntimeError("ContentBasedRecommender is not fitted.")

        pid_str = str(product_id)
        if pid_str not in self.item2idx:
            return None

        it_idx = self.item2idx[pid_str]
        target_vector = self.tfidf_matrix[it_idx]

        # linear_kernel computes cosine similarity on L2-normalized vectors
        sim_scores = linear_kernel(target_vector, self.tfidf_matrix).flatten()
        # Exclude self
        sim_scores[it_idx] = -1.0

        top_indices = np.argsort(sim_scores)[::-1][:top_n]
        target_meta = self.product_meta.get(pid_str, {})
        target_title = target_meta.get("title", "this item")[:35]

        results: List[RecommendationItem] = []
        for rank, idx in enumerate(top_indices, start=1):
            score_val = float(sim_scores[idx])
            sim_pid = self.idx2item[idx]
            meta = self.product_meta.get(sim_pid, {})
            results.append(RecommendationItem(
                product_id=sim_pid,
                title=meta.get("title", f"Product {sim_pid}"),
                category=meta.get("category", "General"),
                price=float(meta.get("price", 0.0)),
                rating=float(meta.get("rating", 4.0)),
                image_url=meta.get("image_url", ""),
                score=score_val,
                rank=rank,
                algorithm="content_based",
                explanation=f"Shares characteristics and category with {target_title}..."
            ))

        return results

    def get_item_similarity_vector(self, product_id: str) -> Optional[np.ndarray]:
        """
        Compute raw cosine similarity vector against all catalog items for product_id.
        Returns a 1D numpy array of shape (n_items,), or None if product is not found.
        """
        if not self.is_fitted:
            raise RuntimeError("ContentBasedRecommender is not fitted.")

        pid_str = str(product_id)
        if pid_str not in self.item2idx:
            return None

        it_idx = self.item2idx[pid_str]
        target_vector = self.tfidf_matrix[it_idx]
        sim_scores = linear_kernel(target_vector, self.tfidf_matrix).flatten()
        return sim_scores

    def predict_all_items_for_profile(
        self,
        interacted_items: Optional[List[Tuple[str, float]]] = None,
        preferred_categories: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Generate content match scores across all catalog items for a user profile.
        Returns a 1D numpy array of shape (n_items,).
        """
        if not self.is_fitted:
            raise RuntimeError("ContentBasedRecommender is not fitted.")

        n_items = self.tfidf_matrix.shape[0]
        profile_vec = np.zeros((1, self.tfidf_matrix.shape[1]), dtype=np.float32)
        has_signal = False

        # 1. Accumulate weighted vectors from user interaction history
        if interacted_items:
            for pid, weight in interacted_items:
                pid_str = str(pid)
                if pid_str in self.item2idx:
                    it_idx = self.item2idx[pid_str]
                    item_vec = self.tfidf_matrix[it_idx].toarray()
                    profile_vec += float(weight) * item_vec
                    has_signal = True

        # 2. Accumulate vectors from preferred onboarding categories
        if preferred_categories:
            cat_text = " ".join([c.strip() for c in preferred_categories if c and c.strip()])
            if cat_text:
                cat_vec = self.vectorizer.transform([cat_text]).toarray()
                # Category preference given a baseline weight of 1.5
                profile_vec += 1.5 * cat_vec
                has_signal = True

        if not has_signal:
            return np.zeros(n_items, dtype=np.float32)

        # L2-normalize user profile vector
        norm = np.linalg.norm(profile_vec)
        if norm > 0:
            profile_vec = profile_vec / norm

        # Compute cosine similarities
        scores = linear_kernel(profile_vec, self.tfidf_matrix).flatten()
        return scores

    def recommend_for_user_profile(
        self,
        interacted_items: Optional[List[Tuple[str, float]]] = None,
        preferred_categories: Optional[List[str]] = None,
        top_n: int = 10,
        exclude_interacted: bool = True
    ) -> List[RecommendationItem]:
        """
        Recommend items matching user profile (interaction history + onboarding categories).
        """
        scores = self.predict_all_items_for_profile(interacted_items, preferred_categories)
        if np.all(scores == 0):
            return []

        scores = scores.copy()

        # Exclude interacted items
        if exclude_interacted and interacted_items:
            for pid, _ in interacted_items:
                pid_str = str(pid)
                if pid_str in self.item2idx:
                    scores[self.item2idx[pid_str]] = -1.0

        top_indices = np.argsort(scores)[::-1][:top_n]

        results: List[RecommendationItem] = []
        for rank, idx in enumerate(top_indices, start=1):
            score_val = float(scores[idx])
            if score_val <= 0:
                continue
            pid = self.idx2item[idx]
            meta = self.product_meta.get(pid, {})
            results.append(RecommendationItem(
                product_id=pid,
                title=meta.get("title", f"Product {pid}"),
                category=meta.get("category", "General"),
                price=float(meta.get("price", 0.0)),
                rating=float(meta.get("rating", 4.0)),
                image_url=meta.get("image_url", ""),
                score=score_val,
                rank=rank,
                algorithm="content_based",
                explanation="Matches your browsing history and category preferences"
            ))

        return results

    def save(self, filepath: str | Path) -> None:
        """Persist model artifact using joblib."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted model.")
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str | Path) -> "ContentBasedRecommender":
        """Load persisted model artifact from disk."""
        model = joblib.load(filepath)
        if not isinstance(model, cls):
            raise TypeError(f"Loaded object is not an instance of {cls.__name__}")
        return model
