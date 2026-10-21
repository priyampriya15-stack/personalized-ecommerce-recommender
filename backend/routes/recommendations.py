"""
recommendations.py
------------------
Recommendation endpoints: Popularity, Collaborative Filtering,
Content-Based, and Hybrid Recommendations.
"""

from flask import Blueprint, request, current_app, g
from typing import List, Optional

from backend.models.database_models import db, User, Product, Interaction, RecommendationLog
from backend.models.schemas import success_response, error_response
from backend.routes.auth_helpers import jwt_required, optional_jwt

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")


def verify_user_access(requested_user_id: str) -> Optional[User]:
    """Verify that current authenticated user has rights to access requested_user_id."""
    if not hasattr(g, "current_user") or not g.current_user:
        return None

    current_user: User = g.current_user
    is_self = str(requested_user_id).lower() == "me" or str(current_user.id) == str(requested_user_id)

    # Admins can view any user; standard users can only view their own
    if is_self:
        return current_user

    if current_user.role == "admin":
        if str(requested_user_id).isdigit():
            return db.session.get(User, int(requested_user_id))
        return User.query.filter_by(email=requested_user_id).first()

    return None


def get_user_signals(user: User):
    """Extract category preferences and recent interaction history for a user."""
    preferred_categories = [p.category for p in user.preferences.all()]

    # Extract interaction history with weights
    type_weights = {"view": 0.5, "cart": 1.5, "like": 2.0, "rating": 2.0, "purchase": 3.0}
    interactions = user.interactions.order_by(Interaction.timestamp.desc()).limit(50).all()

    user_history = []
    for inter in interactions:
        if inter.product and inter.product.external_product_id:
            w = float(inter.rating) if inter.rating is not None else type_weights.get(inter.interaction_type, 1.0)
            user_history.append((inter.product.external_product_id, w))

    return preferred_categories, user_history


def log_recommendations(user_id: int, rec_items: list):
    """Asynchronously record recommendation events into recommendation_logs table."""
    try:
        for r in rec_items:
            ext_id = r.get("product_id")
            prod = Product.query.filter_by(external_product_id=ext_id).first()
            prod_id = prod.id if prod else 0
            if prod_id > 0:
                log = RecommendationLog(
                    user_id=user_id,
                    product_id=prod_id,
                    algorithm=r.get("algorithm", "hybrid"),
                    recommendation_score=float(r.get("score", 0.0))
                )
                db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


@recommendations_bp.route("/popular", methods=["GET"])
def get_popular_recommendations():
    """Get non-personalized popularity baseline recommendations (open to all)."""
    limit = min(request.args.get("limit", 10, type=int), 30)
    category = request.args.get("category", type=str)

    pop_model = current_app.recommendation_services.get("popularity")
    if not pop_model:
        return error_response("Recommendation service unavailable.", "SERVICE_UNAVAILABLE", 503)

    recs = pop_model.recommend(top_n=limit, category=category)
    results = [r.to_dict() for r in recs]
    return success_response(results, "Popular recommendations retrieved.", 200)


@recommendations_bp.route("/<user_id>", methods=["GET"])
@recommendations_bp.route("/<user_id>/hybrid", methods=["GET"])
@jwt_required
def get_hybrid_recommendations(user_id: str):
    """Get personalized hybrid recommendations for the authenticated user."""
    target_user = verify_user_access(user_id)
    if not target_user:
        return error_response("Access denied: You can only view your own recommendations.", "FORBIDDEN", 403)

    limit = min(request.args.get("limit", 10, type=int), 30)
    alpha = request.args.get("alpha", type=float)

    hybrid_engine = current_app.recommendation_services.get("hybrid")
    if not hybrid_engine:
        return error_response("Recommendation service unavailable.", "SERVICE_UNAVAILABLE", 503)

    preferred_categories, user_history = get_user_signals(target_user)

    recs = hybrid_engine.recommend(
        user_id=str(target_user.email),  # Map user email or id
        preferred_categories=preferred_categories,
        user_history=user_history,
        top_n=limit,
        alpha=alpha,
        exclude_interacted=True
    )

    results = [r.to_dict() for r in recs]
    log_recommendations(target_user.id, results)
    return success_response(results, "Personalized hybrid recommendations retrieved.", 200)


@recommendations_bp.route("/<user_id>/collaborative", methods=["GET"])
@jwt_required
def get_collaborative_recommendations(user_id: str):
    """Get pure collaborative filtering recommendations for the authenticated user."""
    target_user = verify_user_access(user_id)
    if not target_user:
        return error_response("Access denied: You can only view your own recommendations.", "FORBIDDEN", 403)

    limit = min(request.args.get("limit", 10, type=int), 30)
    cf_model = current_app.recommendation_services.get("collaborative")
    pop_model = current_app.recommendation_services.get("popularity")

    if not cf_model or not pop_model:
        return error_response("Recommendation service unavailable.", "SERVICE_UNAVAILABLE", 503)

    # Use user email to check SVD latent factor matrix
    recs = cf_model.recommend(str(target_user.email), top_n=limit, exclude_interacted=True)
    if not recs:
        # Graceful cold-start fallback
        recs = pop_model.recommend(top_n=limit)

    results = [r.to_dict() for r in recs]
    log_recommendations(target_user.id, results)
    return success_response(results, "Collaborative recommendations retrieved.", 200)


@recommendations_bp.route("/<user_id>/content-based", methods=["GET"])
@jwt_required
def get_content_based_recommendations(user_id: str):
    """Get pure content-based recommendations based on user preferences and history."""
    target_user = verify_user_access(user_id)
    if not target_user:
        return error_response("Access denied: You can only view your own recommendations.", "FORBIDDEN", 403)

    limit = min(request.args.get("limit", 10, type=int), 30)
    cb_model = current_app.recommendation_services.get("content_based")
    pop_model = current_app.recommendation_services.get("popularity")

    if not cb_model or not pop_model:
        return error_response("Recommendation service unavailable.", "SERVICE_UNAVAILABLE", 503)

    preferred_categories, user_history = get_user_signals(target_user)

    recs = cb_model.recommend_for_user_profile(
        interacted_items=user_history,
        preferred_categories=preferred_categories,
        top_n=limit,
        exclude_interacted=True
    )
    if not recs:
        recs = pop_model.recommend(top_n=limit)

    results = [r.to_dict() for r in recs]
    log_recommendations(target_user.id, results)
    return success_response(results, "Content-based recommendations retrieved.", 200)
