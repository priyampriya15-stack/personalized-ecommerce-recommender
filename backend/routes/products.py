"""
products.py
-----------
Product catalog endpoints: listing, filtering, search, details, and similar items.
"""

from flask import Blueprint, request, current_app
from sqlalchemy import or_

from backend.models.database_models import db, Product
from backend.models.schemas import success_response, error_response

products_bp = Blueprint("products", __name__, url_prefix="/api/products")


def get_product_by_id_or_external(product_identifier: str) -> Product:
    """Find product by integer ID or external Amazon ASIN string."""
    identifier_str = str(product_identifier).strip()
    product = None
    if identifier_str.isdigit():
        product = db.session.get(Product, int(identifier_str))
    if not product:
        product = Product.query.filter_by(external_product_id=identifier_str).first()
    return product


@products_bp.route("", methods=["GET"])
def list_products():
    """
    List products with pagination, category filter, price filter, rating filter, and sorting.
    """
    page = request.args.get("page", 1, type=int)
    limit = min(request.args.get("limit", 20, type=int), 100)
    category = request.args.get("category", type=str)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    min_rating = request.args.get("min_rating", type=float)
    sort_by = request.args.get("sort", "rating_desc", type=str)

    query = Product.query

    # Filters
    if category:
        query = query.filter(Product.category.ilike(category.strip()))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort_by == "rating_asc":
        query = query.order_by(Product.rating.asc())
    elif sort_by == "title_asc":
        query = query.order_by(Product.title.asc())
    else:  # default: rating_desc
        query = query.order_by(Product.rating.desc(), Product.id.asc())

    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    products = [p.to_dict() for p in pagination.items]

    return success_response({
        "products": products,
        "total": pagination.total,
        "page": pagination.page,
        "total_pages": pagination.pages,
        "limit": limit
    }, "Products retrieved.", 200)


@products_bp.route("/categories", methods=["GET"])
def list_categories():
    """Return distinct categories available in the product catalog with item counts."""
    from sqlalchemy import func
    results = Product.query.with_entities(
        Product.category, func.count(Product.id)
    ).group_by(Product.category).all()

    categories = [{"name": cat, "count": count} for cat, count in results]
    return success_response(categories, "Categories retrieved.", 200)


@products_bp.route("/search", methods=["GET"])
def search_products():
    """Search products by keyword in title, description, or category."""
    query_str = request.args.get("q", "", type=str).strip()
    page = request.args.get("page", 1, type=int)
    limit = min(request.args.get("limit", 20, type=int), 100)
    category = request.args.get("category", type=str)

    if not query_str:
        return error_response("Search query 'q' parameter is required.", "MISSING_QUERY", 400)

    pattern = f"%{query_str}%"
    query = Product.query.filter(
        or_(
            Product.title.ilike(pattern),
            Product.description.ilike(pattern),
            Product.category.ilike(pattern)
        )
    )

    if category:
        query = query.filter(Product.category.ilike(category.strip()))

    pagination = query.order_by(Product.rating.desc()).paginate(page=page, per_page=limit, error_out=False)
    products = [p.to_dict() for p in pagination.items]

    return success_response({
        "query": query_str,
        "products": products,
        "total": pagination.total,
        "page": pagination.page,
        "total_pages": pagination.pages,
        "limit": limit
    }, f"Found {pagination.total} products.", 200)


@products_bp.route("/<product_identifier>", methods=["GET"])
def get_product_details(product_identifier: str):
    """Get single product details by integer database ID or external ASIN."""
    product = get_product_by_id_or_external(product_identifier)
    if not product:
        return error_response(f"Product '{product_identifier}' not found.", "NOT_FOUND", 404)

    return success_response(product.to_dict(), "Product retrieved.", 200)


@products_bp.route("/<product_identifier>/similar", methods=["GET"])
def get_similar_products(product_identifier: str):
    """Get content-based similar products using TF-IDF cosine similarity."""
    product = get_product_by_id_or_external(product_identifier)
    if not product:
        return error_response(f"Product '{product_identifier}' not found.", "NOT_FOUND", 404)

    limit = min(request.args.get("limit", 6, type=int), 20)

    # Use Content-Based service from current app
    cb_model = current_app.recommendation_services.get("content_based")
    if not cb_model:
        return error_response("Recommendation service unavailable.", "SERVICE_UNAVAILABLE", 503)

    similar_recs = cb_model.recommend_similar_to_product(product.external_product_id, top_n=limit)
    if not similar_recs:
        # Fallback to products in same category
        fallback_products = Product.query.filter(
            Product.category == product.category,
            Product.id != product.id
        ).order_by(Product.rating.desc()).limit(limit).all()
        return success_response([p.to_dict() for p in fallback_products], "Similar products retrieved (category fallback).", 200)

    results = [r.to_dict() for r in similar_recs]
    return success_response(results, "Similar products retrieved.", 200)
