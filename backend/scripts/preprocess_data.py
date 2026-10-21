"""
preprocess_data.py
------------------
Reproducible data collection, cleaning, schema validation, and preprocessing
pipeline for the Personalized E-Commerce Recommendation System using the
authentic Amazon Reviews 2023 dataset (McAuley Lab / UCSD).

Pipeline Features:
1. Multi-category coverage: "All Beauty", "Appliances", and "Digital Music".
2. Prioritizes items with high interaction density for effective Collaborative Filtering
   while preserving catalog breadth across diverse categories.
3. Imputes missing prices using category medians, cleans text, normalizes timestamps.
4. Generates rich content_text for Content-Based TF-IDF vectorization.
5. Deduplicates user-item interactions and enforces interaction integrity.
6. Performs a leak-free temporal train/test split per user.
7. Saves processed outputs under data/processed/ in both Parquet and CSV formats.
8. Writes detailed preprocessing metadata and dataset limitations.
"""

import os
import re
import sys
import json
import random
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set

import requests
import numpy as np
import pandas as pd

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("preprocess_data")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Configuration & Categories
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

CATEGORIES = ["All_Beauty", "Appliances", "Digital_Music"]
HF_BASE_URL = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw"

MIN_ITEM_INTERACTIONS = 2
MIN_USER_INTERACTIONS = 2
TEST_HOLD_RATIO = 0.20  # Chronological holdout


def clean_price(val: Any) -> Optional[float]:
    """Parse string or numerical price into clean float; returns None if invalid."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else None
    
    val_str = str(val).strip()
    match = re.search(r"([0-9]+\.?[0-9]*)", val_str)
    if match:
        try:
            num = float(match.group(1))
            return num if num > 0 else None
        except ValueError:
            return None
    return None


def clean_text(text: Any) -> str:
    """Normalize text: strip HTML, extra whitespace, and normalize unicode."""
    if text is None or pd.isna(text):
        return ""
    text_str = str(text)
    text_str = re.sub(r"<[^>]+>", " ", text_str)
    text_str = re.sub(r"\s+", " ", text_str).strip()
    return text_str


def get_first_image_url(images: Any, category: str) -> str:
    """Extract first high-quality image URL or provide category-based asset."""
    if isinstance(images, list) and len(images) > 0:
        first = images[0]
        if isinstance(first, dict):
            url = first.get("large") or first.get("hi_res") or first.get("thumb")
            if url and isinstance(url, str) and url.startswith("http"):
                return url
        elif isinstance(first, str) and first.startswith("http"):
            return first
            
    category_defaults = {
        "All Beauty": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=600&auto=format&fit=crop&q=80",
        "Appliances": "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=600&auto=format&fit=crop&q=80",
        "Digital Music": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop&q=80",
    }
    return category_defaults.get(category, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80")


def get_raw_file_paths(category: str) -> Tuple[Path, Path]:
    """Determine paths for raw metadata and review files, preferring full files if present."""
    # Check for full files
    meta_full = RAW_DIR / f"meta_{category}_full.jsonl"
    meta_path = meta_full if meta_full.exists() else RAW_DIR / f"meta_{category}.jsonl"
    
    rev_full = RAW_DIR / f"{category}_full.jsonl"
    rev_path = rev_full if rev_full.exists() else RAW_DIR / f"{category}.jsonl"
    
    return meta_path, rev_path


def load_raw_products(target_prods: Optional[Set[str]] = None) -> pd.DataFrame:
    """Load metadata from raw files, clean and deduplicate products."""
    product_records = []
    seen_asins = set()
    
    cat_config = [
        ("All_Beauty", "All Beauty", 1500),
        ("Appliances", "Appliances", 1500),
        ("Digital_Music", "Digital Music", 3000)
    ]

    for cat_key, cat_name, max_items in cat_config:
        meta_file, _ = get_raw_file_paths(cat_key)
        if not meta_file.exists():
            logger.warning(f"Raw file not found: {meta_file}")
            continue
            
        count = 0
        with open(meta_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                    
                asin = item.get("parent_asin") or item.get("asin")
                if not asin or asin in seen_asins:
                    continue
                    
                # If target_prods specified and not yet full, prioritize target products
                if target_prods is not None and asin not in target_prods and count >= max_items:
                    continue
                    
                title = clean_text(item.get("title", ""))
                if not title or len(title) < 3:
                    continue
                    
                seen_asins.add(asin)
                
                desc_list = item.get("description", [])
                desc_text = " ".join([clean_text(d) for d in desc_list if clean_text(d)]) if isinstance(desc_list, list) else clean_text(desc_list)
                
                feat_list = item.get("features", [])
                feat_text = " ".join([clean_text(f) for f in feat_list if clean_text(f)]) if isinstance(feat_list, list) else clean_text(feat_list)
                
                content_components = [title, cat_name, feat_text, desc_text]
                store = clean_text(item.get("store", ""))
                if store:
                    content_components.append(f"Store: {store}")
                content_text = " ".join([c for c in content_components if c])
                
                price = clean_price(item.get("price"))
                
                avg_rating = item.get("average_rating")
                try:
                    avg_rating = float(avg_rating) if avg_rating is not None else 4.0
                    avg_rating = min(max(avg_rating, 1.0), 5.0)
                except (ValueError, TypeError):
                    avg_rating = 4.0
                    
                rating_num = item.get("rating_number")
                try:
                    rating_num = int(rating_num) if rating_num is not None else 1
                except (ValueError, TypeError):
                    rating_num = 1
                    
                image_url = get_first_image_url(item.get("images"), cat_name)
                
                product_records.append({
                    "product_id": asin,
                    "external_product_id": asin,
                    "title": title,
                    "category": cat_name,
                    "price": price,
                    "rating": round(avg_rating, 2),
                    "rating_count": rating_num,
                    "image_url": image_url,
                    "description": desc_text if desc_text else (feat_text if feat_text else title),
                    "features": feat_text,
                    "content_text": content_text,
                    "store": store
                })
                count += 1
                if count >= max_items and target_prods is None:
                    break
                    
    df_products = pd.DataFrame(product_records)
    logger.info(f"Loaded {len(df_products)} raw products across categories.")
    
    # Impute missing prices by category median with sensible fallback
    category_defaults = {"All Beauty": 18.99, "Appliances": 49.99, "Digital Music": 14.99}
    category_medians = df_products.groupby("category")["price"].median()
    
    for cat, default_p in category_defaults.items():
        if cat in category_medians and not pd.isna(category_medians[cat]):
            category_defaults[cat] = float(category_medians[cat])
            
    df_products["price"] = df_products.apply(
        lambda r: r["price"] if (r["price"] is not None and not pd.isna(r["price"])) else category_defaults.get(r["category"], 24.99),
        axis=1
    )
    df_products["price"] = df_products["price"].round(2)
    
    df_products = df_products.drop_duplicates(subset=["product_id"])
    return df_products


def load_raw_interactions(valid_product_ids: Set[str]) -> pd.DataFrame:
    """Load reviews matching valid product catalog, validate and deduplicate."""
    interaction_records = []
    cat_keys = ["All_Beauty", "Appliances", "Digital_Music"]
    
    for cat_key in cat_keys:
        _, rev_file = get_raw_file_paths(cat_key)
        if not rev_file.exists():
            continue
            
        with open(rev_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rev = json.loads(line)
                except Exception:
                    continue
                    
                prod_id = rev.get("parent_asin") or rev.get("asin")
                if not prod_id or prod_id not in valid_product_ids:
                    continue
                    
                user_id = rev.get("user_id")
                if not user_id or len(str(user_id).strip()) < 3:
                    continue
                user_id = str(user_id).strip()
                
                try:
                    rating = float(rev.get("rating", 0.0))
                    if rating < 1.0 or rating > 5.0:
                        continue
                except (ValueError, TypeError):
                    continue
                    
                raw_ts = rev.get("timestamp")
                try:
                    ts_val = int(raw_ts)
                    if ts_val > 1e11:  # milliseconds
                        ts_val = int(ts_val / 1000)
                    dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
                    iso_timestamp = dt.isoformat()
                except Exception:
                    ts_val = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
                    iso_timestamp = "2023-01-01T00:00:00+00:00"
                    
                verified = bool(rev.get("verified_purchase", False))
                helpful = int(rev.get("helpful_vote", 0)) if rev.get("helpful_vote") is not None else 0
                
                interaction_records.append({
                    "user_id": user_id,
                    "product_id": prod_id,
                    "rating": rating,
                    "timestamp": ts_val,
                    "timestamp_iso": iso_timestamp,
                    "verified_purchase": verified,
                    "interaction_type": "rating",
                    "helpful_vote": helpful,
                    "review_title": clean_text(rev.get("title", "")),
                    "review_text": clean_text(rev.get("text", ""))[:500]
                })
                
    df_interactions = pd.DataFrame(interaction_records)
    logger.info(f"Loaded {len(df_interactions)} raw interactions matching product catalog.")
    
    if df_interactions.empty:
        raise ValueError("No valid interactions found matching product catalog!")
        
    df_interactions = df_interactions.sort_values("timestamp").drop_duplicates(
        subset=["user_id", "product_id"], keep="last"
    )
    logger.info(f"Deduplicated interactions count: {len(df_interactions)}")
    return df_interactions


def find_top_reviewed_products() -> Set[str]:
    """Extract top reviewed product IDs to ensure dense review matching."""
    top_prods = set()
    cat_keys = ["All_Beauty", "Appliances", "Digital_Music"]
    
    for cat_key in cat_keys:
        _, rev_file = get_raw_file_paths(cat_key)
        if not rev_file.exists():
            continue
        counts = Counter()
        with open(rev_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    d = json.loads(line)
                    asin = d.get("parent_asin") or d.get("asin")
                    if asin:
                        counts[asin] += 1
                except Exception:
                    pass
        limit = 2500 if cat_key == "Digital_Music" else 1500
        for asin, _ in counts.most_common(limit):
            top_prods.add(asin)
            
    logger.info(f"Identified {len(top_prods)} top-reviewed candidate products.")
    return top_prods


def filter_dense_core(df_interactions: pd.DataFrame, min_user: int = MIN_USER_INTERACTIONS, min_item: int = MIN_ITEM_INTERACTIONS) -> pd.DataFrame:
    """Filter interactions to retain users and items meeting minimum interaction thresholds."""
    df_curr = df_interactions.copy()
    
    user_counts = df_curr["user_id"].value_counts()
    valid_users = user_counts[user_counts >= min_user].index
    
    item_counts = df_curr["product_id"].value_counts()
    valid_items = item_counts[item_counts >= min_item].index
    
    df_filtered = df_curr[
        df_curr["user_id"].isin(valid_users) & df_curr["product_id"].isin(valid_items)
    ].copy()
    
    logger.info(
        f"Filtered dense core (min_user={min_user}, min_item={min_item}): "
        f"{len(df_filtered)} interactions, {df_filtered['user_id'].nunique()} users, "
        f"{df_filtered['product_id'].nunique()} products."
    )
    return df_filtered


def temporal_train_test_split(df_interactions: pd.DataFrame, test_ratio: float = TEST_HOLD_RATIO) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Perform leak-free chronological per-user holdout train/test split."""
    train_list = []
    test_list = []
    
    df_sorted = df_interactions.sort_values(["user_id", "timestamp"])
    
    for _, group in df_sorted.groupby("user_id"):
        n_items = len(group)
        if n_items <= 1:
            train_list.append(group)
        else:
            n_test = max(1, int(round(n_items * test_ratio)))
            train_list.append(group.iloc[:-n_test])
            test_list.append(group.iloc[-n_test:])
            
    df_train = pd.concat(train_list, ignore_index=True)
    df_test = pd.concat(test_list, ignore_index=True) if test_list else pd.DataFrame(columns=df_interactions.columns)
    
    logger.info(f"Temporal Split: Train interactions = {len(df_train)}, Test interactions = {len(df_test)}")
    return df_train, df_test


def compute_catalog_ratings(df_products: pd.DataFrame, df_interactions: pd.DataFrame) -> pd.DataFrame:
    """Compute empirical average rating and interaction counts from real interactions."""
    stats = df_interactions.groupby("product_id").agg(
        empirical_avg_rating=("rating", "mean"),
        interaction_count=("rating", "count")
    ).reset_index()
    
    df_merged = df_products.merge(stats, on="product_id", how="left")
    df_merged["interaction_count"] = df_merged["interaction_count"].fillna(0).astype(int)
    df_merged["rating"] = df_merged.apply(
        lambda r: round(r["empirical_avg_rating"], 2) if r["interaction_count"] > 0 else r["rating"],
        axis=1
    )
    df_merged = df_merged.drop(columns=["empirical_avg_rating"])
    return df_merged


def run_pipeline() -> Dict[str, Any]:
    """Run full preprocessing pipeline, validate outputs, and save to disk."""
    logger.info("=== Starting Phase 1 Data Preprocessing Pipeline ===")
    
    # 1. Identify top-reviewed candidate products to ensure dense overlap
    top_candidates = find_top_reviewed_products()
    
    # 2. Load and clean products prioritizing top candidate items
    df_products = load_raw_products(target_prods=top_candidates)
    valid_product_ids = set(df_products["product_id"])
    
    # 3. Load interactions matching valid product catalog
    df_interactions_all = load_raw_interactions(valid_product_ids)
    
    # 4. Dense Core Filtering for Collaborative Filtering
    df_interactions_dense = filter_dense_core(df_interactions_all, min_user=MIN_USER_INTERACTIONS, min_item=MIN_ITEM_INTERACTIONS)
    
    # 5. Enrich product catalog with empirical interaction counts & ratings
    df_products = compute_catalog_ratings(df_products, df_interactions_all)
    
    # 6. Temporal Train/Test Split on dense interactions
    df_train, df_test = temporal_train_test_split(df_interactions_dense, test_ratio=TEST_HOLD_RATIO)
    
    # 7. Save Processed Datasets
    logger.info("Saving processed datasets to data/processed/...")
    
    df_products.to_parquet(PROCESSED_DIR / "products.parquet", index=False)
    df_interactions_all.to_parquet(PROCESSED_DIR / "interactions.parquet", index=False)
    df_train.to_parquet(PROCESSED_DIR / "train_interactions.parquet", index=False)
    df_test.to_parquet(PROCESSED_DIR / "test_interactions.parquet", index=False)
    
    df_products.to_csv(PROCESSED_DIR / "products.csv", index=False)
    df_interactions_all.to_csv(PROCESSED_DIR / "interactions.csv", index=False)
    df_train.to_csv(PROCESSED_DIR / "train_interactions.csv", index=False)
    df_test.to_csv(PROCESSED_DIR / "test_interactions.csv", index=False)
    
    n_users = df_interactions_all["user_id"].nunique()
    n_prods = df_products["product_id"].nunique()
    n_interactions = len(df_interactions_all)
    matrix_sparsity = (1.0 - (n_interactions / (n_users * n_prods))) * 100.0 if (n_users * n_prods) > 0 else 100.0
    
    metadata = {
        "dataset_name": "Amazon Reviews 2023 (McAuley Lab / UCSD)",
        "source_repository": "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023",
        "processed_timestamp": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "categories": CATEGORIES,
        "metrics": {
            "total_products": int(n_prods),
            "total_interactions": int(n_interactions),
            "unique_users": int(n_users),
            "matrix_sparsity_percent": round(matrix_sparsity, 4),
            "dense_core_interactions": int(len(df_interactions_dense)),
            "dense_core_users": int(df_interactions_dense["user_id"].nunique()),
            "dense_core_products": int(df_interactions_dense["product_id"].nunique()),
            "train_interactions": int(len(df_train)),
            "test_interactions": int(len(df_test)),
            "mean_product_price": round(float(df_products["price"].mean()), 2),
            "mean_product_rating": round(float(df_products["rating"].mean()), 2),
            "category_distribution": df_products["category"].value_counts().to_dict()
        },
        "limitations": [
            "Purchase history is proxied by verified_purchase reviews and explicit product ratings.",
            "Amazon prices formatted as text or missing were imputed using category medians.",
            "Cold users (<2 interactions) are preserved in the full interaction log but held out of dense matrix factorization."
        ]
    }
    
    with open(PROCESSED_DIR / "preprocessing_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    logger.info("=== Preprocessing Pipeline Completed Successfully ===")
    logger.info(
        f"Products: {n_prods} | Total Interactions: {n_interactions} | "
        f"Dense Core: {len(df_interactions_dense)} ({df_interactions_dense['user_id'].nunique()} users) | "
        f"Train: {len(df_train)} | Test: {len(df_test)} | Sparsity: {matrix_sparsity:.2f}%"
    )
    return metadata


if __name__ == "__main__":
    run_pipeline()
