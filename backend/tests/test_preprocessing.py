"""
test_preprocessing.py
---------------------
Unit and data integrity tests for the data preprocessing pipeline.
"""

import os
import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from backend.scripts.preprocess_data import (
    clean_price,
    clean_text,
    get_first_image_url,
    temporal_train_test_split,
    filter_dense_core,
    compute_catalog_ratings
)

PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"


def test_clean_price():
    """Verify clean_price parses various formats correctly."""
    assert clean_price("$19.99") == 19.99
    assert clean_price("  $100.50  ") == 100.50
    assert clean_price("25") == 25.0
    assert clean_price(14.95) == 14.95
    assert clean_price(None) is None
    assert clean_price("invalid_price") is None
    assert clean_price(-10.0) is None


def test_clean_text():
    """Verify clean_text strips HTML and normalizes whitespace."""
    raw = "<div>Hello &nbsp; <b>World</b>!   \n\n This is a test.</div>"
    cleaned = clean_text(raw)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "  " not in cleaned
    assert "Hello" in cleaned
    assert "World" in cleaned
    assert clean_text(None) == ""


def test_get_first_image_url():
    """Verify image extraction and fallback behaviour."""
    sample_images = [
        {"thumb": "https://example.com/thumb.jpg", "large": "https://example.com/large.jpg"}
    ]
    assert get_first_image_url(sample_images, "All_Beauty") == "https://example.com/large.jpg"
    assert "http" in get_first_image_url([], "All_Beauty")
    assert "http" in get_first_image_url(None, "Appliances")


def test_filter_dense_core():
    """Verify dense core filtering enforces min interaction counts."""
    interactions = pd.DataFrame({
        "user_id": ["u1", "u1", "u2", "u3", "u3"],
        "product_id": ["p1", "p2", "p1", "p1", "p2"],
        "rating": [5.0, 4.0, 3.0, 4.0, 5.0],
        "timestamp": [1, 2, 3, 4, 5]
    })
    filtered = filter_dense_core(interactions, min_user=2, min_item=2)
    # u2 has only 1 interaction -> removed
    assert "u2" not in filtered["user_id"].values
    assert len(filtered) == 4


def test_temporal_train_test_split():
    """Verify temporal train/test split avoids temporal leakage."""
    interactions = pd.DataFrame({
        "user_id": ["u1", "u1", "u1", "u1", "u2", "u2"],
        "product_id": ["p1", "p2", "p3", "p4", "p1", "p2"],
        "rating": [5.0, 4.0, 3.0, 4.0, 5.0, 4.0],
        "timestamp": [100, 200, 300, 400, 50, 60]
    })
    train, test = temporal_train_test_split(interactions, test_ratio=0.25)
    
    # Check that for any user, train timestamps are strictly <= test timestamps
    for user_id in interactions["user_id"].unique():
        u_train = train[train["user_id"] == user_id]
        u_test = test[test["user_id"] == user_id]
        if not u_train.empty and not u_test.empty:
            assert u_train["timestamp"].max() <= u_test["timestamp"].min()


@pytest.mark.skipif(not (PROCESSED_DIR / "products.csv").exists(), reason="Processed data not generated yet")
def test_processed_products_integrity():
    """Verify processed products table schema and constraints."""
    df = pd.read_csv(PROCESSED_DIR / "products.csv")
    required_cols = ["product_id", "title", "category", "price", "rating", "image_url", "content_text"]
    for col in required_cols:
        assert col in df.columns, f"Missing required column {col} in products.csv"
        
    assert not df["product_id"].isnull().any(), "Product IDs must not be null"
    assert df["product_id"].is_unique, "Product IDs must be unique"
    assert (df["price"] > 0).all(), "All product prices must be greater than zero"
    assert (df["rating"] >= 1.0).all() and (df["rating"] <= 5.0).all(), "Ratings must be between 1.0 and 5.0"
    assert not (df["content_text"].str.strip() == "").any(), "Content text must not be empty"


@pytest.mark.skipif(not (PROCESSED_DIR / "interactions.csv").exists(), reason="Processed data not generated yet")
def test_processed_interactions_integrity():
    """Verify processed interactions table schema and integrity."""
    df = pd.read_csv(PROCESSED_DIR / "interactions.csv")
    required_cols = ["user_id", "product_id", "rating", "timestamp", "verified_purchase"]
    for col in required_cols:
        assert col in df.columns, f"Missing required column {col} in interactions.csv"
        
    assert not df["user_id"].isnull().any(), "User IDs must not be null"
    assert not df["product_id"].isnull().any(), "Product IDs must not be null"
    assert (df["rating"] >= 1.0).all() and (df["rating"] <= 5.0).all(), "Ratings must be between 1.0 and 5.0"
    
    # Check duplicate interaction prevention
    dup_count = df.duplicated(subset=["user_id", "product_id"]).sum()
    assert dup_count == 0, f"Found {dup_count} duplicate user-product interaction pairs"
