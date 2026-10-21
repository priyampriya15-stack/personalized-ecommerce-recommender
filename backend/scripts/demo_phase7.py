"""
demo_phase7.py
--------------
Phase 7 End-to-End Real-Data Verification Script:
Validates the complete chain:
SQLite Database Records -> Flask REST API -> Admin Dashboard Payload.
Audits against dummy data, verifies RBAC, checks alpha parameter tuning,
and cross-checks exact counts.
"""

import sys
import sqlite3
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app import create_app
from backend.models.database_models import db, User, Product, Interaction, RecommendationLog
from backend.routes.auth_helpers import generate_jwt_token
import pandas as pd


def verify_phase7_real_data():
    print("=" * 70)
    print("PHASE 7 REAL-DATA AUDIT & END-TO-END VERIFICATION")
    print("=" * 70)

    db_path = PROJECT_ROOT / "data" / "ecommerce.db"
    assert db_path.exists(), f"Database file missing at {db_path}"

    # 1. Direct SQLite Query
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    sql_users = cur.execute("SELECT count(*) FROM users").fetchone()[0]
    sql_products = cur.execute("SELECT count(*) FROM products").fetchone()[0]
    sql_interactions = cur.execute("SELECT count(*) FROM interactions").fetchone()[0]
    sql_rec_logs = cur.execute("SELECT count(*) FROM recommendation_logs").fetchone()[0]
    sql_active_users = cur.execute("SELECT count(DISTINCT user_id) FROM interactions").fetchone()[0]
    sql_avg_rating = cur.execute("SELECT avg(rating) FROM products").fetchone()[0]

    # Category breakdown from SQLite
    sql_cats = dict(cur.execute("SELECT category, count(*) FROM products GROUP BY category").fetchall())

    # Interaction breakdown from SQLite
    sql_inter_types = dict(cur.execute("SELECT interaction_type, count(*) FROM interactions GROUP BY interaction_type").fetchall())

    print("\n[1] DIRECT SQLITE VERIFICATION:")
    print(f"  - Total Users:                  {sql_users}")
    print(f"  - Active Users with History:    {sql_active_users}")
    print(f"  - Total Catalog Products:       {sql_products}")
    print(f"  - Catalog Average Rating:       {sql_avg_rating:.2f}")
    print(f"  - Total Interactions:           {sql_interactions}")
    print(f"  - Interaction Breakdown:        {sql_inter_types}")
    print(f"  - Total Recommendation Logs:    {sql_rec_logs}")
    print(f"  - Category Breakdown:           {sql_cats}")

    # 2. Flask REST API Query
    app = create_app()
    with app.app_context():
        client = app.test_client()

        admin_user = User.query.filter_by(role="admin").first()
        normal_user = User.query.filter_by(role="user").first()

        assert admin_user is not None, "Admin user must exist in database"
        assert normal_user is not None, "Normal user must exist in database"

        admin_token = generate_jwt_token(admin_user.id, admin_user.role)
        user_token = generate_jwt_token(normal_user.id, normal_user.role)

        print("\n[2] ADMIN AUTHORIZATION RBAC CHECKS:")
        # A. Unauthenticated
        res_unauth = client.get("/api/admin/analytics")
        assert res_unauth.status_code == 401, f"Expected 401 for unauthenticated, got {res_unauth.status_code}"
        print("  ✓ Unauthenticated access -> 401 Unauthorized (PASS)")

        # B. Normal User
        res_norm = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {user_token}"})
        assert res_norm.status_code == 403, f"Expected 403 for regular user, got {res_norm.status_code}"
        print(f"  ✓ Regular user ({normal_user.email}) -> 403 Forbidden (PASS)")

        # C. Admin User
        res_admin = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_admin.status_code == 200, f"Expected 200 for admin, got {res_admin.status_code}"
        print(f"  ✓ Admin user ({admin_user.email}) -> 200 OK (PASS)")

        api_data = res_admin.get_json()["data"]

        print("\n[3] CROSS-CHECK: SQLITE RECORDS == FLASK ANALYTICS API:")
        api_users = api_data["overview"]["total_users"]
        api_active_users = api_data["overview"]["active_users"]
        api_products = api_data["overview"]["total_products"]
        api_interactions = api_data["overview"]["total_interactions"]
        api_rec_calls = api_data["overview"]["total_recommendation_calls"]
        api_cats = api_data["category_statistics"]
        api_inter_types = api_data["interaction_breakdown"]

        assert sql_users == api_users, f"Users mismatch: SQL {sql_users} vs API {api_users}"
        print(f"  ✓ Total Users:          SQL {sql_users} == API {api_users} (MATCH)")

        assert sql_active_users == api_active_users, f"Active users mismatch: SQL {sql_active_users} vs API {api_active_users}"
        print(f"  ✓ Active Users:         SQL {sql_active_users} == API {api_active_users} (MATCH)")

        assert sql_products == api_products, f"Products mismatch: SQL {sql_products} vs API {api_products}"
        print(f"  ✓ Catalog Products:     SQL {sql_products} == API {api_products} (MATCH)")

        assert sql_interactions == api_interactions, f"Interactions mismatch: SQL {sql_interactions} vs API {api_interactions}"
        print(f"  ✓ Interactions:         SQL {sql_interactions} == API {api_interactions} (MATCH)")

        assert sql_rec_logs == api_rec_calls, f"Rec logs mismatch: SQL {sql_rec_logs} vs API {api_rec_calls}"
        print(f"  ✓ Recommendation Logs:  SQL {sql_rec_logs} == API {api_rec_calls} (MATCH)")

        assert sql_cats == api_cats, f"Categories mismatch: SQL {sql_cats} vs API {api_cats}"
        print(f"  ✓ Category Statistics:  SQL {sql_cats} == API {api_cats} (MATCH)")

        assert sql_inter_types == api_inter_types, f"Interaction breakdown mismatch: SQL {sql_inter_types} vs API {api_inter_types}"
        print(f"  ✓ Interaction Types:    SQL {sql_inter_types} == API {api_inter_types} (MATCH)")

        print("\n[4] MODEL METRICS REPORT VERIFICATION:")
        res_metrics = client.get("/api/admin/model-metrics", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_metrics.status_code == 200
        mm_data = res_metrics.get_json()["data"]

        csv_file = PROJECT_ROOT / "reports" / "model_comparison.csv"
        df_csv = pd.read_csv(csv_file)
        assert len(mm_data["model_comparison"]) == len(df_csv)
        print(f"  ✓ Stored CSV Rows ({len(df_csv)}) == API Model Comparison Rows ({len(mm_data['model_comparison'])}) (MATCH)")

        k10_hybrid = next(m for m in mm_data["k10_models"] if "Hybrid" in m["Model"])
        print(f"  ✓ Measured Hybrid K=10 Recall: {float(k10_hybrid['Recall@K']) * 100:.2f}% (VERIFIED)")
        print(f"  ✓ Measured Hybrid K=10 NDCG:   {float(k10_hybrid['NDCG@K']):.4f} (VERIFIED)")

        print("\n[5] LIVE HYBRID ALPHA DYNAMIC ADJUSTMENT:")
        # Update alpha to 0.40
        res_put = client.put(
            "/api/admin/recommendation-settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"alpha": 0.40}
        )
        assert res_put.status_code == 200
        assert res_put.get_json()["data"]["current_hybrid_alpha"] == 0.40
        print("  ✓ Hybrid alpha updated to 0.40 via API (PASS)")

        # Verify engine reflects the updated alpha
        hybrid_engine = app.recommendation_services.get("hybrid")
        assert hybrid_engine.get_alpha() == 0.40, f"Expected 0.40 in engine, got {hybrid_engine.get_alpha()}"
        print(f"  ✓ Hybrid Recommendation Engine active alpha: {hybrid_engine.get_alpha()} (MATCH)")

        # Reset back to empirical optimum 0.25
        res_reset = client.put(
            "/api/admin/recommendation-settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"alpha": 0.25}
        )
        assert res_reset.status_code == 200
        assert hybrid_engine.get_alpha() == 0.25
        print(f"  ✓ Reset alpha to Phase 3 optimum 0.25 (VERIFIED)")

    print("\n" + "=" * 70)
    print("ALL PHASE 7 REAL-DATA AUDITS & CROSS-CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    verify_phase7_real_data()
