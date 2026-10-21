"""
recommendation_engine.py
------------------------
Core recommendation data structures and the Popularity-Based Recommender.

Implements the Bayesian Weighted Rating (adapted from the IMDb formula for e-commerce):
    W = (v / (v + m)) * R + (m / (v + m)) * C
where:
    v = number of interactions/ratings for the product
    m = minimum interaction threshold (configurable)
    R = average rating of the product
    C = global mean rating across all products
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import joblib
import numpy as np
import pandas as pd


@dataclass
class RecommendationItem:
    """Standardized representation of a single recommended product."""
    product_id: str
    title: str
    category: str
    price: float
    rating: float
    image_url: str
    score: float
    rank: int
    algorithm: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to JSON-serializable dictionary."""
        return {
            "product_id": self.product_id,
            "title": self.title,
            "category": self.category,
            "price": round(float(self.price), 2),
            "rating": round(float(self.rating), 2),
            "image_url": self.image_url,
            "score": round(float(self.score), 4),
            "rank": int(self.rank),
            "algorithm": self.algorithm,
            "explanation": self.explanation
        }


class PopularityRecommender:
    """
    Bayesian Weighted Popularity Recommender.
    Provides robust non-personalized baseline and cold-start fallback.
    """

    def __init__(self, min_threshold: int = 3):
        self.min_threshold = int(min_threshold)
        self.global_mean: float = 4.0
        self.catalog_df: Optional[pd.DataFrame] = None
        self.ranked_products: Optional[pd.DataFrame] = None
        self.is_fitted: bool = False

    def fit(self, df_products: pd.DataFrame, df_interactions: pd.DataFrame) -> "PopularityRecommender":
        """
        Fit popularity baseline from products and interaction datasets.
        """
        if df_products is None or df_products.empty:
            raise ValueError("df_products cannot be empty.")
        if df_interactions is None or df_interactions.empty:
            raise ValueError("df_interactions cannot be empty.")

        # Compute global mean rating C
        self.global_mean = float(df_interactions["rating"].mean())
        m = float(self.min_threshold)
        C = self.global_mean

        # Aggregate interaction counts and average rating per product
        stats = df_interactions.groupby("product_id").agg(
            v=("rating", "count"),
            R=("rating", "mean")
        ).reset_index()

        # Merge with full catalog (so unreviewed items also exist with v=0)
        df_merged = df_products[[
            "product_id", "title", "category", "price", "rating", "image_url"
        ]].merge(stats, on="product_id", how="left")

        df_merged["v"] = df_merged["v"].fillna(0).astype(int)
        # For items with 0 interactions, default R to item catalog rating or global mean
        df_merged["R"] = df_merged.apply(
            lambda row: row["R"] if row["v"] > 0 else (row["rating"] if not pd.isna(row["rating"]) else C),
            axis=1
        )

        # Compute Bayesian Weighted Rating: W = (v / (v + m)) * R + (m / (v + m)) * C
        df_merged["score"] = (
            (df_merged["v"] / (df_merged["v"] + m)) * df_merged["R"] +
            (m / (df_merged["v"] + m)) * C
        )

        # Sort descending by score, tie-breaking by interaction count v
        self.ranked_products = df_merged.sort_values(
            by=["score", "v"], ascending=[False, False]
        ).reset_index(drop=True)

        self.catalog_df = df_products.copy()
        self.is_fitted = True
        return self

    def recommend(
        self,
        top_n: int = 10,
        category: Optional[str] = None,
        exclude_items: Optional[Set[str]] = None
    ) -> List[RecommendationItem]:
        """
        Generate ranked popular recommendations with optional category filter
        and exclusion of previously interacted items.
        """
        if not self.is_fitted or self.ranked_products is None:
            raise RuntimeError("PopularityRecommender must be fitted before calling recommend().")

        df = self.ranked_products

        # Category filtering
        if category:
            df = df[df["category"].str.lower() == category.strip().lower()]

        # Exclude interacted items
        if exclude_items:
            df = df[~df["product_id"].isin(exclude_items)]

        candidates = df.head(top_n)

        results: List[RecommendationItem] = []
        for rank, (_, row) in enumerate(candidates.iterrows(), start=1):
            category_label = row.get("category", "Trending")
            explanation = (
                f"Top-rated in {category_label} with {int(row['v'])} customer reviews"
                if int(row["v"]) >= self.min_threshold
                else f"Popular choice in {category_label}"
            )
            results.append(RecommendationItem(
                product_id=str(row["product_id"]),
                title=str(row["title"]),
                category=str(row["category"]),
                price=float(row["price"]),
                rating=float(row["rating"]),
                image_url=str(row["image_url"]),
                score=float(row["score"]),
                rank=rank,
                algorithm="popularity",
                explanation=explanation
            ))

        return results

    def save(self, filepath: str | Path) -> None:
        """Persist model artifact using joblib."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted model.")
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str | Path) -> "PopularityRecommender":
        """Load persisted model artifact from disk."""
        model = joblib.load(filepath)
        if not isinstance(model, cls):
            raise TypeError(f"Loaded object is not an instance of {cls.__name__}")
        return model
