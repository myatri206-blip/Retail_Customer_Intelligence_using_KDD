
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Project paths
ROOT = Path(__file__).resolve().parents[1]
data_path = ROOT / "data" / "clean_transactions.csv"
output_dir = ROOT / "outputs" / "eda"

output_dir.mkdir(parents=True, exist_ok=True)

# Load cleaned dataset
df = pd.read_csv(
    data_path,
    dtype={
        "CustomerID": "string",
        "InvoiceNo": "string",
        "StockCode": "string"
    }
)

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

print("Dataset loaded!")
print("Rows:", len(df))
print("Customers:", df["CustomerID"].nunique())

sns.set_theme(style="whitegrid")

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

plt.title("Monthly Retail Revenue")
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

products = df.dropna(subset=["Description"]).copy()

top_products = (
    products.groupby("Description")["Revenue"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

plt.figure(figsize=(11, 6))

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

sns.histplot(
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

sns.histplot(
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
