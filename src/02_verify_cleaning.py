
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
db_path = ROOT / "database" / "retail.db"

with sqlite3.connect(db_path) as conn:
    df = pd.read_sql_query(
        "SELECT * FROM clean_transactions", conn
    )

print("Cleaned rows:", len(df))
print("Missing CustomerIDs:", df["CustomerID"].isna().sum())
print("Duplicate rows:", df.duplicated().sum())
print("Non-positive quantities:", (df["Quantity"] <= 0).sum())
print("Non-positive prices:", (df["UnitPrice"] <= 0).sum())
print("Total positive-sales revenue:", df["Revenue"].sum())
