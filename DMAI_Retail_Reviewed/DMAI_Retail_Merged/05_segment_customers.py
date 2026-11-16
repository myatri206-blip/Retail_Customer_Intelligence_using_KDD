"""
05_segment_customers.py  -  KDD step 5b: unsupervised learning. Group customers with K-Means on RFM.

No labels here: we do NOT tell the computer "this is a loyal customer". It finds groups by
distance, and WE name them afterwards by reading their median R, F, M.
Analogy: dump 3,000 students in a hall and say "stand near people who behave like you".
"""
import sqlite3, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from config import *

con = sqlite3.connect(DB_PATH)
snap = pd.Timestamp(con.execute("SELECT MAX(invoice_date) FROM invoices").fetchone()[0]).normalize() + pd.Timedelta(days=1)
rfm = pd.read_sql("""
    SELECT i.customer_id,
           CAST(julianday(:snap) - julianday(date(MAX(i.invoice_date))) AS INTEGER) AS recency_days,
           COUNT(DISTINCT i.invoice_no)                                       AS frequency,
           SUM(ii.quantity * ii.unit_price)                                   AS monetary
    FROM invoices i JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
    GROUP BY i.customer_id""", con, params={"snap": snap.strftime("%Y-%m-%d")})
print(f"{len(rfm)} customers, 'today' = {snap.date()}")
print(rfm[["recency_days", "frequency", "monetary"]].describe().round(1).to_string())

# ---- scaling: log first (tames huge spenders, the paper's 'outliers'), then standardise ----
# Without this, monetary (up to 100,000+) would drown recency (0-373) in distance calculations.
if len(rfm) < 3:
    raise SystemExit("Silhouette comparison needs at least three customers. Use a larger dataset.")
X = np.log1p(rfm[["recency_days", "frequency", "monetary"]])
Xs = StandardScaler().fit_transform(X)

# ---- choose K: elbow (inertia) + silhouette ----
inertia, sil = [], []
distinct = len(np.unique(Xs, axis=0))
ks = [k for k in K_RANGE if 2 <= k < len(Xs) and k <= distinct]
if not ks:
    raise SystemExit("No valid K for these customer profiles. Check K_RANGE and the dataset.")
if K_FINAL is not None and K_FINAL not in ks:
    raise SystemExit(f"K_FINAL must be one of {ks}.")
for k in ks:
    km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit(Xs)
    inertia.append(km.inertia_)
    sil.append(silhouette_score(Xs, km.labels_))
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(ks, inertia, "o-"); ax[0].set(title="Elbow plot", xlabel="K", ylabel="inertia (compactness)")
ax[1].plot(ks, sil, "o-");     ax[1].set(title="Silhouette score", xlabel="K", ylabel="score (higher=better)")
plt.tight_layout(); plt.savefig(OUT / "choose_k.png", dpi=130); plt.close()
print("\nK vs silhouette:", {k: round(s, 3) for k, s in zip(ks, sil)})

K = K_FINAL if K_FINAL is not None else ks[int(np.argmax(sil))]
print("Chosen K =", K)
km = KMeans(n_clusters=K, n_init=10, random_state=RANDOM_STATE).fit(Xs)
rfm["cluster"] = km.labels_

# ---- profile every cluster in ORIGINAL units (pounds/days), so humans can read them ----
prof = rfm.groupby("cluster").agg(customers=("customer_id", "count"), recency_days=("recency_days", "median"),
                                  frequency=("frequency", "median"), monetary=("monetary", "median"),
                                  revenue=("monetary", "sum"))
prof["pct_customers"] = (100 * prof.customers / prof.customers.sum()).round(1)
prof["pct_revenue"] = (100 * prof.revenue / prof.revenue.sum()).round(1)

# ---- name them with simple, explainable rules (compare each cluster to overall medians) ----
med = rfm[["recency_days", "frequency", "monetary"]].median()
def name(r):
    recent, often, big = r.recency_days <= med.recency_days, r.frequency >= med.frequency, r.monetary >= med.monetary
    if recent and often and big: return "Champions"
    if recent and not often:     return "Recent / infrequent"
    if not recent and often and big: return "At risk (were loyal)"
    if not recent:               return "Less recent"
    return "Regular"
prof["segment"] = prof.apply(name, axis=1)
# if two clusters get the same name, separate them by spending rank so every label is unique
for nm, grp in prof.groupby("segment"):
    if len(grp) > 1:
        for rank, idx in enumerate(grp.sort_values("monetary", ascending=False).index, start=1):
            prof.loc[idx, "segment"] = f"{nm} (spend rank {rank})"
rfm["segment"] = rfm.cluster.map(prof["segment"])
print("\n", prof.round(1).drop(columns="revenue").to_string())
prof.round(1).to_csv(OUT / "segment_profiles.csv")

rfm.to_sql("customer_segments", con, if_exists="replace", index=False); con.commit()

# Export the partner's customer-level RFM, cluster profiles and diagnostics
# from the same features and assignments used in the reviewed analysis.
rfm_dir = OUT / "rfm"
cluster_dir = OUT / "clustering"
rfm_dir.mkdir(exist_ok=True)
cluster_dir.mkdir(exist_ok=True)
customer_export = rfm.rename(columns={"customer_id": "CustomerID", "recency_days": "Recency",
                                      "frequency": "Frequency", "monetary": "Monetary",
                                      "cluster": "Cluster", "segment": "Segment"})
customer_export["Monetary"] = customer_export["Monetary"].round(2)
customer_export[["CustomerID", "Recency", "Frequency", "Monetary"]].to_csv(
    rfm_dir / "rfm_customers.csv", index=False)
customer_export.to_csv(cluster_dir / "customer_segments.csv", index=False)
means = customer_export.groupby(["Cluster", "Segment"]).agg(
    Customers=("CustomerID", "size"), AvgRecency=("Recency", "mean"),
    AvgFrequency=("Frequency", "mean"), AvgMonetary=("Monetary", "mean"))
means.round(2).to_csv(cluster_dir / "cluster_profiles.csv")
pd.DataFrame({"K": ks, "Inertia": inertia, "SilhouetteScore": sil}).to_csv(
    cluster_dir / "cluster_evaluation.csv", index=False)

for column, unit in [("Recency", "days since last purchase"), ("Frequency", "orders"),
                     ("Monetary", "gross purchases in £")]:
    fig, axis = plt.subplots(figsize=(9, 5))
    axis.hist(customer_export[column], bins=40, edgecolor="black")
    axis.set(title=f"{column} distribution", xlabel=unit, ylabel="Customers")
    fig.tight_layout()
    fig.savefig(rfm_dir / f"{column.lower()}_distribution.png", dpi=150)
    plt.close(fig)

# ---- pictures ----
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
for c, g in rfm.groupby("cluster"):
    ax[0].scatter(np.log1p(g.frequency), np.log1p(g.monetary), s=6, alpha=.5, label=f"{c}: {prof.segment[c]}")
ax[0].set(xlabel="log(frequency)", ylabel="log(monetary)", title="Segments"); ax[0].legend(markerscale=3, fontsize=8)
x = np.arange(K); ax[1].bar(x - .2, prof.pct_customers, .4, label="% of customers"); ax[1].bar(x + .2, prof.pct_revenue, .4, label="% of revenue")
ax[1].set_xticks(x); ax[1].set_xticklabels(prof.segment, rotation=20, ha="right"); ax[1].legend(); ax[1].set_title("Who brings the money?")
plt.tight_layout(); plt.savefig(OUT / "segments.png", dpi=130); plt.close()
