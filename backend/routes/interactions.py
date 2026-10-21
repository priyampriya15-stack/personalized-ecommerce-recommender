"""
interactions.py
---------------
Interaction tracking and user preferences endpoints.
Supports interaction types: 'view', 'like', 'rating', 'cart', 'purchase'.
"""

from datetime import datetime, timezone
from flask import Blueprint, request, g

from backend.models.database_models import db, User, Product, Interaction, UserPreference
from backend.models.schemas import success_response, error_response
from backend.routes.auth_helpers import jwt_required

interactions_bp = Blueprint("interactions", __name__, url_prefix="/api")


@interactions_bp.route("/interactions", methods=["POST"])
@jwt_required
def record_interaction():
    """
    Record or update a user-product interaction event ('view', 'like', 'rating', 'cart', 'purchase').
    """
    user: User = g.current_user
    data = request.get_json(silent=True) or {}

    product_identifier = data.get("product_id")
    interaction_type = str(data.get("interaction_type", "")).strip().lower()
    rating_val = data.get("rating")

    valid_types = {"view", "like", "rating", "cart", "purchase"}
    if interaction_type not in valid_types:
        return error_response(f"Invalid interaction_type. Must be one of: {', '.join(valid_types)}", "INVALID_TYPE", 400)

    if not product_identifier:
        return error_response("product_id is required.", "MISSING_PRODUCT_ID", 400)

    # Resolve product by int ID or external ASIN
    prod_str = str(product_identifier).strip()
    product = None
    if prod_str.isdigit():
        product = db.session.get(Product, int(prod_str))
    if not product:
        product = Product.query.filter_by(external_product_id=prod_str).first()

    if not product:
        return error_response(f"Product '{product_identifier}' not found.", "NOT_FOUND", 404)

    # Validate rating range if provided
    parsed_rating = None
    if rating_val is not None:
        try:
            parsed_rating = float(rating_val)
            if parsed_rating < 1.0 or parsed_rating > 5.0:
                return error_response("Rating must be a numerical value between 1.0 and 5.0.", "INVALID_RATING", 400)
        except (ValueError, TypeError):
            return error_response("Rating must be a valid number.", "INVALID_RATING", 400)

    try:
        # Check if an interaction of this type already exists for this user and product
        existing = Interaction.query.filter_by(
            user_id=user.id,
            product_id=product.id,
            interaction_type=interaction_type
        ).first()

        now = datetime.now(timezone.utc)
        if existing:
            existing.timestamp = now
            if parsed_rating is not None:
                existing.rating = parsed_rating
            interaction_record = existing
        else:
            interaction_record = Interaction(
                user_id=user.id,
                product_id=product.id,
                interaction_type=interaction_type,
                rating=parsed_rating,
                timestamp=now
            )
            db.session.add(interaction_record)

        db.session.commit()
        return success_response(interaction_record.to_dict(), "Interaction recorded successfully.", 201)

    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to record interaction: {str(e)}", "SERVER_ERROR", 500)


@interactions_bp.route("/users/<user_id>/history", methods=["GET"])
@jwt_required
def get_user_history(user_id: str):
    """Retrieve interaction history for user_id with optional type filter."""
    current_user: User = g.current_user
    is_self = str(user_id).lower() == "me" or str(current_user.id) == str(user_id)

    if not is_self and current_user.role != "admin":
        return error_response("Access denied: You can only view your own interaction history.", "FORBIDDEN", 403)

    target_user = current_user if is_self else (db.session.get(User, int(user_id)) if str(user_id).isdigit() else None)
    if not target_user:
        return error_response("User not found.", "NOT_FOUND", 404)

    interaction_type = request.args.get("type", type=str)
    query = target_user.interactions.order_by(Interaction.timestamp.desc())

    if interaction_type:
        query = query.filter(Interaction.interaction_type == interaction_type.strip().lower())

    limit = min(request.args.get("limit", 50, type=int), 100)
    items = query.limit(limit).all()

    return success_response([i.to_dict() for i in items], "User history retrieved.", 200)


@interactions_bp.route("/users/preferences", methods=["POST"])
@jwt_required
def update_preferences():
    """Update preferred categories for the authenticated user with validation and weights."""
    user: User = g.current_user
    data = request.get_json(silent=True) or {}
    categories = data.get("categories", [])

    if not isinstance(categories, list):
        return error_response("Categories must be provided as a list.", "INVALID_INPUT", 400)

    # Query valid catalog categories from database
    db_cats = {c[0] for c in db.session.query(Product.category).distinct().all() if c[0]}
    cat_map_lower = {c.lower(): c for c in db_cats}

    validated_prefs = []
    # Assign weights: primary = 2.0, secondary = 1.5, optional = 1.0
    tier_weights = [2.0, 1.5, 1.0]

    for idx, item in enumerate(categories):
        if isinstance(item, dict):
            raw_cat = str(item.get("category", "")).strip()
            weight = float(item.get("weight", tier_weights[min(idx, len(tier_weights) - 1)]))
        else:
            raw_cat = str(item).strip()
            weight = tier_weights[min(idx, len(tier_weights) - 1)]

        if not raw_cat:
            continue

        matched_cat = cat_map_lower.get(raw_cat.lower())
        if not matched_cat:
            return error_response(
                f"Invalid category '{raw_cat}'. Allowed categories: {', '.join(sorted(db_cats))}",
                "INVALID_CATEGORY",
                400
            )

        validated_prefs.append((matched_cat, weight))

    try:
        # Clear existing preferences
        UserPreference.query.filter_by(user_id=user.id).delete()

        created_prefs = []
        for cat_name, w in validated_prefs:
            pref = UserPreference(user_id=user.id, category=cat_name, preference_weight=w)
            db.session.add(pref)
            created_prefs.append(pref)

        db.session.commit()
        return success_response([p.to_dict() for p in created_prefs], "Preferences updated successfully.", 200)

    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to update preferences: {str(e)}", "SERVER_ERROR", 500)

