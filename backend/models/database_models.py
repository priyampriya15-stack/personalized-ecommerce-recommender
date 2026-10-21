"""
database_models.py
------------------
SQLAlchemy ORM models for Users, Products, User Preferences,
Interactions, Recommendation Logs, and Cart Management.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Registered platform user."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    preferences = db.relationship("UserPreference", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    interactions = db.relationship("Interaction", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    cart = db.relationship("UserCart", backref="user", uselist=False, cascade="all, delete-orphan")
    recommendation_logs = db.relationship("RecommendationLog", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    orders = db.relationship("Order", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Hash plaintext password using bcrypt."""
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify plaintext password against bcrypt hash."""
        if not self.password_hash or not password:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to safe dictionary (no password hash)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Product(db.Model):
    """E-commerce catalog item mapped from real Amazon 2023 dataset."""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    external_product_id = db.Column(db.String(50), unique=True, index=True, nullable=False)  # Amazon ASIN
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), index=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, default=4.0, nullable=False)
    image_url = db.Column(db.Text, nullable=True)

    # Relationships
    interactions = db.relationship("Interaction", backref="product", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary."""
        return {
            "id": self.id,
            "external_product_id": self.external_product_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "price": round(float(self.price), 2),
            "rating": round(float(self.rating), 2),
            "image_url": self.image_url
        }


class UserPreference(db.Model):
    """User category affinity preferences established during onboarding."""
    __tablename__ = "user_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    preference_weight = db.Column(db.Float, default=1.0, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "preference_weight": float(self.preference_weight)
        }


class Interaction(db.Model):
    """Live and historical user-product interaction event."""
    __tablename__ = "interactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False)  # 'view', 'like', 'rating', 'cart', 'purchase'
    rating = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "product_title": self.product.title if self.product else None,
            "external_product_id": self.product.external_product_id if self.product else None,
            "category": self.product.category if self.product else None,
            "image_url": self.product.image_url if self.product else None,
            "price": self.product.price if self.product else None,
            "interaction_type": self.interaction_type,
            "rating": float(self.rating) if self.rating is not None else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class RecommendationLog(db.Model):
    """Audit log of generated recommendations for analytics."""
    __tablename__ = "recommendation_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    algorithm = db.Column(db.String(50), nullable=False)
    recommendation_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "algorithm": self.algorithm,
            "recommendation_score": round(float(self.recommendation_score), 4),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UserCart(db.Model):
    """User shopping cart container."""
    __tablename__ = "user_cart"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    items = db.relationship("CartItem", backref="cart", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self) -> Dict[str, Any]:
        cart_items = [item.to_dict() for item in self.items]
        total_price = sum(item["subtotal"] for item in cart_items)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "items": cart_items,
            "total_items": sum(item["quantity"] for item in cart_items),
            "total_price": round(total_price, 2)
        }


class CartItem(db.Model):
    """Individual item inside user cart."""
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("user_cart.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product = db.relationship("Product")

    def to_dict(self) -> Dict[str, Any]:
        unit_price = float(self.product.price) if self.product else 0.0
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "external_product_id": self.product.external_product_id if self.product else None,
            "title": self.product.title if self.product else "",
            "category": self.product.category if self.product else "",
            "image_url": self.product.image_url if self.product else "",
            "price": unit_price,
            "quantity": self.quantity,
            "subtotal": round(unit_price * self.quantity, 2),
            "added_at": self.added_at.isoformat() if self.added_at else None
        }


class Order(db.Model):
    """User order container."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(20), default="PENDING", nullable=False, index=True)  # 'PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED'
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=True)

    # Relationships
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self) -> Dict[str, Any]:
        order_items = [item.to_dict() for item in self.items]
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "total_amount": round(float(self.total_amount), 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else (self.created_at.isoformat() if self.created_at else None),
            "items_count": sum(item["quantity"] for item in order_items),
            "items": order_items
        }


class OrderItem(db.Model):
    """Line item inside a user order."""
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    product = db.relationship("Product")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "external_product_id": self.product.external_product_id if self.product else None,
            "title": self.product.title if self.product else "",
            "category": self.product.category if self.product else "",
            "image_url": self.product.image_url if self.product else "",
            "quantity": self.quantity,
            "unit_price": round(float(self.unit_price), 2),
            "subtotal": round(float(self.subtotal), 2),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


