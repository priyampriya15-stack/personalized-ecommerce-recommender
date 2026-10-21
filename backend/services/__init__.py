"""
backend.services
----------------
Recommendation services and algorithms package.
"""

from .recommendation_engine import RecommendationItem, PopularityRecommender
from .collaborative_filtering import CollaborativeFilteringRecommender
from .content_based import ContentBasedRecommender
from .hybrid_recommender import HybridRecommender, min_max_normalize

__all__ = [
    "RecommendationItem",
    "PopularityRecommender",
    "CollaborativeFilteringRecommender",
    "ContentBasedRecommender",
    "HybridRecommender",
    "min_max_normalize",
]
