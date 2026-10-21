"""
import_products.py
------------------
Initializes SQLite database tables and imports the processed real Amazon product
catalog from data/processed/products.parquet into the database.
Creates initial seed users (Admin, Demo User, and Active User with historical interactions).

Safe to run repeatedly (idempotent, prevents duplicate products and users).
"""

import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.models.database_models import db, User, Product, UserPreference, Interaction, UserCart

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("import_products")

DATA_DIR = BASE_DIR / "data" / "processed"


def seed_users():
    """Create initial seed users: Admin, Demo User, and Active Dataset User."""
    logger.info("Seeding initial user accounts...")

    # 1. Admin User
    admin = User.query.filter_by(email="admin@ecommerce.com").first()
    if not admin:
        admin = User(name="System Administrator", email="admin@ecommerce.com", role="admin")
        admin.set_password("Admin@123")
        admin_cart = UserCart()
        admin.cart = admin_cart
        db.session.add(admin)
        logger.info("Created Admin User: admin@ecommerce.com / Admin@123")

    # 2. Demo User
    demo = User.query.filter_by(email="demo@ecommerce.com").first()
    if not demo:
        demo = User(name="Alex Demo", email="demo@ecommerce.com", role="user")
        demo.set_password("Demo@123")
        demo_cart = UserCart()
        demo.cart = demo_cart
        # Add onboarding preferences
        demo_prefs = [
            UserPreference(category="All Beauty", preference_weight=1.5),
            UserPreference(category="Appliances", preference_weight=1.2)
        ]
        demo.preferences = demo_prefs
        db.session.add(demo)
        logger.info("Created Demo User: demo@ecommerce.com / Demo@123")

    db.session.commit()
    return admin, demo


def seed_active_user_with_interactions(df_train: pd.DataFrame, df_products: pd.DataFrame):
    """
    Seed a real active user account mapped to the highest-activity training user
    and insert their authentic interaction history into the database.
    """
    top_user_id = df_train["user_id"].value_counts().index[0]
    user_train_rows = df_train[df_train["user_id"] == top_user_id]

    active_user = User.query.filter_by(email="activeuser@ecommerce.com").first()
    if not active_user:
        active_user = User(name="Jordan Music Fan", email="activeuser@ecommerce.com", role="user")
        active_user.set_password("User@123")
        active_user.cart = UserCart()
        active_user.preferences = [
            UserPreference(category="Digital Music", preference_weight=2.0)
        ]
        db.session.add(active_user)
        db.session.flush()
        logger.info(f"Created Active User: activeuser@ecommerce.com / User@123 (mapped to {top_user_id})")

    # Seed interactions
    existing_inter_count = Interaction.query.filter_by(user_id=active_user.id).count()
    if existing_inter_count == 0:
        logger.info(f"Seeding {len(user_train_rows)} real historical interactions for activeuser...")
        # Map external_product_id -> Product.id
        prod_map = {
            p.external_product_id: p.id for p in Product.query.filter(
                Product.external_product_id.in_(list(user_train_rows["product_id"].astype(str)))
            ).all()
        }

        inter_records = []
        for _, row in user_train_rows.iterrows():
            ext_pid = str(row["product_id"])
            if ext_pid in prod_map:
                inter_records.append(Interaction(
                    user_id=active_user.id,
                    product_id=prod_map[ext_pid],
                    interaction_type="rating",
                    rating=float(row.get("rating", 5.0)),
                    timestamp=datetime.fromtimestamp(int(row["timestamp"]), tz=timezone.utc)
                ))
        db.session.bulk_save_objects(inter_records)
        db.session.commit()
        logger.info(f"Successfully seeded {len(inter_records)} interactions for activeuser.")


def import_products_catalog(batch_size: int = 500):
    """Import preprocessed product catalog into SQLite database."""
    products_path = DATA_DIR / "products.parquet"
    if not products_path.exists():
        products_path = DATA_DIR / "products.csv"

    if not products_path.exists():
        raise FileNotFoundError(f"Processed products dataset not found in {DATA_DIR}")

    logger.info(f"Reading processed products from {products_path}...")
    df = pd.read_parquet(products_path) if str(products_path).endswith(".parquet") else pd.read_csv(products_path)

    total_in_file = len(df)
    logger.info(f"Loaded {total_in_file} products from processed data file.")

    # Find existing products by external_product_id to avoid duplicates
    existing_asins = set(
        pid for (pid,) in db.session.query(Product.external_product_id).all()
    )
    logger.info(f"Existing products in database: {len(existing_asins)}")

    new_products = []
    skipped_count = 0

    for _, row in df.iterrows():
        ext_id = str(row["product_id"])
        if ext_id in existing_asins:
            skipped_count += 1
            continue

        desc = str(row.get("description", "")) if not pd.isna(row.get("description")) else ""
        img = str(row.get("image_url", "")) if not pd.isna(row.get("image_url")) else ""

        p = Product(
            external_product_id=ext_id,
            title=str(row["title"])[:250],
            description=desc[:1500] if desc else None,
            category=str(row.get("category", "General")),
            price=round(float(row.get("price", 19.99)), 2),
            rating=round(float(row.get("rating", 4.0)), 2),
            image_url=img
        )
        new_products.append(p)
        existing_asins.add(ext_id)

        # Batch insert for high performance
        if len(new_products) >= batch_size:
            db.session.bulk_save_objects(new_products)
            db.session.commit()
            logger.info(f"Inserted batch of {len(new_products)} products...")
            new_products = []

    if new_products:
        db.session.bulk_save_objects(new_products)
        db.session.commit()
        logger.info(f"Inserted final batch of {len(new_products)} products.")

    total_inserted = total_in_file - skipped_count
    final_count = Product.query.count()
    logger.info(f"=== Product Import Summary ===")
    logger.info(f"Total in Dataset: {total_in_file} | Inserted: {total_inserted} | Skipped/Existing: {skipped_count} | Total in DB: {final_count}")
    return total_inserted, skipped_count, final_count


def run_init():
    """Main execution entry point."""
    app = create_app("development")
    with app.app_context():
        logger.info("Initializing database schema...")
        db.create_all()
        logger.info("Database schema initialized.")

        # Import products
        inserted, skipped, total = import_products_catalog()

        # Seed users
        seed_users()

        # Seed active dataset user with real training interactions
        train_path = DATA_DIR / "train_interactions.parquet"
        products_path = DATA_DIR / "products.parquet"
        if train_path.exists() and products_path.exists():
            df_train = pd.read_parquet(train_path)
            df_products = pd.read_parquet(products_path)
            seed_active_user_with_interactions(df_train, df_products)

        logger.info("Database initialization and product seeding completed successfully.")


if __name__ == "__main__":
    run_init()
