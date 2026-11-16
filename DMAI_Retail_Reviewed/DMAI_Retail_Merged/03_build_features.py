"""
03_build_features.py  -  KDD step 4: turn raw purchases into ONE ROW PER CUSTOMER PER CUTOFF (RFM + extras)
for the repurchase prediction. The aggregation is done in SQL (that is the 'database' part of the course).

THE KEY IDEA - "snapshots" (avoids cheating / data leakage):
Pretend today is a CUTOFF date. Describe each customer using ONLY the 90 days BEFORE the cutoff.
Then look at the 30 days AFTER the cutoff: did they buy again? That yes/no is the label.

        |<---- 90 days history (features) ---->| CUTOFF |<-- 30 days (label) -->|

Riya example: at cutoff 1 June she had 3 orders in the last 90 days, last one 6 days ago.
If she orders on 15 June -> label = 1 (repurchased). Features never see 15 June.

We repeat this for many cutoffs (every 15 days) so we get thousands of training rows instead of ~4,000.
"""
import sqlite3, pandas as pd
from config import *

SQL = f"""
WITH w AS (                                   -- behaviour inside the 90-day history window
  SELECT i.customer_id,
         MAX(i.invoice_date)                  AS last_dt,
         COUNT(DISTINCT i.invoice_no)         AS frequency,
         SUM(ii.quantity * ii.unit_price)     AS monetary,
         COUNT(DISTINCT ii.stock_code)        AS n_products
  FROM invoices i JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
  WHERE i.invoice_date >= date(:c, '-' || :h || ' days') AND i.invoice_date < :c
  GROUP BY i.customer_id
), t AS (                                     -- whole past before the cutoff (never the future!)
  SELECT customer_id, MIN(invoice_date) AS first_dt, COUNT(*) AS orders_ever
  FROM invoices WHERE invoice_date < :c GROUP BY customer_id
)
SELECT :c AS cutoff, w.customer_id,
       CAST(julianday(:c) - julianday(date(w.last_dt))  AS INTEGER) AS recency_days,
       w.frequency,
       ROUND(w.monetary, 2)                       AS monetary,
       ROUND(w.monetary * 1.0 / w.frequency, 2)   AS avg_order_value,
       w.n_products,
       CAST(julianday(:c) - julianday(date(t.first_dt)) AS INTEGER) AS tenure_days,
       t.orders_ever,
       EXISTS (SELECT 1 FROM invoices x                          -- the LABEL: any invoice in next 30 days?
               WHERE x.customer_id = w.customer_id
                 AND x.invoice_date >= :c
                 AND x.invoice_date <  date(:c, '+' || :z || ' days')) AS {LABEL_COLUMN}
FROM w JOIN t ON t.customer_id = w.customer_id
"""

con = sqlite3.connect(DB_PATH)
bounds = con.execute("SELECT MIN(invoice_date), MAX(invoice_date) FROM invoices").fetchone()
if None in bounds:
    raise SystemExit("No clean invoices. Check the cleaning log and the input dataset.")
mn, mx = map(pd.Timestamp, bounds)
first_cut = mn.normalize() + pd.Timedelta(days=HISTORY_DAYS)     # need a full 90 days of history
last_cut = mx.normalize() - pd.Timedelta(days=HORIZON_DAYS)      # need a full 30 days of future to label
cutoffs = pd.date_range(first_cut, last_cut, freq=f"{SNAPSHOT_STEP_DAYS}D")
if cutoffs.empty:
    raise SystemExit(f"Data covers {mn.date()} to {mx.date()}. Use the full workbook to build "
                     f"{HISTORY_DAYS}-day histories and {HORIZON_DAYS}-day outcomes.")
print(f"Data runs {mn.date()} -> {mx.date()}. Using {len(cutoffs)} snapshots: {cutoffs[0].date()} ... {cutoffs[-1].date()}")

frames = [pd.read_sql(SQL, con, params={"c": c.strftime("%Y-%m-%d"), "h": HISTORY_DAYS, "z": HORIZON_DAYS}) for c in cutoffs]
feat = pd.concat(frames, ignore_index=True)
if feat.empty:
    raise SystemExit("No customers bought during the history windows. Check the invoice dates.")
feat.to_sql("features_snapshots", con, if_exists="replace", index=False)
con.commit()

print("Rows:", len(feat), "| distinct customers:", feat.customer_id.nunique())
print(f"Share who repurchased within {HORIZON_DAYS} days (class balance):", round(feat[LABEL_COLUMN].mean(), 3))
print(feat.head().to_string(index=False))
