import sqlite3
from pathlib import Path

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def audit_database():
    db_path = Path("data/ecommerce.db")
    print(f"Database path: {db_path.resolve()}")
    print(f"Database size: {db_path.stat().st_size} bytes ({db_path.stat().st_size / (1024*1024):.2f} MB)")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall() if not row[0].startswith("sqlite_")]
    print("\nDATABASE TABLES AND ROW COUNTS:")
    for t in tables:
        cnt = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {cnt}")

    print("\nSAMPLE PRODUCTS FROM DATABASE:")
    for row in cur.execute("SELECT id, external_product_id, title, category, price, rating FROM products LIMIT 3").fetchall():
        print(f"  ID {row[0]}: [{row[3]}] '{row[2][:40]}' (${row[4]}, rating={row[5]}) ASIN={row[1]}")

    print("\nSAMPLE USERS FROM DATABASE:")
    for row in cur.execute("SELECT id, name, email, role, created_at FROM users LIMIT 5").fetchall():
        print(f"  ID {row[0]}: {row[1]} ({row[2]}) [role={row[3]}] created={row[4]}")

    print("\nFOREIGN KEY CHECK:")
    fk_errors = cur.execute("PRAGMA foreign_key_check").fetchall()
    print(f"  FK errors: {len(fk_errors)}")

if __name__ == "__main__":
    audit_database()
