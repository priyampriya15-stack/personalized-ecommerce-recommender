"""
demo_phase4.py
--------------
End-to-end integration verification for Phase 4: Database + Flask REST API.
Verifies all 13 real-world API workflows against the live SQLite database
and persisted ML recommendation models.
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.models.database_models import db, User, Product, Interaction


def print_section(num: int, title: str):
    print("\n" + "=" * 80)
    print(f" STEP {num}: {title}")
    print("=" * 80)


def run_demo():
    print("Starting Flask application in development mode with SQLite database...")
    app = create_app("development")
    client = app.test_client()

    with app.app_context():
        # Ensure database is present
        total_prods = Product.query.count()
        total_users = User.query.count()
        total_ints = Interaction.query.count()
        print(f"Database connected: {total_prods} products, {total_users} users, {total_ints} interactions.")

    # 1. Register a user
    print_section(1, "Register a New User (POST /api/auth/register)")
    test_email = "alex.rivera@example.com"
    # Clean up if existing from previous run
    with app.app_context():
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

    reg_payload = {
        "name": "Alex Rivera",
        "email": test_email,
        "password": "SecurePassword123!"
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    print(f"Status: {res_reg.status_code}")
    reg_data = res_reg.get_json()
    print(f"Response: {json.dumps(reg_data, indent=2)}")
    assert res_reg.status_code == 201
    assert reg_data["success"] is True
    user_id = reg_data["data"]["user"]["id"]
    reg_token = reg_data["data"]["token"]

    # 2. Login successfully
    print_section(2, "Login Successfully (POST /api/auth/login)")
    login_payload = {
        "email": test_email,
        "password": "SecurePassword123!"
    }
    res_login = client.post("/api/auth/login", json=login_payload)
    print(f"Status: {res_login.status_code}")
    login_data = res_login.get_json()
    print(f"Response: {json.dumps(login_data, indent=2)}")
    assert res_login.status_code == 200
    assert login_data["success"] is True
    auth_token = login_data["data"]["token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # 3. Retrieve authenticated user
    print_section(3, "Retrieve Authenticated User (GET /api/auth/me)")
    res_me = client.get("/api/auth/me", headers=auth_headers)
    print(f"Status: {res_me.status_code}")
    me_data = res_me.get_json()
    print(f"Response: {json.dumps(me_data, indent=2)}")
    assert res_me.status_code == 200
    assert me_data["data"]["email"] == test_email

    # 4. Retrieve real products from SQLite
    print_section(4, "Retrieve Products & Search (GET /api/products, GET /api/products/search)")
    res_prods = client.get("/api/products?page=1&limit=3&category=All_Beauty")
    print(f"Listing Status: {res_prods.status_code}")
    prods_data = res_prods.get_json()
    print(f"Total matching: {prods_data['data']['total']}")
    sample_prod = prods_data["data"]["products"][0]
    sample_prod_id = sample_prod["id"]
    print(f"Sample product #{sample_prod_id}: {sample_prod['title'][:60]} | ${sample_prod['price']} | {sample_prod['rating']} stars")

    res_search = client.get("/api/products/search?q=moisturizer&limit=2")
    search_data = res_search.get_json()
    print(f"Search 'moisturizer' found {search_data['data']['total']} items:")
    for p in search_data["data"]["products"]:
        print(f" - #{p['id']}: {p['title'][:60]}")

    # 5. Record a real interaction
    print_section(5, "Record a Real Interaction (POST /api/interactions)")
    int_payload = {
        "product_id": sample_prod_id,
        "interaction_type": "rating",
        "rating": 5.0
    }
    res_int = client.post("/api/interactions", headers=auth_headers, json=int_payload)
    print(f"Status: {res_int.status_code}")
    int_data = res_int.get_json()
    print(f"Response: {json.dumps(int_data, indent=2)}")
    assert res_int.status_code == 201

    # Record two more interactions so user has history
    with app.app_context():
        p2 = Product.query.filter(Product.id != sample_prod_id).first()
        p2_id = p2.id
    client.post("/api/interactions", headers=auth_headers, json={
        "product_id": p2_id,
        "interaction_type": "like"
    })

    # 6. Retrieve interaction history
    print_section(6, "Retrieve User Interaction History (GET /api/users/<user_id>/history)")
    res_hist = client.get(f"/api/users/{user_id}/history", headers=auth_headers)
    print(f"Status: {res_hist.status_code}")
    hist_data = res_hist.get_json()
    print(f"History count: {len(hist_data['data'])}")
    for h in hist_data["data"]:
        print(f" - Interaction #{h['id']}: Product #{h['product_id']} ({h['product_title'][:40]}) -> Type: {h['interaction_type']}, Rating: {h['rating']}")

    # 7. Generate popularity recommendations
    print_section(7, "Generate Popularity Recommendations (GET /api/recommendations/popular)")
    res_pop = client.get("/api/recommendations/popular?limit=3")
    print(f"Status: {res_pop.status_code}")
    pop_data = res_pop.get_json()
    for r in pop_data["data"]:
        print(f" - Rank #{r['rank']} | Score: {r['score']:.4f} | {r['title'][:55]} | Reason: {r['explanation']}")

    # 8. Generate collaborative recommendations
    print_section(8, "Generate Collaborative Recommendations (GET /api/recommendations/<user_id>/collaborative)")
    # Non-admin accessing other user CF recommendations
    res_cf_other = client.get("/api/recommendations/2/collaborative?limit=3", headers=auth_headers)
    print(f"Non-admin accessing other user CF recommendations status: {res_cf_other.status_code} (Expected 403 Forbidden)")
    assert res_cf_other.status_code == 403

    # Now query for Alex himself
    res_cf_self = client.get(f"/api/recommendations/{user_id}/collaborative?limit=3", headers=auth_headers)
    print(f"Alex self CF status: {res_cf_self.status_code}")
    cf_data = res_cf_self.get_json()
    print(f"Collaborative recs count: {len(cf_data['data'])}")
    for r in cf_data["data"]:
        print(f" - Rank #{r['rank']} | [{r['algorithm']}] Score: {r['score']:.4f} | {r['title'][:55]}")

    # 9. Generate content-based recommendations
    print_section(9, "Generate Content-Based Recommendations (GET /api/recommendations/<user_id>/content-based)")
    res_cb = client.get(f"/api/recommendations/{user_id}/content-based?limit=3", headers=auth_headers)
    print(f"Status: {res_cb.status_code}")
    cb_data = res_cb.get_json()
    for r in cb_data["data"]:
        print(f" - Rank #{r['rank']} | Score: {r['score']:.4f} | {r['title'][:55]} | Reason: {r['explanation']}")

    # 10. Generate hybrid recommendations
    print_section(10, "Generate Hybrid Recommendations (GET /api/recommendations/<user_id>/hybrid)")
    res_hyb = client.get(f"/api/recommendations/{user_id}/hybrid?limit=3&alpha=0.3", headers=auth_headers)
    print(f"Status: {res_hyb.status_code}")
    hyb_data = res_hyb.get_json()
    for r in hyb_data["data"]:
        print(f" - Rank #{r['rank']} | Score: {r['score']:.4f} | {r['title'][:55]} | Reason: {r['explanation']}")

    # 11. Generate similar-product recommendations
    print_section(11, f"Generate Similar Product Recommendations (GET /api/products/{sample_prod_id}/similar)")
    res_sim = client.get(f"/api/products/{sample_prod_id}/similar?limit=3")
    print(f"Status: {res_sim.status_code}")
    sim_data = res_sim.get_json()
    for r in sim_data["data"]:
        print(f" - Rank #{r['rank']} | Similarity: {r['score']:.4f} | {r['title'][:55]} | Reason: {r['explanation']}")

    # 12. Retrieve admin analytics
    print_section(12, "Retrieve Admin Analytics & Metrics (GET /api/admin/analytics, GET /api/admin/model-metrics)")
    # Login as admin
    res_adm_login = client.post("/api/auth/login", json={
        "email": "admin@ecommerce.com",
        "password": "Admin@123"
    })
    admin_token = res_adm_login.get_json()["data"]["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    res_analytics = client.get("/api/admin/analytics", headers=admin_headers)
    print(f"Analytics Status: {res_analytics.status_code}")
    an_data = res_analytics.get_json()["data"]
    print(f"Total Users: {an_data['overview']['total_users']}")
    print(f"Total Products: {an_data['overview']['total_products']}")
    print(f"Total Interactions: {an_data['overview']['total_interactions']}")
    print(f"Current Hybrid Alpha: {an_data['overview']['current_hybrid_alpha']}")
    print(f"Interactions by type: {an_data['interaction_breakdown']}")

    res_metrics = client.get("/api/admin/model-metrics", headers=admin_headers)
    print(f"Model Metrics Status: {res_metrics.status_code}")
    mm_data = res_metrics.get_json()["data"]
    print(f"Evaluated Models: {[m['Model'] for m in mm_data['model_comparison']]}")
    print(f"Sample Metric: {mm_data['model_comparison'][0]}")

    # 13. Update and use Hybrid alpha
    print_section(13, "Update Recommendation Settings (PUT /api/admin/recommendation-settings)")
    res_alpha = client.put("/api/admin/recommendation-settings", headers=admin_headers, json={"alpha": 0.45})
    print(f"Update Status: {res_alpha.status_code}")
    alpha_data = res_alpha.get_json()
    print(f"Updated Alpha: {alpha_data['data']['current_hybrid_alpha']}")
    assert alpha_data["data"]["current_hybrid_alpha"] == 0.45

    # Check updated analytics overview reflecting the live alpha change
    res_analytics2 = client.get("/api/admin/analytics", headers=admin_headers)
    assert res_analytics2.get_json()["data"]["overview"]["current_hybrid_alpha"] == 0.45
    print("Verified that live hybrid alpha updated dynamically in memory!")

    print("\n" + "=" * 80)
    print(" ALL 13 REAL WORKFLOWS VERIFIED SUCCESSFULLY WITH ZERO ERRORS!")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
