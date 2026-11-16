
import sqlite3, pandas as pd
from config import DB_PATH, OUT

con = sqlite3.connect(DB_PATH)
con.execute("PRAGMA foreign_keys = ON")          # SQLite ignores foreign keys unless you switch this on!
df = pd.read_sql("SELECT * FROM raw_online_retail", con)

log = []
def step(name, before, after, why):
    log.append({"step": name, "rows_before": before, "rows_after": after,
                "rows_removed": before - after, "reason": why})

n = len(df); log.append({"step": "0. raw rows", "rows_before": n, "rows_after": n, "rows_removed": 0, "reason": "starting point"})

# 1) Cancellations: invoice numbers starting with 'C'. Kept in their own table, NOT thrown away,
#    because "who returns a lot" is useful knowledge later.
is_cancel = df["InvoiceNo"].str.startswith("C")
cancellations = df[is_cancel].copy()
df = df[~is_cancel]; step("1. cancellations", n, len(df), "InvoiceNo starts with 'C' -> moved to table 'cancellations'"); n = len(df)

# 2) No CustomerID -> we cannot say WHO bought it, so useless for customer analysis.
df = df[df["CustomerID"].notna()]; step("2. missing CustomerID", n, len(df), "cannot link purchase to a customer"); n = len(df)

# 3) Impossible numbers.
df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]; step("3. qty<=0 or price<=0", n, len(df), "free/negative/adjustment rows are not real sales"); n = len(df)

# 4) Non-product rows (POST = postage, M = manual, BANK CHARGES, DOT...). Real products start with 5 digits.
df = df[df["StockCode"].str.match(r"^\d{5}")]; step("4. non-product codes", n, len(df), "postage/fees/manual entries are not products"); n = len(df)

# 5) Repeated invoice lines matching the six fields below.
keys = ["InvoiceNo", "StockCode", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID"]
df = df.drop_duplicates(subset=keys); step("5. duplicate rows", n, len(df), "same invoice, stock, quantity, date, price and customer"); n = len(df)

df = df.assign(CustomerID=df["CustomerID"].astype(int), Description=df["Description"].astype("string").str.strip())

# ---------- Relational design ----------
con.executescript("""
DROP TABLE IF EXISTS invoice_items; DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS products;      DROP TABLE IF EXISTS customers;

CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, country TEXT);
CREATE TABLE products  (stock_code  TEXT PRIMARY KEY,    description TEXT);
CREATE TABLE invoices  (invoice_no  TEXT PRIMARY KEY,
                        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                        invoice_date TEXT NOT NULL, country TEXT);
CREATE TABLE invoice_items (item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_no TEXT NOT NULL REFERENCES invoices(invoice_no),
                        stock_code TEXT NOT NULL REFERENCES products(stock_code),
                        quantity INTEGER NOT NULL CHECK (quantity > 0),
                        unit_price REAL NOT NULL CHECK (unit_price > 0));
CREATE INDEX idx_inv_cust_date ON invoices(customer_id, invoice_date);
CREATE INDEX idx_items_invoice ON invoice_items(invoice_no);
""")

customers = df.groupby("CustomerID", as_index=False)["Country"].first().rename(columns={"CustomerID": "customer_id", "Country": "country"})
desc = (df.dropna(subset=["Description"]).groupby("StockCode")["Description"]
          .agg(lambda s: s.mode().iloc[0]).rename("description").reset_index())
products = pd.DataFrame({"StockCode": df["StockCode"].unique()}).merge(desc, how="left", on="StockCode").rename(columns={"StockCode": "stock_code"})
invoices = (df.groupby("InvoiceNo", as_index=False).agg(customer_id=("CustomerID", "first"), invoice_date=("InvoiceDate", "min"), country=("Country", "first"))
              .rename(columns={"InvoiceNo": "invoice_no"}))
items = df[["InvoiceNo", "StockCode", "Quantity", "UnitPrice"]].rename(
    columns={"InvoiceNo": "invoice_no", "StockCode": "stock_code", "Quantity": "quantity", "UnitPrice": "unit_price"})

# parent tables first, children after (a bill cannot point to a customer that does not exist yet)
customers.to_sql("customers", con, if_exists="append", index=False)
products.to_sql("products", con, if_exists="append", index=False)
invoices.to_sql("invoices", con, if_exists="append", index=False)
items.to_sql("invoice_items", con, if_exists="append", index=False)
cancellations.to_sql("cancellations", con, if_exists="replace", index=False)
logdf = pd.DataFrame(log); logdf.to_sql("cleaning_log", con, if_exists="replace", index=False)
con.commit()

bad = con.execute("PRAGMA foreign_key_check").fetchall()
print(logdf.to_string(index=False))
print("\nForeign-key violations:", len(bad))
for t in ["customers", "products", "invoices", "invoice_items", "cancellations"]:
    print(f"{t:15s}", con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
logdf.to_csv(OUT / "cleaning_log.csv", index=False)
con.close()
