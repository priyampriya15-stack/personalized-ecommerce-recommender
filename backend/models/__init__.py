"""
backend.models
--------------
Database models and schema validation package.
"""

from .database_models import (
    db,
    User,
    Product,
    UserPreference,
    Interaction,
    RecommendationLog,
    UserCart,
    CartItem,
    Order,
    OrderItem
)
from .schemas import success_response, error_response, validate_email

__all__ = [
    "db",
    "User",
    "Product",
    "UserPreference",
    "Interaction",
    "RecommendationLog",
    "UserCart",
    "CartItem",
    "Order",
    "OrderItem",
    "success_response",
    "error_response",
    "validate_email",
]
