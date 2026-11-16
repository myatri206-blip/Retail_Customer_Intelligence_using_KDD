"""Create the partner's five EDA charts from the team's shared sales view."""
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import DB_PATH, OUT

output_dir = OUT / "eda"
output_dir.mkdir(exist_ok=True)
if not DB_PATH.is_file():
    raise SystemExit("Run the database steps and 06_verify_sql.py first.")
with sqlite3.connect(DB_PATH) as conn:
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='clean_transactions'").fetchone():
        raise SystemExit("Run 06_verify_sql.py first to create the sales view.")
    df = pd.read_sql_query("SELECT * FROM clean_transactions", conn)

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

print("Dataset loaded!")
print("Rows:", len(df))
print("Customers:", df["CustomerID"].nunique())

plt.style.use("seaborn-v0_8-whitegrid")

# ----------------------------------
# GRAPH 1: MONTHLY REVENUE
# ----------------------------------

df["Month"] = df["InvoiceDate"].dt.to_period("M")

monthly_sales = (
    df.groupby("Month")["Revenue"]
    .sum()
    .sort_index()
)

plt.figure(figsize=(11, 5))

plt.plot(
    monthly_sales.index.astype(str),
    monthly_sales.values,
    marker="o"
)

last_day = df["InvoiceDate"].max().normalize()
title = "Monthly Retail Revenue"
if not last_day.is_month_end:
    title += f" (final month through {last_day:%d %b %Y})"
plt.title(title)
plt.xlabel("Month")
plt.ylabel("Positive-Sales Revenue (£)")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    output_dir / "monthly_revenue.png",
    dpi=300
)
plt.close()

print("Graph 1 saved!")

# ----------------------------------
# GRAPH 2: TOP 10 PRODUCTS
# ----------------------------------

products = df.copy()
products["Description"] = products["Description"].fillna("Unknown product")

top_products = (
    products.groupby(["StockCode", "Description"])["Revenue"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

plt.figure(figsize=(11, 6))

top_products.index = [f"{code}  {desc}" for code, desc in top_products.index]
top_products.sort_values().plot(kind="barh")

plt.title("Top 10 Products by Revenue")
plt.xlabel("Positive-Sales Revenue (£)")
plt.ylabel("Product")
plt.tight_layout()

plt.savefig(
    output_dir / "top_products.png",
    dpi=300
)
plt.close()

print("Graph 2 saved!")

# ----------------------------------
# GRAPH 3: REVENUE BY COUNTRY
# ----------------------------------

country_sales = (
    df.groupby("Country")["Revenue"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

plt.figure(figsize=(11, 6))

country_sales.sort_values().plot(kind="barh")

plt.title("Top 10 Countries by Revenue")
plt.xlabel("Positive-Sales Revenue (£)")
plt.ylabel("Country")
plt.tight_layout()

plt.savefig(
    output_dir / "country_revenue.png",
    dpi=300
)
plt.close()

print("Graph 3 saved!")

# ----------------------------------
# GRAPH 4: CUSTOMER SPENDING
# ----------------------------------

customer_spending = (
    df.groupby("CustomerID")["Revenue"]
    .sum()
)

plt.figure(figsize=(10, 5))

plt.hist(
    customer_spending,
    bins=50
)

plt.title("Customer Spending Distribution")
plt.xlabel("Total Customer Spending (£)")
plt.ylabel("Number of Customers")
plt.tight_layout()

plt.savefig(
    output_dir / "customer_spending.png",
    dpi=300
)
plt.close()

print("Graph 4 saved!")

# ----------------------------------
# GRAPH 5: ORDER FREQUENCY
# ----------------------------------

order_frequency = (
    df.groupby("CustomerID")["InvoiceNo"]
    .nunique()
)

plt.figure(figsize=(10, 5))

plt.hist(
    order_frequency,
    bins=40
)

plt.title("Customer Order Frequency")
plt.xlabel("Number of Orders")
plt.ylabel("Number of Customers")
plt.tight_layout()

plt.savefig(
    output_dir / "order_frequency.png",
    dpi=300
)
plt.close()

print("Graph 5 saved!")

# ----------------------------------
# SAVE SUMMARY STATISTICS
# ----------------------------------

summary = pd.DataFrame({
    "Metric": [
        "Transaction rows",
        "Unique customers",
        "Unique invoices",
        "Total positive-sales revenue",
        "Average customer spending"
    ],
    "Value": [
        len(df),
        df["CustomerID"].nunique(),
        df["InvoiceNo"].nunique(),
        df["Revenue"].sum(),
        customer_spending.mean()
    ]
})

summary.to_csv(
    output_dir / "eda_summary.csv",
    index=False
)

print("\nEDA completed successfully!")
print(summary.to_string(index=False))
print("\nAll graphs saved in:", output_dir)
