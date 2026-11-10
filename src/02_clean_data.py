
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
db_path = ROOT / "database" / "retail.db"
output_path = ROOT / "data" / "clean_transactions.csv"

# Read raw data from SQLite
with sqlite3.connect(db_path) as conn:
    df = pd.read_sql_query(
        "SELECT * FROM raw_transactions",
        conn
    )

print("Original rows:", len(df))

# Convert data types
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"], errors="coerce"
)

df["CustomerID"] = pd.to_numeric(
    df["CustomerID"], errors="coerce"
).astype("Int64").astype("string")

# Check data quality before cleaning
print("\nMissing values:")
print(df.isnull().sum())

print("\nDuplicate rows:", df.duplicated().sum())

# Remove duplicate records
df = df.drop_duplicates()

# Exclude cancelled invoices
cancelled = df["InvoiceNo"].astype(str).str.startswith("C")

# Keep valid positive-sales transactions
clean = df[
    df["CustomerID"].notna()
    & df["InvoiceDate"].notna()
    & ~cancelled
    & (df["Quantity"] > 0)
    & (df["UnitPrice"] > 0)
].copy()

# Calculate revenue
clean["Revenue"] = (
    clean["Quantity"] * clean["UnitPrice"]
)

# Save cleaned data to SQLite
with sqlite3.connect(db_path) as conn:
    clean.to_sql(
        "clean_transactions",
        conn,
        if_exists="replace",
        index=False
    )

# Export cleaned data to CSV
clean.to_csv(output_path, index=False)

print("\nCleaning completed!")
print("Original rows:", len(df))
print("Cleaned rows:", len(clean))
print("Unique customers:", clean["CustomerID"].nunique())
print("Saved CSV:", output_path)
