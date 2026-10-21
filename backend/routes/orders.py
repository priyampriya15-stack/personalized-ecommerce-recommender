"""
orders.py
---------
Order management endpoints: Create Order (Cart or Buy Now), View Orders,
Order Details, and Order Cancellation.
Uses real SQLite products, prices, and user isolation.
"""

from datetime import datetime, timezone
from flask import Blueprint, request, g
from backend.models.database_models import db, User, Product, Order, OrderItem, UserCart, CartItem, Interaction
from backend.models.schemas import success_response, error_response
from backend.routes.auth_helpers import jwt_required

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@orders_bp.route("/quote", methods=["POST"])
@jwt_required
def get_order_quote():
    """
    Calculate server-side order preview / quote with verified SQLite prices.
    Accepts either direct item ({ product_id, quantity }) for Buy Now,
    or calculates from authenticated user's cart ({ source: 'cart' }).
    """
    user: User = g.current_user
    payload = request.get_json(silent=True) or {}
    source = payload.get("source")
    product_id = payload.get("product_id")
    quantity = payload.get("quantity", 1)

    items_to_quote = []

    if product_id is not None:
        # Buy Now direct item
        try:
            p_id = int(product_id)
            qty = int(quantity)
        except (ValueError, TypeError):
            return error_response("Invalid product ID or quantity format.", "BAD_REQUEST", 400)

        if qty <= 0:
            return error_response("Quantity must be greater than 0.", "INVALID_QUANTITY", 400)

        product = db.session.get(Product, p_id)
        if not product:
            return error_response(f"Product #{p_id} not found.", "NOT_FOUND", 404)

        unit_price = float(product.price) if product.price is not None else 0.0
        subtotal = round(unit_price * qty, 2)

        items_to_quote.append({
            "product_id": product.id,
            "external_product_id": product.external_product_id,
            "title": product.title,
            "category": product.category,
            "image_url": product.image_url,
            "unit_price": unit_price,
            "quantity": qty,
            "subtotal": subtotal
        })

    else:
        # Cart checkout
        cart = user.cart
        if not cart or not cart.items.count():
            return error_response("Your shopping cart is currently empty.", "EMPTY_CART", 400)

        for c_item in cart.items:
            prod = c_item.product
            if not prod:
                continue
            unit_price = float(prod.price) if prod.price is not None else 0.0
            subtotal = round(unit_price * c_item.quantity, 2)
            items_to_quote.append({
                "product_id": prod.id,
                "external_product_id": prod.external_product_id,
                "title": prod.title,
                "category": prod.category,
                "image_url": prod.image_url,
                "unit_price": unit_price,
                "quantity": c_item.quantity,
                "subtotal": subtotal
            })

    if not items_to_quote:
        return error_response("No valid items found for checkout.", "EMPTY_QUOTE", 400)

    total_amount = round(sum(i["subtotal"] for i in items_to_quote), 2)

    return success_response({
        "items": items_to_quote,
        "items_count": sum(i["quantity"] for i in items_to_quote),
        "total_amount": total_amount
    }, "Order quote calculated from real database prices.", 200)


@orders_bp.route("", methods=["POST"])
@jwt_required
def create_order():
    """
    Create a new order in SQLite.
    Prices are strictly computed server-side from Product.price in SQLite.
    Accepts direct product ({ product_id, quantity }) for Buy Now,
    or creates an order from the user's active cart.
    """
    user: User = g.current_user
    payload = request.get_json(silent=True) or {}
    product_id = payload.get("product_id")
    quantity = payload.get("quantity", 1)

    order_items_to_create = []

    if product_id is not None:
        # Buy Now direct single-item order
        try:
            p_id = int(product_id)
            qty = int(quantity)
        except (ValueError, TypeError):
            return error_response("Invalid product ID or quantity format.", "BAD_REQUEST", 400)

        if qty <= 0:
            return error_response("Quantity must be greater than 0.", "INVALID_QUANTITY", 400)

        product = db.session.get(Product, p_id)
        if not product:
            return error_response(f"Product #{p_id} not found.", "NOT_FOUND", 404)

        unit_price = float(product.price) if product.price is not None else 0.0
        subtotal = round(unit_price * qty, 2)

        order = Order(
            user_id=user.id,
            status="PENDING",
            total_amount=subtotal,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price,
            subtotal=subtotal
        )
        db.session.add(item)

        # Record purchase/order interaction
        try:
            inter = Interaction(
                user_id=user.id,
                product_id=product.id,
                interaction_type="cart",
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(inter)
        except Exception:
            pass

    else:
        # Cart checkout order
        cart = user.cart
        if not cart or not cart.items.count():
            return error_response("Shopping cart is empty. Cannot create order.", "EMPTY_CART", 400)

        cart_items_list = cart.items.all()
        total_amount = 0.0

        order = Order(
            user_id=user.id,
            status="PENDING",
            total_amount=0.0,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(order)
        db.session.flush()

        for c_item in cart_items_list:
            prod = c_item.product
            if not prod:
                continue

            if c_item.quantity <= 0:
                continue

            unit_price = float(prod.price) if prod.price is not None else 0.0
            subtotal = round(unit_price * c_item.quantity, 2)
            total_amount += subtotal

            o_item = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                quantity=c_item.quantity,
                unit_price=unit_price,
                subtotal=subtotal
            )
            db.session.add(o_item)

            # Clear cart item
            db.session.delete(c_item)

        order.total_amount = round(total_amount, 2)

    db.session.commit()
    return success_response(order.to_dict(), "Order created successfully in database.", 201)


@orders_bp.route("", methods=["GET"])
@jwt_required
def get_user_orders():
    """
    Retrieve list of orders belonging strictly to the authenticated user.
    Enforces user data isolation.
    """
    user: User = g.current_user
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    results = [o.to_dict() for o in orders]
    return success_response(results, f"Retrieved {len(results)} orders.", 200)


@orders_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required
def get_order_by_id(order_id: int):
    """
    Retrieve single order by ID.
    Enforces user ownership check (User A cannot view User B's order).
    """
    user: User = g.current_user
    order = db.session.get(Order, order_id)
    if not order:
        return error_response(f"Order #{order_id} not found.", "NOT_FOUND", 404)

    if order.user_id != user.id and user.role != "admin":
        return error_response("Access denied: You can only view your own orders.", "FORBIDDEN", 403)

    return success_response(order.to_dict(), "Order details retrieved.", 200)


@orders_bp.route("/<int:order_id>/cancel", methods=["POST"])
@jwt_required
def cancel_order(order_id: int):
    """
    Cancel an existing order.
    Enforces that only the order owner (or admin) can cancel.
    Only PENDING orders can be cancelled. Does NOT delete the database record.
    """
    user: User = g.current_user
    order = db.session.get(Order, order_id)
    if not order:
        return error_response(f"Order #{order_id} not found.", "NOT_FOUND", 404)

    if order.user_id != user.id and user.role != "admin":
        return error_response("Access denied: You can only cancel your own orders.", "FORBIDDEN", 403)

    if order.status != "PENDING":
        return error_response(
            f"Cannot cancel order #{order_id} with status '{order.status}'. Only PENDING orders can be cancelled.",
            "INVALID_ORDER_STATUS",
            400
        )

    order.status = "CANCELLED"
    order.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response(order.to_dict(), f"Order #{order_id} has been cancelled.", 200)


@orders_bp.route("/buy-now", methods=["POST"])
@jwt_required
def buy_now_order():
    """
    Dedicated endpoint for Buy Now single-item direct orders.
    Validates product exists in SQLite, reads real unit price,
    creates order and order item, and returns created order.
    """
    user: User = g.current_user
    payload = request.get_json(silent=True) or {}
    product_id = payload.get("product_id")
    quantity = payload.get("quantity", 1)

    if product_id is None:
        return error_response("Missing required 'product_id' parameter.", "BAD_REQUEST", 400)

    try:
        p_id = int(product_id)
        qty = int(quantity)
    except (ValueError, TypeError):
        return error_response("Invalid product ID or quantity format.", "BAD_REQUEST", 400)

    if qty <= 0:
        return error_response("Quantity must be greater than 0.", "INVALID_QUANTITY", 400)

    product = db.session.get(Product, p_id)
    if not product:
        return error_response(f"Product #{p_id} not found.", "NOT_FOUND", 404)

    unit_price = float(product.price) if product.price is not None else 0.0
    subtotal = round(unit_price * qty, 2)

    order = Order(
        user_id=user.id,
        status="PENDING",
        total_amount=subtotal,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.session.add(order)
    db.session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=qty,
        unit_price=unit_price,
        subtotal=subtotal,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(item)

    try:
        inter = Interaction(
            user_id=user.id,
            product_id=product.id,
            interaction_type="cart",
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(inter)
    except Exception:
        pass

    db.session.commit()
    return success_response(order.to_dict(), "Buy Now order created successfully in database.", 201)

