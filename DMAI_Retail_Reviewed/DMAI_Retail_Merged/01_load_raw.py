
import sqlite3, pandas as pd
from config import DATA_FILE, DB_PATH

if not DATA_FILE.exists():
    raise SystemExit(f"Put the dataset at {DATA_FILE} .")

dtypes = {"InvoiceNo": str, "StockCode": str}   # read as text: invoice 'C536379' and code '85123A' contain letters
if DATA_FILE.suffix.lower() == ".xlsx":
    df = pd.read_excel(DATA_FILE, dtype=dtypes)
elif DATA_FILE.suffix.lower() == ".csv":
    df = pd.read_csv(DATA_FILE, encoding="ISO-8859-1", dtype=dtypes)
else:
    raise SystemExit("Choose an .xlsx workbook or a .csv file in config.py.")
required = {"InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"}
missing = sorted(required.difference(df.columns))
if missing:
    raise SystemExit(f"Missing columns: {missing}. Check the input file and its header row.")

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"]).dt.strftime("%Y-%m-%d %H:%M:%S")

with sqlite3.connect(DB_PATH) as con:
    df.to_sql("raw_online_retail", con, if_exists="replace", index=False)
    print("Rows loaded into raw_online_retail:", con.execute("SELECT COUNT(*) FROM raw_online_retail").fetchone()[0])
    print("\nFirst look with plain SQL:")
    q = """SELECT COUNT(*) AS rows_,
                  COUNT(DISTINCT CustomerID) AS customers,
                  COUNT(DISTINCT StockCode) AS products,
                  MIN(InvoiceDate) AS first_date, MAX(InvoiceDate) AS last_date,
                  SUM(CustomerID IS NULL) AS missing_customer_rows
           FROM raw_online_retail"""
    print(pd.read_sql(q, con).T.to_string(header=False))
