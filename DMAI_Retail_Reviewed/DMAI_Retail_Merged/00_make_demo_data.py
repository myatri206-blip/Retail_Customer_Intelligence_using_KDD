"""
00_make_demo_data.py  -  OPTIONAL. Makes FAKE data shaped like the UCI Online Retail file
so you can test the pipeline before downloading the real one.
DO NOT report results from this file. Real results must come from the real dataset.
"""
import numpy as np, pandas as pd
from config import BASE

rng = np.random.default_rng(1)
start, end = pd.Timestamp("2010-12-01"), pd.Timestamp("2011-12-09")
days = (end - start).days
products = [f"{rng.integers(10000, 99999)}" for _ in range(300)]
prices = dict(zip(products, np.round(rng.uniform(0.5, 25, 300), 2)))
rows, inv = [], 536000

# 4 customer "personalities" - this is what K-Means should rediscover
types = {"champion": (600, 0.12), "regular": (500, 0.05), "occasional": (500, 0.015), "lapsed": (400, 0.02)}
cid = 12000
for t, (n, p) in types.items():
    for _ in range(n):
        cid += 1
        d0 = rng.integers(0, days)
        d1 = d0 + (rng.integers(20, 120) if t == "lapsed" else days)
        for d in range(d0, min(d1, days)):
            if rng.random() < p:
                inv += 1
                dt = start + pd.Timedelta(days=int(d), hours=int(rng.integers(8, 17)), minutes=int(rng.integers(0, 60)))
                for pr in rng.choice(products, rng.integers(1, 25 if t != "champion" else 60)):
                    q = int(rng.integers(1, 12 if t != "champion" else 48))
                    rows.append([str(inv), pr, "ITEM " + pr, q, dt, prices[pr], cid, "United Kingdom"])
df = pd.DataFrame(rows, columns=["InvoiceNo","StockCode","Description","Quantity","InvoiceDate","UnitPrice","CustomerID","Country"])

# --- inject the same kinds of mess the real file has ---
miss = df.sample(frac=0.2, random_state=1).index
df.loc[miss, "CustomerID"] = np.nan                                   # missing customer IDs
canc = df.sample(frac=0.02, random_state=2).copy()
canc["InvoiceNo"] = "C" + canc["InvoiceNo"]; canc["Quantity"] *= -1   # cancellations
junk = df.sample(frac=0.005, random_state=3).copy()
junk["StockCode"] = rng.choice(["POST", "M", "BANK CHARGES", "DOT"], len(junk))  # non-product rows
bad = df.sample(frac=0.003, random_state=4).copy(); bad["UnitPrice"] = 0          # price 0
dup = df.sample(frac=0.01, random_state=5).copy()                                 # exact duplicates
df = pd.concat([df, canc, junk, bad, dup]).sort_values("InvoiceDate").reset_index(drop=True)
out = BASE / "data" / "online_retail_demo.csv"
out.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out, index=False, encoding="ISO-8859-1")
print("Fake demo file written:", out, "rows:", len(df))
