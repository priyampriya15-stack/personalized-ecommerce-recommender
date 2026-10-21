"""
auth.py
-------
Authentication routes for User Registration, Login, and Current User profile.
"""

from flask import Blueprint, request, g
from backend.models.database_models import db, User, Product, UserPreference, UserCart
from backend.models.schemas import success_response, error_response, validate_email
from backend.routes.auth_helpers import generate_jwt_token, jwt_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account with optional onboarding category preferences."""
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    categories = data.get("categories", [])  # Optional onboarding categories

    if not name or len(name) < 2:
        return error_response("Name must be at least 2 characters long.", "INVALID_INPUT", 400)

    if not validate_email(email):
        return error_response("Please provide a valid email address.", "INVALID_EMAIL", 400)

    if not password or len(password) < 6:
        return error_response("Password must be at least 6 characters long.", "WEAK_PASSWORD", 400)

    # Check for duplicate email
    if User.query.filter_by(email=email).first():
        return error_response("An account with this email address already exists.", "DUPLICATE_EMAIL", 409)

    # Validate categories against database if provided
    validated_prefs = []
    if isinstance(categories, list) and categories:
        db_cats = {c[0] for c in db.session.query(Product.category).distinct().all() if c[0]}
        cat_map_lower = {c.lower(): c for c in db_cats}
        tier_weights = [2.0, 1.5, 1.0]

        for idx, item in enumerate(categories):
            raw_cat = str(item.get("category", "") if isinstance(item, dict) else item).strip()
            if not raw_cat:
                continue
            matched_cat = cat_map_lower.get(raw_cat.lower())
            if not matched_cat:
                return error_response(
                    f"Invalid category '{raw_cat}'. Allowed categories: {', '.join(sorted(db_cats))}",
                    "INVALID_CATEGORY",
                    400
                )
            weight = float(item.get("weight", tier_weights[min(idx, len(tier_weights) - 1)])) if isinstance(item, dict) else tier_weights[min(idx, len(tier_weights) - 1)]
            validated_prefs.append((matched_cat, weight))

    try:
        user = User(name=name, email=email, role="user")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user.id

        # Save onboarding category preferences if provided
        for cat_name, w in validated_prefs:
            pref = UserPreference(user_id=user.id, category=cat_name, preference_weight=w)
            db.session.add(pref)

        # Initialize shopping cart
        cart = UserCart(user_id=user.id)
        db.session.add(cart)

        db.session.commit()

        token = generate_jwt_token(user.id, user.role)
        response_data = {
            "user": user.to_dict(),
            "token": token
        }
        return success_response(response_data, "Registration successful.", 201)

    except Exception as e:
        db.session.rollback()
        return error_response(f"Registration failed: {str(e)}", "SERVER_ERROR", 500)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user with email and password, returning signed JWT token."""
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return error_response("Email and password are required.", "MISSING_CREDENTIALS", 400)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return error_response("Invalid email or password.", "INVALID_CREDENTIALS", 401)

    token = generate_jwt_token(user.id, user.role)
    response_data = {
        "user": user.to_dict(),
        "token": token
    }
    return success_response(response_data, "Login successful.", 200)


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user():
    """Retrieve currently authenticated user profile, preferences, and cart info."""
    user: User = g.current_user
    prefs = [p.category for p in user.preferences.all()]
    cart_items_count = user.cart.items.count() if user.cart else 0

    user_info = user.to_dict()
    user_info["preferred_categories"] = prefs
    user_info["cart_items_count"] = cart_items_count

    return success_response(user_info, "User profile retrieved.", 200)
