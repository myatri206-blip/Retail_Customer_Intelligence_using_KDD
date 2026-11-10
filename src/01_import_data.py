
from pathlib import Path
import sqlite3
import pandas as pd

# Find the main project folder
ROOT = Path(__file__).resolve().parents[1]

# Dataset and database locations
excel_path = ROOT / "data" / "Online Retail.xlsx"
db_path = ROOT / "database" / "retail.db"

# Create the database folder if necessary
db_path.parent.mkdir(parents=True, exist_ok=True)

# Read the Excel dataset
print("Loading dataset...")
df = pd.read_excel(excel_path)

# Display basic information
print("Dataset loaded successfully!")
print("Total rows:", len(df))
print("Columns:", df.columns.tolist())
print(df.head())

# Import data into SQLite
with sqlite3.connect(db_path) as conn:
    df.to_sql(
        "raw_transactions",
        conn,
        if_exists="replace",
        index=False
    )

print("SQLite database created successfully!")
print("Database location:", db_path)
