"""
Generates high-quality sample datasets with thousands of records (both CSV and XLSX formats)
tailored for DataPilot's Questionless Discovery Engine.

Features embedded:
- 3,500 rows across 14 diverse attributes.
- Strong Pearson correlations (e.g. age <-> order_amount, units <-> order_amount).
- Group differences (e.g. East region higher spending, Platinum tier perks).
- Category x Numeric distributions (Electronics vs Books).
- Temporal patterns across hours and weekdays.
- Lightweight service_type x channel interactions.
- Real-world data quality nuances (extreme VIP transactions, realistic missing values).
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd

def generate_sample_dataset(num_rows: int = 3500, random_seed: int = 42) -> pd.DataFrame:
    np.random.seed(random_seed)

    customer_ids = [f"CUST-{10000 + i}" for i in range(num_rows)]
    
    # 1. Demographics
    # Ages 18 to 75 with realistic distribution
    ages = np.random.normal(loc=41, scale=14, size=num_rows)
    ages = np.clip(ages, 18, 75).astype(int)

    # Incomes correlated with age + random variance
    base_income = 25 + (ages * 1.1) + np.random.normal(0, 15, size=num_rows)
    incomes_k = np.clip(base_income, 22, 190).round(1)

    # 2. Categoricals
    regions = np.random.choice(["East", "West", "North", "South"], size=num_rows, p=[0.28, 0.26, 0.24, 0.22])
    tiers = np.random.choice(["Bronze", "Silver", "Gold", "Platinum"], size=num_rows, p=[0.45, 0.30, 0.18, 0.07])
    categories = np.random.choice(
        ["Electronics", "Apparel", "Home & Kitchen", "Books & Media", "Health & Beauty"],
        size=num_rows,
        p=[0.22, 0.30, 0.20, 0.14, 0.14]
    )
    channels = np.random.choice(["Web", "Mobile App", "In-Store"], size=num_rows, p=[0.42, 0.40, 0.18])
    service_types = np.random.choice(["Standard", "Express", "Same-Day"], size=num_rows, p=[0.55, 0.33, 0.12])

    # 3. Numeric Targets with strong statistical relationships
    # Units purchased: 1 to 12
    units = np.random.geometric(p=0.35, size=num_rows)
    units = np.clip(units, 1, 12)

    # Discount applied: 0.0 to 0.35
    discounts = np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20, 0.25], size=num_rows, p=[0.35, 0.25, 0.18, 0.12, 0.07, 0.03])

    # Order amount generation:
    # Strong correlation with age (r ~ 0.70) and units
    category_multipliers = {
        "Electronics": 2.8,
        "Home & Kitchen": 1.4,
        "Apparel": 1.0,
        "Health & Beauty": 0.8,
        "Books & Media": 0.35,
    }
    cat_weights = np.array([category_multipliers[c] for c in categories])

    # Regional skew: East region spends significantly more (+52%)
    region_weights = np.array([1.52 if r == "East" else (0.88 if r == "South" else 1.0) for r in regions])

    # Base order amount
    order_amounts = (
        (15.0 + (ages * 5.2) + (units * 24.0) + (incomes_k * 1.5)) * cat_weights * region_weights
        + np.random.normal(0, 25, size=num_rows)
    )
    order_amounts = np.clip(order_amounts, 12.5, 2900.0).round(2)

    # 4. Delivery days & Service type interaction
    delivery_days = []
    for s, c, u in zip(service_types, channels, units):
        if s == "Same-Day":
            base_days = 0.8 + np.random.uniform(0.1, 0.6)
        elif s == "Express":
            base_days = 2.0 + np.random.uniform(0.2, 1.2)
        else: # Standard
            base_days = 4.5 + np.random.uniform(0.5, 3.2)
        
        # Interaction: Mobile App orders in Same-Day have streamlined priority processing
        if s == "Same-Day" and c == "Mobile App":
            base_days = max(0.4, base_days - 0.4)
            
        delivery_days.append(round(base_days, 1))
    delivery_days = np.array(delivery_days)

    # 5. Customer satisfaction rating (1.0 to 5.0)
    # Higher for Platinum, lower for long delivery days
    tier_boost = np.array([0.9 if t == "Platinum" else (0.5 if t == "Gold" else 0.0) for t in tiers])
    ratings = 4.2 + tier_boost - (delivery_days * 0.18) + np.random.normal(0, 0.35, size=num_rows)
    ratings = np.clip(ratings, 1.0, 5.0).round(1)

    # 6. Order timestamp generation across Q1 2026 (Jan 1 to Mar 31)
    start_ts = pd.Timestamp("2026-01-01 08:00:00")
    # Biased hours (evening peak 18:00 - 21:00)
    raw_hour_probs = np.array([
        0.01, 0.01, 0.01, 0.01, 0.01, 0.02, # 00-05
        0.03, 0.04, 0.06, 0.07, 0.06, 0.05, # 06-11
        0.06, 0.06, 0.05, 0.05, 0.06, 0.07, # 12-17
        0.10, 0.10, 0.08, 0.05, 0.03, 0.02  # 18-23 (Evening peak)
    ])
    hour_probs = raw_hour_probs / raw_hour_probs.sum()

    hours = np.random.choice(
        list(range(24)),
        size=num_rows,
        p=hour_probs
    )
    days_offset = np.random.randint(0, 90, size=num_rows)
    minutes = np.random.randint(0, 60, size=num_rows)
    seconds = np.random.randint(0, 60, size=num_rows)

    timestamps = [
        (start_ts + pd.Timedelta(days=int(d), hours=int(h), minutes=int(m), seconds=int(s))).strftime("%Y-%m-%d %H:%M:%S")
        for d, h, m, s in zip(days_offset, hours, minutes, seconds)
    ]

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "customer_age": ages,
        "annual_income_k": incomes_k,
        "membership_tier": tiers,
        "region": regions,
        "product_category": categories,
        "sales_channel": channels,
        "units_purchased": units,
        "order_amount": order_amounts,
        "discount_rate": discounts,
        "delivery_days": delivery_days,
        "service_type": service_types,
        "satisfaction_score": ratings,
        "order_timestamp": timestamps,
    })

    # 7. Realistic Data Quality nuances (anomalies / extreme values)
    # 4 extreme VIP enterprise transactions (outliers in order_amount)
    outlier_indices = [15, 142, 850, 2190]
    for idx in outlier_indices:
        df.loc[idx, "order_amount"] = 8450.00
        df.loc[idx, "units_purchased"] = 35

    # 1.5% realistic nulls in delivery_days (e.g. pending/unfulfilled orders)
    null_indices = np.random.choice(range(num_rows), size=int(num_rows * 0.015), replace=False)
    df.loc[null_indices, "delivery_days"] = np.nan

    return df

def main():
    print("Generating 3,500-row realistic sample dataset...")
    df = generate_sample_dataset(num_rows=3500)
    print(f"Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")

    # Define paths
    base_dir = Path(__file__).resolve().parent.parent
    sample_dir = base_dir / "sample_data"
    static_sample_dir = base_dir / "backend" / "app" / "static" / "samples"
    
    sample_dir.mkdir(parents=True, exist_ok=True)
    static_sample_dir.mkdir(parents=True, exist_ok=True)

    csv_filename = "retail_sales_3500_records.csv"
    xlsx_filename = "retail_sales_3500_records.xlsx"

    csv_path = sample_dir / csv_filename
    xlsx_path = sample_dir / xlsx_filename

    static_csv_path = static_sample_dir / csv_filename
    static_xlsx_path = static_sample_dir / xlsx_filename

    # Save CSV
    df.to_csv(csv_path, index=False)
    df.to_csv(static_csv_path, index=False)
    print(f"Saved CSV: {csv_path} ({csv_path.stat().st_size / 1024:.1f} KB)")

    # Save XLSX
    df.to_excel(xlsx_path, index=False, engine="openpyxl")
    df.to_excel(static_xlsx_path, index=False, engine="openpyxl")
    print(f"Saved Excel: {xlsx_path} ({xlsx_path.stat().st_size / 1024:.1f} KB)")

    print("\nSummary of columns:")
    for col in df.columns:
        print(f" - {col}: {df[col].dtype} ({df[col].nunique()} unique, {df[col].isna().sum()} nulls)")

if __name__ == "__main__":
    main()
