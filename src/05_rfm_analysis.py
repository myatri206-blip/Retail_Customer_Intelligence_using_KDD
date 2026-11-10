
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------
# STEP 1: Project file locations
# ---------------------------------

ROOT = Path(__file__).resolve().parents[1]

data_path = ROOT / "data" / "clean_transactions.csv"
output_dir = ROOT / "outputs" / "rfm"

output_dir.mkdir(parents=True, exist_ok=True)

# ---------------------------------
# STEP 2: Load cleaned dataset
# ---------------------------------

df = pd.read_csv(
    data_path,
    dtype={
        "CustomerID": "string",
        "InvoiceNo": "string",
        "StockCode": "string"
    }
)

df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"], errors="raise"
)

print("Dataset loaded successfully!")
print("Transaction rows:", len(df))

# ---------------------------------
# STEP 3: Select reference date
# ---------------------------------

# One day after the last transaction
reference_date = (
    df["InvoiceDate"].max().normalize()
    + pd.Timedelta(days=1)
)

print("Reference date:", reference_date.date())

# ---------------------------------
# STEP 4: Calculate RFM features
# ---------------------------------

rfm = df.groupby("CustomerID").agg(
    LastPurchase=("InvoiceDate", "max"),
    Frequency=("InvoiceNo", "nunique"),
    Monetary=("Revenue", "sum")
)

rfm["Recency"] = (
    reference_date - rfm["LastPurchase"]
).dt.days

rfm = rfm.reset_index()

rfm = rfm[
    [
        "CustomerID",
        "Recency",
        "Frequency",
        "Monetary"
    ]
]

rfm["Monetary"] = rfm["Monetary"].round(2)

# ---------------------------------
# STEP 5: Verify results
# ---------------------------------

print("\nRFM dataset preview:")
print(rfm.head())

print("\nRFM summary statistics:")
print(
    rfm[
        ["Recency", "Frequency", "Monetary"]
    ].describe()
)

print("\nUnique customers:", len(rfm))

# ---------------------------------
# STEP 6: Save RFM dataset
# ---------------------------------

output_path = ROOT / "data" / "rfm_customers.csv"

rfm.to_csv(output_path, index=False)

print("\nRFM file saved:", output_path)

# ---------------------------------
# STEP 7: Create RFM histograms
# ---------------------------------

for column in ["Recency", "Frequency", "Monetary"]:

    plt.figure(figsize=(9, 5))

    plt.hist(
        rfm[column],
        bins=40,
        edgecolor="black"
    )

    plt.title(f"{column} Distribution")
    plt.xlabel(column)
    plt.ylabel("Number of Customers")
    plt.tight_layout()

    plt.savefig(
        output_dir / f"{column.lower()}_distribution.png",
        dpi=300
    )

    plt.close()

    print(f"{column} graph saved!")

print("\nRFM analysis completed successfully!")
