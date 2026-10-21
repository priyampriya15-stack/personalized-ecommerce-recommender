import json
from pathlib import Path
import pandas as pd

def audit_dataset():
    meta_path = Path("data/processed/preprocessing_metadata.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    print("METADATA:")
    print(json.dumps(meta, indent=2))

    products_df = pd.read_parquet("data/processed/products.parquet")
    interactions_df = pd.read_parquet("data/processed/interactions.parquet")

    print("\nPRODUCTS INFO:")
    print(f"Shape: {products_df.shape}")
    print(f"Columns: {list(products_df.columns)}")
    print("Missing values:")
    for col, val in products_df.isnull().sum().items():
        print(f"  {col}: {val}")
    dups = products_df["external_product_id"].duplicated().sum()
    print(f"Duplicates (external_product_id): {dups}")
    print("Categories:", dict(products_df["category"].value_counts()))

    print("\nINTERACTIONS INFO:")
    print(f"Shape: {interactions_df.shape}")
    print(f"Columns: {list(interactions_df.columns)}")
    print("Missing values:")
    for col, val in interactions_df.isnull().sum().items():
        print(f"  {col}: {val}")
    print("Duplicates (user_id + product_id):", interactions_df.duplicated(subset=["user_id", "product_id"]).sum())
    print("Unique users:", interactions_df["user_id"].nunique())
    print("Unique items:", interactions_df["product_id"].nunique())
    min_r = interactions_df["rating"].min()
    max_r = interactions_df["rating"].max()
    mean_r = interactions_df["rating"].mean()
    print(f"Rating stats: min={min_r}, max={max_r}, mean={mean_r:.2f}")

if __name__ == "__main__":
    audit_dataset()
