"""
generate_eda_notebook.py
------------------------
Executes Exploratory Data Analysis (EDA) on the preprocessed Amazon Reviews 2023 dataset,
generates statistical visualizations (using Matplotlib and Seaborn), saves figures to
reports/figures/, and writes a fully populated Jupyter Notebook to notebooks/eda.ipynb.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import seaborn as sns
import nbformat as nbf

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
FIGURES_DIR = BASE_DIR / "reports" / "figures"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

# Styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 11


def run_eda_and_generate_figures():
    print("Loading preprocessed datasets...")
    df_products = pd.read_csv(DATA_DIR / "products.csv")
    df_interactions = pd.read_csv(DATA_DIR / "interactions.csv")

    print(f"Products: {df_products.shape}, Interactions: {df_interactions.shape}")

    # 1. Rating Distribution Chart
    print("Generating Figure 1: Rating Distribution...")
    fig, ax = plt.subplots(figsize=(8, 5))
    rating_counts = df_interactions["rating"].value_counts().sort_index()
    palette = sns.color_palette("mako", len(rating_counts))
    bars = ax.bar(rating_counts.index, rating_counts.values, width=0.5, color=palette, edgecolor="#333333", alpha=0.9)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 200, f"{int(yval):,}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_title("Rating Distribution in Amazon Interactions", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Rating Score (1.0 to 5.0)", fontsize=12)
    ax.set_ylabel("Interaction Frequency", fontsize=12)
    ax.set_xticks([1.0, 2.0, 3.0, 4.0, 5.0])
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "rating_distribution.png", dpi=300)
    plt.close(fig)

    # 2. Category Distribution Chart
    print("Generating Figure 2: Category Distribution...")
    fig, ax = plt.subplots(figsize=(8, 5))
    cat_counts = df_products["category"].value_counts()
    colors = ["#4f46e5", "#06b6d4", "#10b981"]
    bars = ax.bar(cat_counts.index, cat_counts.values, color=colors[:len(cat_counts)], edgecolor="#222222", width=0.5, alpha=0.9)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 50, f"{int(yval):,}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_title("Product Catalog Distribution Across Categories", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Product Category", fontsize=12)
    ax.set_ylabel("Catalog Count", fontsize=12)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "category_distribution.png", dpi=300)
    plt.close(fig)

    # 3. User Interaction Frequency (Pareto / Power-Law Curve)
    print("Generating Figure 3: User Interaction Distribution...")
    user_counts = df_interactions["user_id"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(user_counts.values, bins=50, color="#6366f1", edgecolor="#1e1b4b", log=True, alpha=0.85)
    ax.set_title("Distribution of User Interactions (Log Scale)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Number of Reviews/Interactions per User", fontsize=12)
    ax.set_ylabel("Number of Users (Log Scale)", fontsize=12)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "user_interaction_distribution.png", dpi=300)
    plt.close(fig)

    # 4. Long-Tail Product Popularity Distribution
    print("Generating Figure 4: Long-Tail Product Popularity...")
    prod_counts = df_interactions["product_id"].value_counts().values
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(range(1, len(prod_counts) + 1), prod_counts, color="#ec4899", lw=2)
    ax.fill_between(range(1, len(prod_counts) + 1), prod_counts, color="#fbcfe8", alpha=0.6)
    
    # 80/20 annotation
    cumulative_interactions = np.cumsum(prod_counts)
    total_interactions = cumulative_interactions[-1]
    top_20_pct_idx = int(len(prod_counts) * 0.20)
    top_20_share = (cumulative_interactions[top_20_pct_idx] / total_interactions) * 100
    
    ax.axvline(x=top_20_pct_idx, color="#831843", linestyle="--", alpha=0.7, label=f"Top 20% Products ({top_20_share:.1f}% Interactions)")
    ax.set_title("Long-Tail Product Popularity Curve", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Ranked Product Index (Most Popular to Least Popular)", fontsize=12)
    ax.set_ylabel("Number of Interactions", fontsize=12)
    ax.legend(loc="upper right", frameon=True)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "product_popularity_distribution.png", dpi=300)
    plt.close(fig)

    # 5. Price Distribution by Category
    print("Generating Figure 5: Price Distribution by Category...")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(x="category", y="price", hue="category", data=df_products, palette="Set2", ax=ax, showfliers=False, legend=False)
    ax.set_title("Product Price Distribution by Category (Excluding Outliers)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Category", fontsize=12)
    ax.set_ylabel("Price ($ USD)", fontsize=12)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "price_distribution_by_category.png", dpi=300)
    plt.close(fig)

    print("All figures successfully saved to reports/figures/.")
    return df_products, df_interactions


def build_notebook():
    print("Building notebooks/eda.ipynb...")
    nb = nbf.v4.new_notebook()

    cells = []

    # Title & Metadata
    cells.append(nbf.v4.new_markdown_cell("""# Exploratory Data Analysis (EDA)
## Personalized E-Commerce Recommendation System
**Dataset:** Amazon Reviews 2023 (Curated by McAuley Lab, University of California San Diego)
**Categories:** All Beauty, Appliances, Digital Music

---

### Objectives of this Analysis:
1. Validate dataset shape, feature schema, and data types.
2. Investigate missing values, price distributions, and imputation results.
3. Quantify user interaction behavior, Pareto power-law skewness, and sparsity.
4. Analyze product popularity and the long-tail catalog phenomenon.
5. Provide actionable insights for **Collaborative Filtering**, **Content-Based Filtering**, and **Cold-Start** handling.
"""))

    # Imports
    cells.append(nbf.v4.new_code_cell("""import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Global aesthetics
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.size"] = 11

DATA_DIR = Path("../data/processed")
"""))

    # Load Data
    cells.append(nbf.v4.new_markdown_cell("## 1. Dataset Ingestion & Schema Inspection"))
    cells.append(nbf.v4.new_code_cell("""df_products = pd.read_csv(DATA_DIR / "products.csv")
df_interactions = pd.read_csv(DATA_DIR / "interactions.csv")

print(f"Products Table Shape: {df_products.shape[0]:,} rows x {df_products.shape[1]} columns")
print(f"Interactions Table Shape: {df_interactions.shape[0]:,} rows x {df_interactions.shape[1]} columns")
"""))

    cells.append(nbf.v4.new_code_cell("""df_products.info()
df_products.head(3)
"""))

    cells.append(nbf.v4.new_code_cell("""df_interactions.info()
df_interactions.head(3)
"""))

    # Missing Values
    cells.append(nbf.v4.new_markdown_cell("## 2. Missing Value & Duplicate Analysis"))
    cells.append(nbf.v4.new_code_cell("""print("=== Missing Values in Products Table ===")
print(df_products.isnull().sum())
print("\\n=== Missing Values in Interactions Table ===")
print(df_interactions.isnull().sum())

print(f"\\nDuplicate Product IDs: {df_products['product_id'].duplicated().sum()}")
print(f"Duplicate (User, Product) Interaction Pairs: {df_interactions.duplicated(subset=['user_id', 'product_id']).sum()}")
"""))

    # Key Statistics & Sparsity
    cells.append(nbf.v4.new_markdown_cell("""## 3. High-Level Summary Statistics & Matrix Sparsity
Matrix sparsity is defined as:
$$\\text{Sparsity} = \\left(1 - \\frac{|Interactions|}{|Users| \\times |Items|}\\right) \\times 100\\%$$
"""))
    cells.append(nbf.v4.new_code_cell("""n_users = df_interactions['user_id'].nunique()
n_products = df_products['product_id'].nunique()
n_interactions = len(df_interactions)

sparsity = (1.0 - (n_interactions / (n_users * n_products))) * 100.0

print(f"Unique Users: {n_users:,}")
print(f"Unique Products: {n_products:,}")
print(f"Total Interactions: {n_interactions:,}")
print(f"Interaction Matrix Sparsity: {sparsity:.4f}%")
"""))

    # Rating Distribution
    cells.append(nbf.v4.new_markdown_cell("## 4. Rating Distribution Analysis"))
    cells.append(nbf.v4.new_code_cell("""fig, ax = plt.subplots(figsize=(8, 4.5))
rating_counts = df_interactions['rating'].value_counts().sort_index()
sns.barplot(x=rating_counts.index, y=rating_counts.values, palette="mako", ax=ax)
ax.set_title("Interaction Rating Distribution (1.0 to 5.0 Stars)", fontweight="bold")
ax.set_xlabel("Star Rating")
ax.set_ylabel("Count")
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', fontsize=9, xytext=(0, 4), textcoords='offset points')
plt.tight_layout()
plt.show()
"""))

    # Category Distribution
    cells.append(nbf.v4.new_markdown_cell("## 5. Product Category Distribution"))
    cells.append(nbf.v4.new_code_cell("""fig, ax = plt.subplots(figsize=(8, 4.5))
cat_counts = df_products['category'].value_counts()
sns.barplot(x=cat_counts.index, y=cat_counts.values, palette=["#4f46e5", "#06b6d4", "#10b981"], ax=ax)
ax.set_title("Catalog Product Count by Category", fontweight="bold")
ax.set_xlabel("Category")
ax.set_ylabel("Products Count")
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', fontsize=9, xytext=(0, 4), textcoords='offset points')
plt.tight_layout()
plt.show()
"""))

    # User Interaction Activity
    cells.append(nbf.v4.new_markdown_cell("## 6. User Activity & Interaction Frequency (Pareto Skew)"))
    cells.append(nbf.v4.new_code_cell("""user_interactions = df_interactions['user_id'].value_counts()
print(f"Median interactions per user: {user_interactions.median():.1f}")
print(f"Max interactions by a single user: {user_interactions.max()}")
print(f"Users with >= 2 interactions: {(user_interactions >= 2).sum():,} ({(user_interactions >= 2).mean()*100:.2f}%)")
print(f"Users with >= 3 interactions: {(user_interactions >= 3).sum():,} ({(user_interactions >= 3).mean()*100:.2f}%)")

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(user_interactions.values, bins=50, color="#6366f1", log=True, edgecolor="#1e1b4b")
ax.set_title("Histogram of User Interactions (Log Scale)", fontweight="bold")
ax.set_xlabel("Interactions per User")
ax.set_ylabel("User Count (Log Scale)")
plt.tight_layout()
plt.show()
"""))

    # Product Popularity & Long-Tail Analysis
    cells.append(nbf.v4.new_markdown_cell("## 7. Product Popularity & Long-Tail Catalog Analysis"))
    cells.append(nbf.v4.new_code_cell("""prod_interactions = df_interactions['product_id'].value_counts()
print("Top 10 Most Interacted Products:")
top10_ids = prod_interactions.head(10).index
top10_details = df_products[df_products['product_id'].isin(top10_ids)][['product_id', 'title', 'category', 'price', 'rating']]
top10_details['interaction_count'] = top10_details['product_id'].map(prod_interactions)
display(top10_details.sort_values('interaction_count', ascending=False))
"""))

    cells.append(nbf.v4.new_code_cell("""fig, ax = plt.subplots(figsize=(9, 4.5))
counts_sorted = prod_interactions.values
ax.plot(range(1, len(counts_sorted) + 1), counts_sorted, color="#ec4899", lw=2)
ax.fill_between(range(1, len(counts_sorted) + 1), counts_sorted, color="#fbcfe8", alpha=0.6)

cum_interactions = np.cumsum(counts_sorted)
top_20_pct = int(len(counts_sorted) * 0.20)
share_20 = (cum_interactions[top_20_pct] / cum_interactions[-1]) * 100

ax.axvline(x=top_20_pct, color="#831843", linestyle="--", label=f"Top 20% Items ({share_20:.1f}% Interactions)")
ax.set_title("Long-Tail Distribution of Product Popularity", fontweight="bold")
ax.set_xlabel("Product Rank")
ax.set_ylabel("Interaction Count")
ax.legend(frameon=True)
plt.tight_layout()
plt.show()
"""))

    # Top-Rated Products with Bayesian Threshold
    cells.append(nbf.v4.new_markdown_cell("""## 8. High-Rated Products with Minimum Interaction Threshold
To prevent items with only a single 5-star rating from dominating recommendations, a minimum interaction threshold is applied.
"""))
    cells.append(nbf.v4.new_code_cell("""min_threshold = 5
popular_prods = df_products[df_products['interaction_count'] >= min_threshold].copy()
popular_prods = popular_prods.sort_values(by=['rating', 'interaction_count'], ascending=[False, False])

print(f"Products with at least {min_threshold} interactions: {len(popular_prods)}")
display(popular_prods[['title', 'category', 'price', 'rating', 'interaction_count']].head(10))
"""))

    # Strategic Findings & Conclusion
    cells.append(nbf.v4.new_markdown_cell("""## 9. Key Findings for Algorithmic Design
1. **High Matrix Sparsity (>99.9%):**
   - Direct item-to-item or user-to-user Collaborative Filtering faces sparse neighborhood overlaps.
   - **Resolution:** Truncated SVD dimensionality reduction (rank $k=30$) compresses the sparse user-item interaction matrix into dense latent spaces, eliminating zero-overlap bottlenecks.
2. **Extreme Power-Law Skew in User Activity:**
   - Most users have 1-2 interactions, while power users have dozens.
   - **Resolution:** Content-Based Filtering and onboarding preferences are vital for cold-start and low-activity users.
3. **Multi-Category Catalog Breadth:**
   - The catalog features distinct product categories ("All Beauty", "Appliances", "Digital Music"), enabling user category preference filtering and cross-category discovery.
4. **Hybrid Engine Synergy:**
   - $\\alpha \\times \\text{CF} + (1 - \\alpha) \\times \\text{CB}$ combines latent collaborative signals with semantic metadata signals, providing reliable recommendations across all user activity levels.
"""))

    nb.cells = cells
    with open(NOTEBOOKS_DIR / "eda.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Notebook notebooks/eda.ipynb generated successfully.")


if __name__ == "__main__":
    run_eda_and_generate_figures()
    build_notebook()
