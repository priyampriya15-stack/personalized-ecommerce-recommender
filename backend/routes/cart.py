"""
cart.py
-------
Shopping cart routes: view cart, add/update items, remove items, and checkout.
"""

from datetime import datetime, timezone
from flask import Blueprint, request, g

from backend.models.database_models import db, User, Product, UserCart, CartItem, Interaction
from backend.models.schemas import success_response, error_response
from backend.routes.auth_helpers import jwt_required

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")


@cart_bp.route("", methods=["GET"])
@jwt_required
def get_cart():
    """Retrieve current user's shopping cart."""
    user: User = g.current_user
    if not user.cart:
        user.cart = UserCart(user_id=user.id)
        db.session.add(user.cart)
        db.session.commit()

    return success_response(user.cart.to_dict(), "Cart retrieved.", 200)


@cart_bp.route("/items", methods=["POST"])
@jwt_required
def add_to_cart():
    """Add a product to cart or increment quantity."""
    user: User = g.current_user
    data = request.get_json(silent=True) or {}
    product_identifier = data.get("product_id")
    quantity = max(1, int(data.get("quantity", 1)))

    if not product_identifier:
        return error_response("product_id is required.", "MISSING_PRODUCT_ID", 400)

    prod_str = str(product_identifier).strip()
    product = Product.query.get(int(prod_str)) if prod_str.isdigit() else Product.query.filter_by(external_product_id=prod_str).first()
    if not product:
        return error_response("Product not found.", "NOT_FOUND", 404)

    if not user.cart:
        user.cart = UserCart(user_id=user.id)
        db.session.add(user.cart)
        db.session.flush()

    # Check if item already exists in cart
    cart_item = CartItem.query.filter_by(cart_id=user.cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=user.cart.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)

    # Also log a 'cart' interaction for recommendation signals
    interaction = Interaction(
        user_id=user.id,
        product_id=product.id,
        interaction_type="cart",
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(interaction)

    db.session.commit()
    return success_response(user.cart.to_dict(), "Item added to cart.", 201)


@cart_bp.route("/items/<int:item_id>", methods=["DELETE"])
@jwt_required
def remove_from_cart(item_id: int):
    """Remove item from cart by cart item ID."""
    user: User = g.current_user
    if not user.cart:
        return error_response("Cart not found.", "NOT_FOUND", 404)

    item = CartItem.query.filter_by(id=item_id, cart_id=user.cart.id).first()
    if not item:
        return error_response("Cart item not found.", "NOT_FOUND", 404)

    db.session.delete(item)
    db.session.commit()
    return success_response(user.cart.to_dict(), "Item removed from cart.", 200)


@cart_bp.route("/checkout", methods=["POST"])
@jwt_required
def checkout():
    """Simulate checkout: converts cart items to purchase interaction records and clears cart."""
    user: User = g.current_user
    if not user.cart or user.cart.items.count() == 0:
        return error_response("Your cart is empty.", "EMPTY_CART", 400)

    now = datetime.now(timezone.utc)
    purchased_items = []

    for item in user.cart.items.all():
        purchased_items.append({
            "product_id": item.product_id,
            "title": item.product.title if item.product else "",
            "quantity": item.quantity,
            "subtotal": round(item.product.price * item.quantity, 2) if item.product else 0.0
        })
        # Record real 'purchase' interaction
        purchase_event = Interaction(
            user_id=user.id,
            product_id=item.product_id,
            interaction_type="purchase",
            timestamp=now
        )
        db.session.add(purchase_event)
        db.session.delete(item)

    db.session.commit()
    return success_response({
        "order_id": f"ORD-{int(now.timestamp())}-{user.id}",
        "purchased_items": purchased_items,
        "total_amount": round(sum(p["subtotal"] for p in purchased_items), 2),
        "status": "completed"
    }, "Order placed successfully.", 200)
