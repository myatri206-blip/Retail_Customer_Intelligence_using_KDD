
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# STEP 1: File paths
ROOT = Path(__file__).resolve().parents[1]
data_path = ROOT / "data" / "rfm_customers.csv"
output_dir = ROOT / "outputs" / "clustering"

output_dir.mkdir(parents=True, exist_ok=True)

# STEP 2: Load RFM data
rfm = pd.read_csv(
    data_path,
    dtype={"CustomerID": "string"}
)

features = ["Recency", "Frequency", "Monetary"]

print("Total customers:", len(rfm))
print(rfm.head())

# STEP 3: Check data quality
if rfm[features].isna().any().any():
    raise ValueError("RFM features contain missing values.")

if (rfm[features] < 0).any().any():
    raise ValueError("RFM features contain negative values.")

# STEP 4: Reduce skewness
X_log = np.log1p(rfm[features])

# STEP 5: Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_log)

# STEP 6: Test different K values
k_values = range(2, min(11, len(rfm)))

inertias = []
silhouette_scores = []

for k in k_values:
    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = model.fit_predict(X_scaled)

    inertia = model.inertia_

    # Sampling keeps silhouette computation manageable
    score = silhouette_score(
        X_scaled,
        labels,
        sample_size=min(2000, len(rfm)),
        random_state=42
    )

    inertias.append(inertia)
    silhouette_scores.append(score)

    print(
        f"K={k}, Inertia={inertia:.2f}, "
        f"Silhouette={score:.3f}"
    )

# STEP 7: Elbow plot
plt.figure(figsize=(8, 5))
plt.plot(list(k_values), inertias, marker="o")
plt.xlabel("Number of Clusters (K)")
plt.ylabel("Inertia")
plt.title("Elbow Method")
plt.tight_layout()
plt.savefig(
    output_dir / "elbow_plot.png",
    dpi=300
)
plt.close()

# STEP 8: Silhouette plot
plt.figure(figsize=(8, 5))
plt.plot(
    list(k_values),
    silhouette_scores,
    marker="o"
)
plt.xlabel("Number of Clusters (K)")
plt.ylabel("Silhouette Score")
plt.title("Silhouette Score vs K")
plt.tight_layout()
plt.savefig(
    output_dir / "silhouette_plot.png",
    dpi=300
)
plt.close()

# STEP 9: Select K using silhouette score
best_k = list(k_values)[
    int(np.argmax(silhouette_scores))
]

print("\nSelected K:", best_k)

# STEP 10: Train final K-Means model
final_model = KMeans(
    n_clusters=best_k,
    random_state=42,
    n_init=10
)

rfm["Cluster"] = final_model.fit_predict(X_scaled)

# STEP 11: Create cluster profiles
profiles = rfm.groupby("Cluster").agg(
    Customers=("CustomerID", "count"),
    AvgRecency=("Recency", "mean"),
    AvgFrequency=("Frequency", "mean"),
    AvgMonetary=("Monetary", "mean")
).round(2)

print("\nCluster profiles:")
print(profiles)

# STEP 12: Save outputs
rfm.to_csv(
    output_dir / "customer_segments.csv",
    index=False
)

profiles.to_csv(
    output_dir / "cluster_profiles.csv"
)

pd.DataFrame({
    "K": list(k_values),
    "Inertia": inertias,
    "SilhouetteScore": silhouette_scores
}).to_csv(
    output_dir / "cluster_evaluation.csv",
    index=False
)

print("\nClustering completed successfully!")
print("Results saved in:", output_dir)

# Customer segmentation scatter plot

plt.figure(figsize=(10, 6))

scatter = plt.scatter(
    rfm["Frequency"],
    rfm["Monetary"],
    c=rfm["Cluster"],
    cmap="tab10",
    alpha=0.6,
    s=20
)

plt.xscale("log")
plt.yscale("log")

plt.xlabel("Frequency (log scale)")
plt.ylabel("Monetary (£, log scale)")
plt.title("Customer Segments: Frequency vs Monetary")

plt.colorbar(scatter, label="Cluster")
plt.tight_layout()

plt.savefig(
    output_dir / "customer_segments_plot.png",
    dpi=300
)

plt.close()

print("Customer segmentation graph saved!")
