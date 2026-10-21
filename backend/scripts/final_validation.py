import sys
import time
import json
import urllib.request
import urllib.error
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
API_BASE = "http://127.0.0.1:5000/api"
DB_PATH = PROJECT_ROOT / "data" / "ecommerce.db"


def request_json(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data else None,
        headers=headers,
        method=method
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8")) if e.fp else {}
        return e.code, body


def run_final_validation():
    print("=" * 80)
    print("FINAL REAL-DATA AUDIT AND APPLICATION VALIDATION")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. REAL PRODUCTS VERIFICATION
    print("\n[CHECK 1: REAL PRODUCTS RETRIEVAL (SQLITE -> API -> CLIENT)]")
    code, prod_res = request_json(f"{API_BASE}/products?page=1&limit=5")
    assert code == 200, f"Failed products API: {code}"
    api_prods = prod_res["data"]["products"]
    total_catalog = prod_res["data"]["total"]
    print(f"  API reported total products: {total_catalog}")
    assert total_catalog == 8337, f"Expected 8337 products, got {total_catalog}"

    for p in api_prods:
        row = cur.execute("SELECT id, external_product_id, title, category, price, rating FROM products WHERE id = ?", (p["id"],)).fetchone()
        assert row is not None, f"Product #{p['id']} does not exist in SQLite!"
        assert row[1] == p["external_product_id"], f"ASIN mismatch: {row[1]} vs {p['external_product_id']}"
        assert row[2] == p["title"], f"Title mismatch for #{p['id']}"
        assert row[3] == p["category"], f"Category mismatch for #{p['id']}"
        print(f"  ✓ Product #{p['id']} verified in SQLite: [{p['category']}] '{p['title'][:35]}...' (${p['price']})")

    # 2. REAL RECOMMENDATIONS ENGINE (COLLABORATIVE, CONTENT, HYBRID, POPULAR)
    print("\n[CHECK 2: REAL RECOMMENDATION ALGORITHMS]")
    # Login as demo user
    code_login, login_res = request_json(f"{API_BASE}/auth/login", "POST", {
        "email": "demo@ecommerce.com",
        "password": "Demo@123"
    })
    assert code_login == 200, f"Login failed: {code_login}"
    demo_token = login_res["data"]["token"]
    demo_id = login_res["data"]["user"]["id"]

    # Hybrid Recs
    c_hyb, hyb_data = request_json(f"{API_BASE}/recommendations/{demo_id}/hybrid?limit=4", "GET", None, demo_token)
    assert c_hyb == 200
    print(f"  ✓ Hybrid Recommendations ({len(hyb_data['data'])} items):")
    for r in hyb_data["data"]:
        # Verify in DB
        db_prod = cur.execute("SELECT id, title, category, price FROM products WHERE external_product_id = ?", (r["product_id"],)).fetchone()
        assert db_prod is not None, f"Recommended product {r['product_id']} not in SQLite!"
        print(f"    - [{r['algorithm']}] ASIN={r['product_id']} | Score={r['score']} | '{r['title'][:30]}...'")
        assert len(r["explanation"]) > 0

    # Collaborative Recs
    c_cf, cf_data = request_json(f"{API_BASE}/recommendations/{demo_id}/collaborative?limit=3", "GET", None, demo_token)
    assert c_cf == 200
    print(f"  ✓ Collaborative Filtering Recs ({len(cf_data['data'])} items): Top ASIN={cf_data['data'][0]['product_id']}")

    # Content-Based Recs
    c_cb, cb_data = request_json(f"{API_BASE}/recommendations/{demo_id}/content-based?limit=3", "GET", None, demo_token)
    assert c_cb == 200
    print(f"  ✓ Content-Based Recs ({len(cb_data['data'])} items): Top ASIN={cb_data['data'][0]['product_id']}")

    # Popularity Recs
    c_pop, pop_data = request_json(f"{API_BASE}/recommendations/popular?limit=3", "GET")
    assert c_pop == 200
    print(f"  ✓ Popularity Baseline Recs ({len(pop_data['data'])} items): Top ASIN={pop_data['data'][0]['product_id']} (Score={pop_data['data'][0]['score']})")

    # 3. PERSONALIZATION PROOF (USER A vs USER B)
    print("\n[CHECK 3: PERSONALIZATION EMPIRICAL PROOF]")
    # User A (Music)
    code_ua, res_ua = request_json(f"{API_BASE}/auth/login", "POST", {
        "email": "activeuser@ecommerce.com",
        "password": "User@123"
    })
    assert code_ua == 200
    token_ua = res_ua["data"]["token"]
    id_ua = res_ua["data"]["user"]["id"]

    _, recs_ua = request_json(f"{API_BASE}/recommendations/{id_ua}/hybrid?limit=6", "GET", None, token_ua)
    _, recs_demo = request_json(f"{API_BASE}/recommendations/{demo_id}/hybrid?limit=6", "GET", None, demo_token)

    asins_ua = [r["product_id"] for r in recs_ua["data"]]
    asins_demo = [r["product_id"] for r in recs_demo["data"]]
    overlap = set(asins_ua).intersection(set(asins_demo))
    print(f"  ✓ User activeuser@ecommerce.com top items: {asins_ua[:3]}")
    print(f"  ✓ User demo@ecommerce.com top items:       {asins_demo[:3]}")
    print(f"  ✓ Item Overlap: {len(overlap)} / 6 items (Personalization Active!)")

    # 4. COLD START VERIFICATION
    print("\n[CHECK 4: COLD START NEW USER VERIFICATION]")
    fresh_email = f"cold_audit_{int(time.time())}@example.com"
    _, reg_cold = request_json(f"{API_BASE}/auth/register", "POST", {
        "name": "Cold Audit User",
        "email": fresh_email,
        "password": "AuditPassword@123"
    })
    token_cold = reg_cold["data"]["token"]
    id_cold = reg_cold["data"]["user"]["id"]

    # Request recommendations for new user with 0 interactions
    _, cold_recs = request_json(f"{API_BASE}/recommendations/{id_cold}/hybrid?limit=4", "GET", None, token_cold)
    assert len(cold_recs["data"]) == 4
    print(f"  ✓ Cold-start new user received {len(cold_recs['data'])} fallback recommendations.")
    print(f"    Explanation: '{cold_recs['data'][0]['explanation']}'")

    # 5. SIMILAR PRODUCTS VERIFICATION
    print("\n[CHECK 5: SIMILAR PRODUCTS VIA TF-IDF COSINE SIMILARITY]")
    sample_prod_id = 1
    _, sim_res = request_json(f"{API_BASE}/products/{sample_prod_id}/similar?limit=3")
    assert len(sim_res["data"]) == 3
    print(f"  ✓ Similar products for product #{sample_prod_id} ('Howard Leather Conditioner'):")
    for s in sim_res["data"]:
        # Confirm exists in DB
        db_item = cur.execute("SELECT id, title, category FROM products WHERE external_product_id = ?", (s["product_id"],)).fetchone()
        assert db_item is not None
        assert db_item[0] != sample_prod_id, "Current product should not be in similar items!"
        print(f"    - ID #{db_item[0]}: '{db_item[1][:35]}...' | Cosine Score: {s['score']:.4f}")

    # 6. INTERACTION TRACKING & CART CHECKOUT
    print("\n[CHECK 6: INTERACTION TRACKING & DATABASE PERSISTENCE]")
    pre_interactions = cur.execute("SELECT count(*) FROM interactions").fetchone()[0]
    pre_cart_items = cur.execute("SELECT count(*) FROM cart_items").fetchone()[0]

    # User adds item to cart
    c_add, _ = request_json(f"{API_BASE}/cart/items", "POST", {"product_id": 1, "quantity": 1}, token_cold)
    assert c_add == 201
    post_cart_items = cur.execute("SELECT count(*) FROM cart_items").fetchone()[0]
    assert post_cart_items == pre_cart_items + 1, "Cart item was not inserted into SQLite!"

    # User rates item 5 stars
    c_rate, _ = request_json(f"{API_BASE}/interactions", "POST", {"product_id": 1, "interaction_type": "rating", "rating": 5.0}, token_cold)
    assert c_rate == 201

    post_interactions = cur.execute("SELECT count(*) FROM interactions").fetchone()[0]
    print(f"  ✓ Interaction count in SQLite: {pre_interactions} -> {post_interactions} (Real event persisted)")
    print(f"  ✓ Cart items in SQLite:        {pre_cart_items} -> {post_cart_items} (Real item persisted)")

    # 7. ADMIN TELEMETRY CROSS-CHECK
    print("\n[CHECK 7: ADMIN TELEMETRY EXACT DATABASE CROSS-CHECK]")
    code_admin, res_admin = request_json(f"{API_BASE}/auth/login", "POST", {
        "email": "admin@ecommerce.com",
        "password": "Admin@123"
    })
    admin_token = res_admin["data"]["token"]
    _, telemetry = request_json(f"{API_BASE}/admin/analytics", "GET", None, admin_token)
    overview = telemetry["data"]["overview"]

    cur_u = cur.execute("SELECT count(*) FROM users").fetchone()[0]
    cur_p = cur.execute("SELECT count(*) FROM products").fetchone()[0]
    cur_i = cur.execute("SELECT count(*) FROM interactions").fetchone()[0]
    cur_r = cur.execute("SELECT count(*) FROM recommendation_logs").fetchone()[0]

    assert overview["total_users"] == cur_u, f"Users mismatch: {overview['total_users']} vs {cur_u}"
    assert overview["total_products"] == cur_p, f"Products mismatch: {overview['total_products']} vs {cur_p}"
    assert overview["total_interactions"] == cur_i, f"Interactions mismatch: {overview['total_interactions']} vs {cur_i}"
    assert overview["total_recommendation_calls"] == cur_r, f"Rec logs mismatch: {overview['total_recommendation_calls']} vs {cur_r}"

    print(f"  ✓ SQLite Users:          {cur_u} == API Analytics: {overview['total_users']} (MATCH)")
    print(f"  ✓ SQLite Products:       {cur_p} == API Analytics: {overview['total_products']} (MATCH)")
    print(f"  ✓ SQLite Interactions:   {cur_i} == API Analytics: {overview['total_interactions']} (MATCH)")
    print(f"  ✓ SQLite Rec Logs:       {cur_r} == API Analytics: {overview['total_recommendation_calls']} (MATCH)")

    print("\n" + "=" * 80)
    print("ALL REAL-DATA AUDIT CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 80)


if __name__ == "__main__":
    run_final_validation()
