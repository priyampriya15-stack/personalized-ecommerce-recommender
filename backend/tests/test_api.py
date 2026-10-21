"""
test_api.py
-----------
Comprehensive integration and unit test suite for Flask REST API:
Database models, Authentication, Products, Recommendations, Interactions, Cart, and Admin.
"""

import pytest
import json
from pathlib import Path

from backend.app import create_app
from backend.models.database_models import db, User, Product, Interaction, UserPreference, UserCart, CartItem, RecommendationLog, Order, OrderItem
from backend.routes.auth_helpers import generate_jwt_token

PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"


@pytest.fixture
def app():
    """Create Flask app with test configuration and fresh in-memory database."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        # Seed sample products for tests
        p1 = Product(
            external_product_id="ASIN001",
            title="Hydrating Face Cream Skincare Lotion",
            category="All Beauty",
            price=24.99,
            rating=4.8,
            image_url="http://example.com/p1.jpg",
            description="Soothing facial cream with natural extracts"
        )
        p2 = Product(
            external_product_id="ASIN002",
            title="Anti-Aging Face Serum Skincare",
            category="All Beauty",
            price=39.99,
            rating=4.9,
            image_url="http://example.com/p2.jpg",
            description="Pure retinol face serum"
        )
        p3 = Product(
            external_product_id="ASIN003",
            title="High Speed Countertop Blender Appliance",
            category="Appliances",
            price=89.99,
            rating=4.5,
            image_url="http://example.com/p3.jpg",
            description="1000W blender for smoothies"
        )
        db.session.add_all([p1, p2, p3])

        # Seed regular user
        user = User(name="Test User", email="test@example.com", role="user")
        user.set_password("Password@123")
        user.cart = UserCart()
        user.preferences = [UserPreference(category="All Beauty", preference_weight=1.5)]
        db.session.add(user)

        # Seed second user
        other_user = User(name="Other User", email="other@example.com", role="user")
        other_user.set_password("Password@123")
        other_user.cart = UserCart()
        db.session.add(other_user)

        # Seed admin user
        admin = User(name="Admin User", email="admin@example.com", role="admin")
        admin.set_password("AdminPass@123")
        admin.cart = UserCart()
        db.session.add(admin)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_token(app):
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        return generate_jwt_token(user.id, user.role), user.id


@pytest.fixture
def admin_token(app):
    with app.app_context():
        admin = User.query.filter_by(email="admin@example.com").first()
        return generate_jwt_token(admin.id, admin.role), admin.id


@pytest.fixture
def auth_headers(user_token):
    token, _ = user_token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_token):
    token, _ = admin_token
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# 1. Database Model Tests
# =========================================================================

def test_user_password_hashing(app):
    with app.app_context():
        u = User(name="Hash Test", email="hash@example.com", role="user")
        u.set_password("Secret123")
        assert u.password_hash != "Secret123"
        assert u.check_password("Secret123") is True
        assert u.check_password("WrongPassword") is False
        assert "password_hash" not in u.to_dict()


def test_unique_external_product_id(app):
    with app.app_context():
        dup = Product(
            external_product_id="ASIN001",  # already exists in fixture
            title="Duplicate Product",
            category="All Beauty",
            price=10.0,
            rating=4.0
        )
        db.session.add(dup)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


# =========================================================================
# 2. Authentication API Tests
# =========================================================================

def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "name": "New User",
        "email": "newuser@example.com",
        "password": "SecurePassword123",
        "categories": ["All Beauty", "Appliances"]
    })
    assert res.status_code == 201
    body = res.get_json()
    assert body["success"] is True
    assert "token" in body["data"]
    assert body["data"]["user"]["email"] == "newuser@example.com"


def test_register_duplicate_email(client):
    res = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",  # already in fixture
        "password": "Password@123"
    })
    assert res.status_code == 409
    body = res.get_json()
    assert body["success"] is False
    assert body["error"]["code"] == "DUPLICATE_EMAIL"


def test_login_success(client):
    res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "Password@123"
    })
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert "token" in body["data"]


def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "IncorrectPassword"
    })
    assert res.status_code == 401
    body = res.get_json()
    assert body["success"] is False


def test_get_me_endpoint(client, user_token):
    token, _ = user_token
    # Unauthorized request without token
    res_unauth = client.get("/api/auth/me")
    assert res_unauth.status_code == 401

    # Authorized request with Bearer token
    res_auth = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_auth.status_code == 200
    body = res_auth.get_json()
    assert body["data"]["email"] == "test@example.com"
    assert "All Beauty" in body["data"]["preferred_categories"]


# =========================================================================
# 3. Product Catalog API Tests
# =========================================================================

def test_list_products_pagination_and_filter(client):
    res = client.get("/api/products?page=1&limit=2")
    assert res.status_code == 200
    body = res.get_json()
    assert len(body["data"]["products"]) == 2
    assert body["data"]["total"] == 3

    # Filter by category
    res_cat = client.get("/api/products?category=Appliances")
    body_cat = res_cat.get_json()
    assert len(body_cat["data"]["products"]) == 1
    assert body_cat["data"]["products"][0]["category"] == "Appliances"

    # Filter by price range
    res_price = client.get("/api/products?min_price=30.0&max_price=50.0")
    body_price = res_price.get_json()
    assert len(body_price["data"]["products"]) == 1
    assert body_price["data"]["products"][0]["external_product_id"] == "ASIN002"


def test_get_single_product_and_404(client):
    # Retrieve by external product ID
    res = client.get("/api/products/ASIN001")
    assert res.status_code == 200
    assert res.get_json()["data"]["external_product_id"] == "ASIN001"

    # Non-existent product
    res_404 = client.get("/api/products/NON_EXISTENT_ID")
    assert res_404.status_code == 404


def test_search_products(client):
    res = client.get("/api/products/search?q=Blender")
    assert res.status_code == 200
    body = res.get_json()
    assert len(body["data"]["products"]) == 1
    assert "Blender" in body["data"]["products"][0]["title"]

    # Empty query parameter
    res_empty = client.get("/api/products/search?q=")
    assert res_empty.status_code == 400


def test_similar_products_api(client):
    res = client.get("/api/products/ASIN001/similar?limit=2")
    assert res.status_code == 200
    body = res.get_json()
    assert "data" in body


# =========================================================================
# 4. Recommendation API Tests
# =========================================================================

def test_popular_recommendations_public(client):
    # Open to guests without authentication
    res = client.get("/api/recommendations/popular?limit=3")
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert len(body["data"]) > 0


def test_hybrid_recommendation_auth_protection(client, user_token):
    token, user_id = user_token

    # Missing token -> 401
    res_no_token = client.get(f"/api/recommendations/{user_id}/hybrid")
    assert res_no_token.status_code == 401

    # Accessing own recommendations -> 200
    res_own = client.get(
        f"/api/recommendations/{user_id}/hybrid",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_own.status_code == 200
    body = res_own.get_json()
    assert body["success"] is True
    assert len(body["data"]) > 0

    # User attempting to access another user's recommendations -> 403 Forbidden
    res_forbidden = client.get(
        "/api/recommendations/9999/hybrid",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_forbidden.status_code == 403


# =========================================================================
# 5. Interaction API Tests
# =========================================================================

def test_record_interaction_valid_and_invalid(client, user_token):
    token, _ = user_token

    # Valid rating interaction
    res_valid = client.post(
        "/api/interactions",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": "ASIN001", "interaction_type": "rating", "rating": 5.0}
    )
    assert res_valid.status_code == 201
    assert res_valid.get_json()["data"]["rating"] == 5.0

    # Invalid rating (> 5.0)
    res_bad_rating = client.post(
        "/api/interactions",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": "ASIN001", "interaction_type": "rating", "rating": 10.0}
    )
    assert res_bad_rating.status_code == 400

    # Invalid interaction type
    res_bad_type = client.post(
        "/api/interactions",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": "ASIN001", "interaction_type": "invalid_event"}
    )
    assert res_bad_type.status_code == 400


def test_get_user_history_and_preferences(client, user_token):
    token, user_id = user_token

    # Record a view
    client.post(
        "/api/interactions",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": "ASIN002", "interaction_type": "view"}
    )

    # Get history
    res_hist = client.get(
        f"/api/users/{user_id}/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_hist.status_code == 200
    history = res_hist.get_json()["data"]
    assert len(history) >= 1

    # Update preferences
    res_pref = client.post(
        "/api/users/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"categories": ["Appliances"]}
    )
    assert res_pref.status_code == 200
    assert res_pref.get_json()["data"][0]["category"] == "Appliances"


# =========================================================================
# 6. Cart and Checkout API Tests
# =========================================================================

def test_cart_workflow(client, user_token):
    token, _ = user_token

    # 1. Add item to cart
    res_add = client.post(
        "/api/cart/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": "ASIN001", "quantity": 2}
    )
    assert res_add.status_code == 201
    cart_data = res_add.get_json()["data"]
    assert cart_data["total_items"] == 2

    # 2. View cart
    res_view = client.get("/api/cart", headers={"Authorization": f"Bearer {token}"})
    assert res_view.status_code == 200
    item_id = res_view.get_json()["data"]["items"][0]["id"]

    # 3. Checkout
    res_checkout = client.post("/api/cart/checkout", headers={"Authorization": f"Bearer {token}"})
    assert res_checkout.status_code == 200
    assert res_checkout.get_json()["data"]["status"] == "completed"

    # Cart should now be empty
    res_empty_cart = client.get("/api/cart", headers={"Authorization": f"Bearer {token}"})
    assert res_empty_cart.get_json()["data"]["total_items"] == 0


# =========================================================================
# 7. Admin API Tests (Phase 7: Admin Dashboard + Analytics)
# =========================================================================

def test_admin_authorization_unauthenticated_and_forbidden(client, user_token, admin_token):
    u_token, _ = user_token
    a_token, _ = admin_token

    # 1. Unauthenticated requests -> 401
    assert client.get("/api/admin/analytics").status_code == 401
    assert client.get("/api/admin/model-metrics").status_code == 401
    assert client.put("/api/admin/recommendation-settings", json={"alpha": 0.5}).status_code == 401

    # 2. Normal authenticated user attempting admin endpoints -> 403 Forbidden
    for ep in ["/api/admin/analytics", "/api/admin/model-metrics"]:
        res_user = client.get(ep, headers={"Authorization": f"Bearer {u_token}"})
        assert res_user.status_code == 403
        assert res_user.get_json()["error"]["code"] == "FORBIDDEN"

    res_put_user = client.put(
        "/api/admin/recommendation-settings",
        headers={"Authorization": f"Bearer {u_token}"},
        json={"alpha": 0.5}
    )
    assert res_put_user.status_code == 403

    # 3. Authenticated admin user accessing endpoints -> 200 OK
    res_admin = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {a_token}"})
    assert res_admin.status_code == 200


def test_admin_analytics_calculations_match_database(client, admin_token, app):
    a_token, _ = admin_token
    res = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {a_token}"})
    assert res.status_code == 200
    data = res.get_json()["data"]

    # Verify exact cross-check with database counts within app context
    with app.app_context():
        real_user_count = User.query.count()
        real_product_count = Product.query.count()
        real_interaction_count = Interaction.query.count()
        real_rec_count = RecommendationLog.query.count()

        assert data["overview"]["total_users"] == real_user_count
        assert data["overview"]["total_products"] == real_product_count
        assert data["overview"]["total_interactions"] == real_interaction_count
        assert data["overview"]["total_recommendation_calls"] == real_rec_count

        # Security check: verify sensitive password hash is never exposed in recent users
        for u in data["users"]["recent"]:
            assert "password_hash" not in u
            assert "password" not in u
            assert "email" in u

        # Verify category stats structure
        assert len(data["categories_detailed"]) >= 1
        for cat in data["categories_detailed"]:
            assert "category" in cat
            assert "product_count" in cat
            assert "interaction_count" in cat
            assert "avg_rating" in cat

        # System status verification
        assert data["system_status"]["database_connected"] is True
        assert data["system_status"]["database_engine"] == "SQLite"
        assert "models_loaded" in data["system_status"]


def test_admin_model_metrics_accuracy(client, admin_token):
    a_token, _ = admin_token
    res = client.get("/api/admin/model-metrics", headers={"Authorization": f"Bearer {a_token}"})
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert "model_comparison" in data
    assert len(data["model_comparison"]) > 0

    # Verify model names present in offline evaluation
    model_names = [m["Model"] for m in data["model_comparison"]]
    assert any("Popularity" in name for name in model_names)
    assert any("Collaborative" in name for name in model_names)
    assert any("Content-Based" in name for name in model_names)
    assert any("Hybrid" in name for name in model_names)

    # Verify best metrics structure at K=10
    assert "best_metrics_k10" in data
    assert "Recall@K" in data["best_metrics_k10"]


def test_admin_hybrid_alpha_boundary_and_persistence(client, admin_token, app):
    a_token, _ = admin_token

    # 1. Valid alpha update
    res = client.put(
        "/api/admin/recommendation-settings",
        headers={"Authorization": f"Bearer {a_token}"},
        json={"alpha": 0.35}
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["data"]["current_hybrid_alpha"] == 0.35
    assert body["data"]["collaborative_weight"] == 0.35
    assert body["data"]["content_weight"] == 0.65

    # 2. Boundary conditions: alpha = 0.0 (Pure Content-Based)
    res_zero = client.put(
        "/api/admin/recommendation-settings",
        headers={"Authorization": f"Bearer {a_token}"},
        json={"alpha": 0.0}
    )
    assert res_zero.status_code == 200
    assert res_zero.get_json()["data"]["current_hybrid_alpha"] == 0.0

    # 3. Boundary conditions: alpha = 1.0 (Pure Collaborative)
    res_one = client.put(
        "/api/admin/recommendation-settings",
        headers={"Authorization": f"Bearer {a_token}"},
        json={"alpha": 1.0}
    )
    assert res_one.status_code == 200
    assert res_one.get_json()["data"]["current_hybrid_alpha"] == 1.0

    # 4. Out of bounds: alpha < 0.0 -> 400
    res_neg = client.put(
        "/api/admin/recommendation-settings",
        headers={"Authorization": f"Bearer {a_token}"},
        json={"alpha": -0.2}
    )
    assert res_neg.status_code == 400
    assert res_neg.get_json()["error"]["code"] == "INVALID_ALPHA"

    # 5. Out of bounds: alpha > 1.0 -> 400
    res_high = client.put(
        "/api/admin/recommendation-settings",
        headers={"Authorization": f"Bearer {a_token}"},
        json={"alpha": 1.25}
    )
    assert res_high.status_code == 400
    assert res_high.get_json()["error"]["code"] == "INVALID_ALPHA"

    # 6. Invalid non-numeric string -> 400
    res_invalid_str = client.put(
        "/api/admin/recommendation-settings",
        headers={"Authorization": f"Bearer {a_token}"},
        json={"alpha": "invalid_number"}
    )
    assert res_invalid_str.status_code == 400

    # 7. Missing parameter -> 400
    res_missing = client.put(
        "/api/admin/recommendation-settings",
        headers={"Authorization": f"Bearer {a_token}"},
        json={}
    )
    assert res_missing.status_code == 400

    # 8. Reset to empirical optimum 0.25
    res_opt = client.put(
        "/api/admin/recommendation-settings",
        headers={"Authorization": f"Bearer {a_token}"},
        json={"alpha": 0.25}
    )
    assert res_opt.status_code == 200
    assert res_opt.get_json()["data"]["current_hybrid_alpha"] == 0.25


# =========================================================================
# 8. Phase 6 Specific Tests: Preferences, Security, Exclusion & Cold-Start
# =========================================================================

def test_preference_validation_and_invalid_category_rejection(client, user_token):
    token, _ = user_token

    # 1. Valid category with tiered weights
    res_valid = client.post(
        "/api/users/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"categories": ["All Beauty", "Appliances"]}
    )
    assert res_valid.status_code == 200
    prefs = res_valid.get_json()["data"]
    assert len(prefs) == 2
    assert prefs[0]["preference_weight"] == 2.0  # Primary tier
    assert prefs[1]["preference_weight"] == 1.5  # Secondary tier

    # 2. Invalid category rejection
    res_invalid = client.post(
        "/api/users/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"categories": ["Space Rocket Engines"]}
    )
    assert res_invalid.status_code == 400
    assert res_invalid.get_json()["error"]["code"] == "INVALID_CATEGORY"

    # 3. Empty preference list clears preferences
    res_empty = client.post(
        "/api/users/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"categories": []}
    )
    assert res_empty.status_code == 200
    assert len(res_empty.get_json()["data"]) == 0

    # 4. Registration with invalid category rejection
    res_reg_invalid = client.post(
        "/api/auth/register",
        json={
            "name": "Invalid Reg",
            "email": "invalid.cat@example.com",
            "password": "Password123!",
            "categories": ["Mythical Category XYZ"]
        }
    )
    assert res_reg_invalid.status_code == 400
    assert res_reg_invalid.get_json()["error"]["code"] == "INVALID_CATEGORY"


def test_security_user_cross_access_forbidden(client, user_token, app):
    token, user1_id = user_token

    with app.app_context():
        user2 = User.query.filter_by(email="other@example.com").first()
        user2_id = user2.id

    # User 1 attempting to view User 2's private history -> 403 Forbidden
    res_cross_history = client.get(
        f"/api/users/{user2_id}/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_cross_history.status_code == 403

    # User 1 attempting to view User 2's personalized recommendations -> 403 Forbidden
    res_cross_recs = client.get(
        f"/api/recommendations/{user2_id}/hybrid",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_cross_recs.status_code == 403

    # User 1 accessing own history via 'me' alias -> 200 OK
    res_me_history = client.get(
        "/api/users/me/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_me_history.status_code == 200

    # User 1 accessing own recommendations via 'me' alias -> 200 OK
    res_me_recs = client.get(
        "/api/recommendations/me/hybrid",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_me_recs.status_code == 200


def test_previously_interacted_product_exclusion_in_recommendations(client, user_token, app):
    token, user_id = user_token

    # User records rating for ASIN001
    client.post(
        "/api/interactions",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": "ASIN001", "interaction_type": "rating", "rating": 5.0}
    )

    # Request recommendations for user
    res = client.get(
        f"/api/recommendations/{user_id}/hybrid?limit=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    rec_products = [r["product_id"] for r in res.get_json()["data"]]

    # ASIN001 should be excluded from candidate list
    assert "ASIN001" not in rec_products


def test_cold_start_new_user_with_onboarding_preferences(client, app):
    # Register a new cold user with 0 interactions but preferred category
    new_email = "cold.user.test@example.com"
    res_reg = client.post(
        "/api/auth/register",
        json={
            "name": "Cold User",
            "email": new_email,
            "password": "ColdPassword123!",
            "categories": ["All Beauty"]
        }
    )
    assert res_reg.status_code == 201
    reg_data = res_reg.get_json()["data"]
    token = reg_data["token"]
    user_id = reg_data["user"]["id"]

    # Verify user exists in database with 0 interactions
    with app.app_context():
        u = db.session.get(User, user_id)
        assert u is not None
        assert u.interactions.count() == 0
        assert u.preferences.count() == 1
        assert u.preferences.first().category == "All Beauty"

    # Request recommendations for cold user -> uses preferences and fallback gracefully
    res_recs = client.get(
        f"/api/recommendations/{user_id}/content-based?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_recs.status_code == 200
    recs = res_recs.get_json()["data"]
    assert len(recs) > 0


def test_order_quote_cart_and_buy_now(client, app, auth_headers):
    # Test Buy Now quote
    res_bn = client.post(
        "/api/orders/quote",
        headers=auth_headers,
        json={"product_id": 1, "quantity": 2}
    )
    assert res_bn.status_code == 200
    data_bn = res_bn.get_json()["data"]
    assert data_bn["items_count"] == 2
    assert data_bn["total_amount"] == 49.98  # 24.99 * 2

    # Add item to cart and test cart quote
    client.post("/api/cart/items", headers=auth_headers, json={"product_id": 2, "quantity": 1})
    res_cart = client.post("/api/orders/quote", headers=auth_headers, json={"source": "cart"})
    assert res_cart.status_code == 200
    data_cart = res_cart.get_json()["data"]
    assert data_cart["items_count"] == 1
    assert data_cart["total_amount"] == 39.99


def test_create_order_buy_now_server_price_calculation(client, app, auth_headers):
    # Send client payload with attempted spoofed price (should be completely ignored by backend)
    res = client.post(
        "/api/orders",
        headers=auth_headers,
        json={"product_id": 1, "quantity": 3, "total_amount": 0.01}  # Attempted cheat
    )
    assert res.status_code == 201
    order = res.get_json()["data"]
    assert order["status"] == "PENDING"
    # Expected: 24.99 * 3 = 74.97
    assert order["total_amount"] == 74.97
    assert order["items_count"] == 3
    assert len(order["items"]) == 1
    assert order["items"][0]["unit_price"] == 24.99
    assert order["items"][0]["subtotal"] == 74.97


def test_create_order_from_cart_and_cart_clearing(client, app, auth_headers):
    # Add 2 products to cart
    client.post("/api/cart/items", headers=auth_headers, json={"product_id": 1, "quantity": 1})
    client.post("/api/cart/items", headers=auth_headers, json={"product_id": 2, "quantity": 2})

    # Checkout cart
    res = client.post("/api/orders", headers=auth_headers, json={"source": "cart"})
    assert res.status_code == 201
    order = res.get_json()["data"]
    assert order["status"] == "PENDING"
    # Expected: 24.99 + (39.99 * 2) = 104.97
    assert order["total_amount"] == 104.97

    # Verify cart is now empty
    res_cart = client.get("/api/cart", headers=auth_headers)
    assert res_cart.status_code == 200
    assert len(res_cart.get_json()["data"]["items"]) == 0


def test_get_orders_user_isolation(client, app, auth_headers, admin_headers):
    # Regular user creates an order
    res_create = client.post("/api/orders", headers=auth_headers, json={"product_id": 1, "quantity": 1})
    order_id = res_create.get_json()["data"]["id"]

    # Register a second user (User B)
    res_user_b = client.post(
        "/api/auth/register",
        json={"name": "User B", "email": "userb@example.com", "password": "Password123!"}
    )
    token_b = res_user_b.get_json()["data"]["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B lists orders -> should be empty (User B cannot see User A's order)
    res_b_orders = client.get("/api/orders", headers=headers_b)
    assert res_b_orders.status_code == 200
    assert len(res_b_orders.get_json()["data"]) == 0

    # User B attempts to access User A's order by ID -> 403 Forbidden
    res_b_view = client.get(f"/api/orders/{order_id}", headers=headers_b)
    assert res_b_view.status_code == 403

    # User B attempts to cancel User A's order -> 403 Forbidden
    res_b_cancel = client.post(f"/api/orders/{order_id}/cancel", headers=headers_b)
    assert res_b_cancel.status_code == 403


def test_cancel_order_workflow_and_validation(client, app, auth_headers):
    # Create order
    res = client.post("/api/orders", headers=auth_headers, json={"product_id": 2, "quantity": 1})
    order_id = res.get_json()["data"]["id"]

    # Cancel order
    res_cancel = client.post(f"/api/orders/{order_id}/cancel", headers=auth_headers)
    assert res_cancel.status_code == 200
    cancelled_order = res_cancel.get_json()["data"]
    assert cancelled_order["status"] == "CANCELLED"

    # Attempt to cancel again -> 400 Bad Request (cannot cancel already CANCELLED order)
    res_cancel_again = client.post(f"/api/orders/{order_id}/cancel", headers=auth_headers)
    assert res_cancel_again.status_code == 400

    # Test invalid product ID or negative quantity
    res_invalid_prod = client.post("/api/orders", headers=auth_headers, json={"product_id": 99999, "quantity": 1})
    assert res_invalid_prod.status_code == 404

    res_negative_qty = client.post("/api/orders", headers=auth_headers, json={"product_id": 1, "quantity": -5})
    assert res_negative_qty.status_code == 400


def test_buy_now_dedicated_endpoint_and_reject_cancel_completed_order(client, app, auth_headers):
    # 1. Dedicated Buy Now endpoint: POST /api/orders/buy-now
    res_bn = client.post(
        "/api/orders/buy-now",
        headers=auth_headers,
        json={"product_id": 1, "quantity": 2}
    )
    assert res_bn.status_code == 201
    order = res_bn.get_json()["data"]
    assert order["status"] == "PENDING"
    assert order["total_amount"] == 49.98
    assert order["items_count"] == 2
    order_id = order["id"]

    # 2. Transition order to COMPLETED in database to test cancellation guard
    with app.app_context():
        ord_db = db.session.get(Order, order_id)
        ord_db.status = "COMPLETED"
        db.session.commit()

    # 3. Attempting to cancel a COMPLETED order must be rejected with 400
    res_cancel_completed = client.post(f"/api/orders/{order_id}/cancel", headers=auth_headers)
    assert res_cancel_completed.status_code == 400
    assert res_cancel_completed.get_json()["error"]["code"] == "INVALID_ORDER_STATUS"



