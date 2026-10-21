"""
admin.py
--------
Admin dashboard routes: platform analytics, offline model evaluation metrics,
and dynamic hybrid recommender parameter adjustment.
Uses real SQLite database records, model artifacts, and evaluation reports only.
"""

from pathlib import Path
import os
from flask import Blueprint, request, current_app
from sqlalchemy import func
import pandas as pd

from backend.models.database_models import db, User, Product, Interaction, RecommendationLog, Order, OrderItem
from backend.models.schemas import success_response, error_response
from backend.routes.auth_helpers import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/analytics", methods=["GET"])
@admin_required
def get_analytics():
    """Retrieve comprehensive platform analytics calculated directly from SQLite."""
    # 1. User Analytics
    total_users = User.query.count()
    user_roles = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role = {role: count for role, count in user_roles}

    # Active users: distinct users with at least 1 interaction
    active_users_count = db.session.query(func.count(func.distinct(Interaction.user_id))).scalar() or 0

    # Recent registered users (without exposing passwords)
    recent_users = [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else None
        }
        for u in User.query.order_by(User.created_at.desc()).limit(10).all()
    ]

    # 2. Product Analytics
    total_products = Product.query.count()
    catalog_avg_rating = db.session.query(func.avg(Product.rating)).scalar() or 0.0
    interacted_products_count = db.session.query(func.count(func.distinct(Interaction.product_id))).scalar() or 0

    # Top interacted products
    top_products_query = db.session.query(
        Product.id,
        Product.title,
        Product.category,
        Product.rating,
        Product.price,
        func.count(Interaction.id).label("interaction_count")
    ).join(Interaction, Product.id == Interaction.product_id)\
     .group_by(Product.id)\
     .order_by(func.count(Interaction.id).desc())\
     .limit(10)\
     .all()

    top_interacted_products = [
        {
            "id": p.id,
            "title": p.title,
            "category": p.category,
            "rating": round(float(p.rating), 2) if p.rating is not None else 0.0,
            "price": round(float(p.price), 2) if p.price is not None else 0.0,
            "interaction_count": p.interaction_count
        }
        for p in top_products_query
    ]

    # 3. Category Analytics
    cat_stats_query = db.session.query(
        Product.category,
        func.count(func.distinct(Product.id)).label("product_count"),
        func.count(Interaction.id).label("interaction_count"),
        func.avg(Product.rating).label("avg_rating")
    ).outerjoin(Interaction, Product.id == Interaction.product_id)\
     .group_by(Product.category)\
     .all()

    category_statistics = {c.category: c.product_count for c in cat_stats_query}
    categories_detailed = [
        {
            "category": c.category,
            "product_count": c.product_count,
            "interaction_count": c.interaction_count,
            "avg_rating": round(float(c.avg_rating), 2) if c.avg_rating is not None else 0.0
        }
        for c in cat_stats_query
    ]

    # 4. Interaction Analytics
    total_interactions = Interaction.query.count()
    type_counts = db.session.query(
        Interaction.interaction_type, func.count(Interaction.id)
    ).group_by(Interaction.interaction_type).all()
    interaction_breakdown = {t: count for t, count in type_counts}

    # Timeline of interactions (grouped by date)
    timeline_query = db.session.query(
        func.substr(Interaction.timestamp, 1, 10).label("date"),
        func.count(Interaction.id).label("count")
    ).group_by(func.substr(Interaction.timestamp, 1, 10))\
     .order_by(func.substr(Interaction.timestamp, 1, 10).asc())\
     .all()

    interactions_timeline = [
        {"date": str(t.date), "count": t.count}
        for t in timeline_query if t.date
    ]

    # Recent interactions with joined product and user details
    recent_interactions_query = db.session.query(
        Interaction.id,
        Interaction.user_id,
        User.email.label("user_email"),
        Interaction.product_id,
        Product.title.label("product_title"),
        Product.category.label("product_category"),
        Interaction.interaction_type,
        Interaction.rating,
        Interaction.timestamp
    ).outerjoin(User, Interaction.user_id == User.id)\
     .outerjoin(Product, Interaction.product_id == Product.id)\
     .order_by(Interaction.timestamp.desc())\
     .limit(15)\
     .all()

    recent_interactions = [
        {
            "id": i.id,
            "user_id": i.user_id,
            "user_email": i.user_email or f"User #{i.user_id}",
            "product_id": i.product_id,
            "product_title": i.product_title or f"Product #{i.product_id}",
            "category": i.product_category or "Uncategorized",
            "interaction_type": i.interaction_type,
            "rating": i.rating,
            "timestamp": i.timestamp.strftime("%Y-%m-%d %H:%M:%S") if i.timestamp else None
        }
        for i in recent_interactions_query
    ]

    # 5. Recommendation Analytics
    total_rec_logs = RecommendationLog.query.count()
    algo_counts = db.session.query(
        RecommendationLog.algorithm, func.count(RecommendationLog.id)
    ).group_by(RecommendationLog.algorithm).all()
    algorithm_usage = {a: count for a, count in algo_counts}

    # Recent recommendation logs with joined details
    recent_logs_query = db.session.query(
        RecommendationLog.id,
        RecommendationLog.user_id,
        User.email.label("user_email"),
        RecommendationLog.product_id,
        Product.title.label("product_title"),
        RecommendationLog.algorithm,
        RecommendationLog.recommendation_score,
        RecommendationLog.created_at
    ).outerjoin(User, RecommendationLog.user_id == User.id)\
     .outerjoin(Product, RecommendationLog.product_id == Product.id)\
     .order_by(RecommendationLog.created_at.desc())\
     .limit(15)\
     .all()

    recent_recommendation_logs = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_email": r.user_email or f"User #{r.user_id}",
            "product_id": r.product_id,
            "product_title": r.product_title or f"Product #{r.product_id}",
            "algorithm": r.algorithm,
            "score": round(float(r.recommendation_score), 4) if r.recommendation_score is not None else 0.0,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None
        }
        for r in recent_logs_query
    ]

    # 6. Current Hybrid Alpha & System Status
    hybrid_engine = current_app.recommendation_services.get("hybrid")
    current_alpha = hybrid_engine.get_alpha() if hybrid_engine else 0.25

    db_path = Path(__file__).resolve().parent.parent.parent / "data" / "ecommerce.db"
    db_size = os.path.getsize(db_path) if db_path.exists() else 0

    models_loaded = {
        "popularity": bool(current_app.recommendation_services.get("popularity")),
        "collaborative": bool(current_app.recommendation_services.get("collaborative")),
        "content_based": bool(current_app.recommendation_services.get("content_based")),
        "hybrid": bool(current_app.recommendation_services.get("hybrid")),
    }

    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status="PENDING").count()
    confirmed_orders = Order.query.filter_by(status="CONFIRMED").count()
    completed_orders = Order.query.filter_by(status="COMPLETED").count()
    cancelled_orders = Order.query.filter_by(status="CANCELLED").count()
    total_order_val = db.session.query(func.coalesce(func.sum(Order.total_amount), 0.0)).filter(Order.status != "CANCELLED").scalar() or 0.0

    analytics_data = {
        "overview": {
            "total_users": total_users,
            "active_users": active_users_count,
            "total_products": total_products,
            "total_interactions": total_interactions,
            "total_recommendation_calls": total_rec_logs,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "total_order_value": round(float(total_order_val), 2),
            "catalog_avg_rating": round(catalog_avg_rating, 2),
            "interacted_products_count": interacted_products_count,
            "current_hybrid_alpha": current_alpha
        },
        "orders": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "total_order_value": round(float(total_order_val), 2)
        },
        "users": {
            "total": total_users,
            "by_role": users_by_role,
            "active_count": active_users_count,
            "recent": recent_users
        },
        "products": {
            "total": total_products,
            "by_category": category_statistics,
            "avg_rating": round(catalog_avg_rating, 2),
            "interacted_count": interacted_products_count,
            "top_interacted": top_interacted_products
        },
        "categories_detailed": categories_detailed,
        "category_statistics": category_statistics,
        "interaction_breakdown": interaction_breakdown,
        "interactions_timeline": interactions_timeline,
        "recent_interactions": recent_interactions,
        "algorithm_usage": algorithm_usage,
        "recent_recommendation_logs": recent_recommendation_logs,
        "system_status": {
            "database_connected": True,
            "database_engine": "SQLite",
            "database_size_bytes": db_size,
            "models_loaded": models_loaded,
            "current_hybrid_alpha": current_alpha
        }
    }

    return success_response(analytics_data, "Platform analytics retrieved.", 200)


@admin_bp.route("/model-metrics", methods=["GET"])
@admin_required
def get_model_metrics():
    """Return offline evaluation results from reports/model_comparison.csv and reports/hybrid_alpha_experiments.csv."""
    reports_dir = current_app.config.get("REPORTS_DIR") or Path(__file__).resolve().parent.parent.parent / "reports"
    csv_path = reports_dir / "model_comparison.csv"
    alpha_csv_path = reports_dir / "hybrid_alpha_experiments.csv"

    if not csv_path.exists():
        return error_response("Offline evaluation metrics not found. Run evaluation script first.", "METRICS_NOT_FOUND", 404)

    df_models = pd.read_csv(csv_path)
    model_comparison = df_models.to_dict(orient="records")

    alpha_experiments = []
    if alpha_csv_path.exists():
        df_alphas = pd.read_csv(alpha_csv_path)
        alpha_experiments = df_alphas.to_dict(orient="records")

    # Grouped comparisons for K=5 and K=10
    k5_models = [m for m in model_comparison if m.get("K") == 5]
    k10_models = [m for m in model_comparison if m.get("K") == 10]

    # Best-performing models strictly by measured metric at K=10
    best_metrics = {}
    if k10_models:
        for metric in ["Precision@K", "Recall@K", "NDCG@K", "MAP@K", "Coverage@K (%)", "Diversity@K"]:
            best_entry = max(k10_models, key=lambda m: float(m.get(metric, 0) or 0))
            best_metrics[metric] = {
                "model": best_entry.get("Model"),
                "value": best_entry.get(metric)
            }

    return success_response({
        "model_comparison": model_comparison,
        "k5_models": k5_models,
        "k10_models": k10_models,
        "alpha_experiments": alpha_experiments,
        "best_metrics_k10": best_metrics
    }, "Model metrics retrieved.", 200)


@admin_bp.route("/recommendation-settings", methods=["PUT"])
@admin_required
def update_recommendation_settings():
    """Dynamically update hybrid recommender alpha parameter (collaborative vs content weight)."""
    data = request.get_json(silent=True) or {}
    new_alpha = data.get("alpha")

    if new_alpha is None:
        return error_response("Parameter 'alpha' is required.", "MISSING_ALPHA", 400)

    try:
        alpha_val = float(new_alpha)
        if alpha_val < 0.0 or alpha_val > 1.0:
            return error_response("Parameter 'alpha' must be between 0.0 and 1.0 inclusive.", "INVALID_ALPHA", 400)
    except (ValueError, TypeError):
        return error_response("Parameter 'alpha' must be a valid float.", "INVALID_ALPHA", 400)

    hybrid_engine = current_app.recommendation_services.get("hybrid")
    if not hybrid_engine:
        return error_response("Hybrid recommendation service unavailable.", "SERVICE_UNAVAILABLE", 503)

    hybrid_engine.set_alpha(alpha_val)

    return success_response({
        "current_hybrid_alpha": hybrid_engine.get_alpha(),
        "collaborative_weight": round(alpha_val, 2),
        "content_weight": round(1.0 - alpha_val, 2)
    }, f"Hybrid alpha successfully updated to {alpha_val:.2f}.", 200)

