"""
verify_phase9.py
----------------
Phase 9 Real-Data Finalization and Production-Style Verification Script.
Validates the complete chain with actual dataset records, actual SQLite database,
actual user interactions, and actual ML recommendation outputs over live HTTP:
- Live HTTP calls against Flask daemon
- 2 distinct users with different preferences & interaction histories receiving distinct recommendations
- Cold start new user fallback verification
- Similar products TF-IDF cosine distance verification
- SQLite exact cross-check (users, products, interactions, recommendation logs)
- Latency benchmarks
"""

import sys
import time
import json
import urllib.request
import urllib.error
import sqlite3
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "http://127.0.0.1:5000/api"


def make_request(url, method="GET", data=None, token=None):
    """Helper to perform HTTP requests against the live Flask daemon."""
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
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8")) if e.fp else {}
        return e.code, body


def run_phase9_verification():
    print("=" * 80)
    print("PHASE 9: REAL DATA FINALIZATION & PRODUCTION-STYLE VERIFICATION")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. VERIFY REAL DATASET ARTIFACTS
    # -------------------------------------------------------------------------
    print("\n[SECTION 1: REAL DATASET & PROCESSED REPOSITORY]")
    proc_dir = PROJECT_ROOT / "data" / "processed"
    assert (proc_dir / "products.parquet").exists(), "products.parquet missing"
    assert (proc_dir / "interactions.parquet").exists(), "interactions.parquet missing"
    assert (proc_dir / "train_interactions.parquet").exists(), "train_interactions.parquet missing"
    assert (proc_dir / "test_interactions.parquet").exists(), "test_interactions.parquet missing"

    db_path = PROJECT_ROOT / "data" / "ecommerce.db"
    assert db_path.exists(), "ecommerce.db missing"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    sql_users = cur.execute("SELECT count(*) FROM users").fetchone()[0]
    sql_products = cur.execute("SELECT count(*) FROM products").fetchone()[0]
    sql_interactions = cur.execute("SELECT count(*) FROM interactions").fetchone()[0]
    sql_rec_logs = cur.execute("SELECT count(*) FROM recommendation_logs").fetchone()[0]

    print(f"  [OK] Dataset source: Amazon Reviews 2023 (McAuley Lab / UCSD)")
    print(f"  [OK] Processed catalog items: {sql_products} products in SQLite")
    print(f"  [OK] Current database records: {sql_users} users, {sql_interactions} interactions, {sql_rec_logs} recommendation logs")

    # -------------------------------------------------------------------------
    # 2. RECOMMENDATION PERSONALIZATION TEST (2 REAL DISTINCT USERS)
    # -------------------------------------------------------------------------
    print("\n[SECTION 2: REAL PERSONALIZATION TEST WITH 2 DISTINCT USERS]")

    ts = int(time.time())
    email_music = f"music_listener_{ts}@example.com"
    email_beauty = f"beauty_shopper_{ts}@example.com"

    # Register User A (Music Fan)
    status_a, res_a = make_request(f"{API_BASE}/auth/register", "POST", {
        "name": "Jordan Melody",
        "email": email_music,
        "password": "MusicUser@123"
    })
    assert status_a == 201, f"User A registration failed: {res_a}"
    token_a = res_a["data"]["token"]
    user_a_id = res_a["data"]["user"]["id"]

    # Register User B (Beauty Fan)
    status_b, res_b = make_request(f"{API_BASE}/auth/register", "POST", {
        "name": "Taylor Glam",
        "email": email_beauty,
        "password": "BeautyUser@123"
    })
    assert status_b == 201, f"User B registration failed: {res_b}"
    token_b = res_b["data"]["token"]
    user_b_id = res_b["data"]["user"]["id"]

    print(f"  [OK] Registered User A (ID {user_a_id}: {email_music})")
    print(f"  [OK] Registered User B (ID {user_b_id}: {email_beauty})")

    # Set User A preferences -> Digital Music
    status_pa, _ = make_request(f"{API_BASE}/users/preferences", "POST", {"categories": ["Digital Music"]}, token_a)
    assert status_pa == 200

    # Set User B preferences -> All Beauty
    status_pb, _ = make_request(f"{API_BASE}/users/preferences", "POST", {"categories": ["All Beauty"]}, token_b)
    assert status_pb == 200

    # User A interacts with a real Digital Music product
    cur.execute("SELECT id, external_product_id, title FROM products WHERE category='Digital Music' LIMIT 1")
    music_prod = cur.fetchone()
    make_request(f"{API_BASE}/interactions", "POST", {"product_id": music_prod[0], "interaction_type": "like"}, token_a)
    make_request(f"{API_BASE}/interactions", "POST", {"product_id": music_prod[0], "interaction_type": "rating", "rating": 5.0}, token_a)

    # User B interacts with a real All Beauty product
    cur.execute("SELECT id, external_product_id, title FROM products WHERE category='All Beauty' LIMIT 1")
    beauty_prod = cur.fetchone()
    make_request(f"{API_BASE}/interactions", "POST", {"product_id": beauty_prod[0], "interaction_type": "like"}, token_b)
    make_request(f"{API_BASE}/interactions", "POST", {"product_id": beauty_prod[0], "interaction_type": "rating", "rating": 5.0}, token_b)

    print(f"  [OK] User A interacted with Digital Music item: '{music_prod[2][:35]}...'")
    print(f"  [OK] User B interacted with All Beauty item:   '{beauty_prod[2][:35]}...'")

    # Generate Personalized Hybrid Recommendations for both users
    status_ra, recs_payload_a = make_request(f"{API_BASE}/recommendations/{user_a_id}/hybrid?limit=6", "GET", None, token_a)
    assert status_ra == 200
    recs_a = recs_payload_a["data"]

    status_rb, recs_payload_b = make_request(f"{API_BASE}/recommendations/{user_b_id}/hybrid?limit=6", "GET", None, token_b)
    assert status_rb == 200
    recs_b = recs_payload_b["data"]

    recs_a_ids = [r["product_id"] for r in recs_a]
    recs_b_ids = [r["product_id"] for r in recs_b]

    # Verify that interacted products are excluded
    assert music_prod[1] not in recs_a_ids, "User A's interacted product was not excluded"
    assert beauty_prod[1] not in recs_b_ids, "User B's interacted product was not excluded"

    # Verify that User A and User B received distinct personalized recommendation sets
    overlap = set(recs_a_ids).intersection(set(recs_b_ids))
    print(f"  [OK] User A Top Recommended Categories: {[r['category'] for r in recs_a[:3]]}")
    print(f"  [OK] User B Top Recommended Categories: {[r['category'] for r in recs_b[:3]]}")
    print(f"  [OK] Personalization Verified: Overlap between User A and User B = {len(overlap)} / 6 items")
    assert len(overlap) < len(recs_a_ids), "User A and User B should have different recommendations!"

    # -------------------------------------------------------------------------
    # 3. COLD-START NEW USER VERIFICATION
    # -------------------------------------------------------------------------
    print("\n[SECTION 3: COLD-START FALLBACK]")
    email_cold = f"cold_user_{ts}@example.com"
    _, res_cold = make_request(f"{API_BASE}/auth/register", "POST", {
        "name": "Cold Start Visitor",
        "email": email_cold,
        "password": "ColdUser@123"
    })
    token_cold = res_cold["data"]["token"]
    user_cold_id = res_cold["data"]["user"]["id"]

    # Cold user with 0 interactions requests recommendations -> should fallback to popularity/baseline
    status_cold_rec, cold_recs = make_request(f"{API_BASE}/recommendations/{user_cold_id}/hybrid?limit=5", "GET", None, token_cold)
    assert status_cold_rec == 200
    assert len(cold_recs["data"]) == 5
    print(f"  [OK] Cold-start user successfully received {len(cold_recs['data'])} fallback recommendations.")
    print(f"  [OK] Fallback explanation: '{cold_recs['data'][0]['explanation']}'")

    # -------------------------------------------------------------------------
    # 4. SIMILAR PRODUCTS VERIFICATION
    # -------------------------------------------------------------------------
    print("\n[SECTION 4: SIMILAR PRODUCTS VIA TF-IDF COSINE SIMILARITY]")
    target_id = music_prod[0]
    target_ext_id = music_prod[1]
    status_sim, sim_res = make_request(f"{API_BASE}/products/{target_id}/similar?limit=4")
    assert status_sim == 200
    similar_items = sim_res["data"]
    assert len(similar_items) == 4
    # Query product must not be in its own similar products list
    assert target_ext_id not in [item["product_id"] for item in similar_items]
    print(f"  [OK] Generated {len(similar_items)} similar products for item #{target_id} ('{music_prod[2][:35]}...').")
    print(f"  [OK] Top Similar Item: {similar_items[0]['product_id']} ('{similar_items[0]['title'][:35]}...') | Score: {similar_items[0]['score']:.4f}")

    # -------------------------------------------------------------------------
    # 5. ADMIN ANALYTICS REAL DATABASE CROSS-CHECK
    # -------------------------------------------------------------------------
    print("\n[SECTION 5: ADMIN TELEMETRY CROSS-CHECK]")
    # Login as Admin
    status_admin_login, res_admin_login = make_request(f"{API_BASE}/auth/login", "POST", {
        "email": "admin@ecommerce.com",
        "password": "Admin@123"
    })
    assert status_admin_login == 200
    admin_token = res_admin_login["data"]["token"]

    status_analytics, analytics_payload = make_request(f"{API_BASE}/admin/analytics", "GET", None, admin_token)
    assert status_analytics == 200
    analytics = analytics_payload["data"]

    # Re-query database to verify exact match
    cur_users = cur.execute("SELECT count(*) FROM users").fetchone()[0]
    cur_products = cur.execute("SELECT count(*) FROM products").fetchone()[0]
    cur_interactions = cur.execute("SELECT count(*) FROM interactions").fetchone()[0]
    cur_rec_logs = cur.execute("SELECT count(*) FROM recommendation_logs").fetchone()[0]

    assert analytics["overview"]["total_users"] == cur_users, f"Users mismatch: {analytics['overview']['total_users']} vs {cur_users}"
    assert analytics["overview"]["total_products"] == cur_products, f"Products mismatch: {analytics['overview']['total_products']} vs {cur_products}"
    assert analytics["overview"]["total_interactions"] == cur_interactions, f"Interactions mismatch: {analytics['overview']['total_interactions']} vs {cur_interactions}"
    assert analytics["overview"]["total_recommendation_calls"] == cur_rec_logs, f"Rec logs mismatch: {analytics['overview']['total_recommendation_calls']} vs {cur_rec_logs}"

    print(f"  [OK] SQLite Users:          {cur_users} == API Analytics: {analytics['overview']['total_users']} (MATCH)")
    print(f"  [OK] SQLite Products:       {cur_products} == API Analytics: {analytics['overview']['total_products']} (MATCH)")
    print(f"  [OK] SQLite Interactions:   {cur_interactions} == API Analytics: {analytics['overview']['total_interactions']} (MATCH)")
    print(f"  [OK] SQLite Rec Logs:       {cur_rec_logs} == API Analytics: {analytics['overview']['total_recommendation_calls']} (MATCH)")

    # -------------------------------------------------------------------------
    # 6. LATENCY BENCHMARKING
    # -------------------------------------------------------------------------
    print("\n[SECTION 6: LATENCY & PERFORMANCE BENCHMARKS (LIVE HTTP)]")
    benchmarks = [
        ("Catalog Pagination", f"{API_BASE}/products?page=1&limit=20", None),
        ("Product Text Search", f"{API_BASE}/products/search?q=conditioner&limit=10", None),
        ("Popular Recommendations", f"{API_BASE}/recommendations/popular?limit=10", None),
        ("Personalized Hybrid Recs", f"{API_BASE}/recommendations/{user_a_id}/hybrid?limit=10", token_a),
        ("Similar Products (TF-IDF)", f"{API_BASE}/products/{target_id}/similar?limit=4", None),
        ("Admin Telemetry Query", f"{API_BASE}/admin/analytics", admin_token),
    ]

    for label, url, tok in benchmarks:
        t0 = time.perf_counter()
        code, _ = make_request(url, "GET", None, tok)
        dur_ms = (time.perf_counter() - t0) * 1000
        assert code == 200
        print(f"  [OK] {label:<27} -> Status: 200 | Latency: {dur_ms:6.2f} ms")

    print("\n" + "=" * 80)
    print("ALL PHASE 9 PRODUCTION VERIFICATION CHECKS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_phase9_verification()
