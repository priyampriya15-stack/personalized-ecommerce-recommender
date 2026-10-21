"""
backend.routes
--------------
Route blueprints package.
"""

from .auth import auth_bp
from .products import products_bp
from .recommendations import recommendations_bp
from .interactions import interactions_bp
from .cart import cart_bp
from .orders import orders_bp
from .admin import admin_bp

__all__ = [
    "auth_bp",
    "products_bp",
    "recommendations_bp",
    "interactions_bp",
    "cart_bp",
    "orders_bp",
    "admin_bp",
]
