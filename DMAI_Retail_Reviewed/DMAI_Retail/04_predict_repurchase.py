"""
04_predict_repurchase.py  -  KDD step 5a: supervised learning. Predict repurchased_30d (0/1).

Models: Decision Tree (readable rules) vs Random Forest (many trees voting -> usually steadier).
Test set = the LAST snapshots in time (like predicting next month, not shuffling the past).
"""
import sqlite3, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.dummy import DummyClassifier
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix, ConfusionMatrixDisplay)
from config import *

con = sqlite3.connect(DB_PATH)
d = pd.read_sql("SELECT * FROM features_snapshots", con).sort_values(["cutoff", "customer_id"]).reset_index(drop=True)
FEATURES = ["recency_days", "frequency", "monetary", "avg_order_value", "n_products", "tenure_days", "orders_ever"]

# ---- time-based split with a "purge gap" ----
cut = sorted(d["cutoff"].unique())
n_test = max(2, round(TEST_FRACTION * len(cut)))
test_cuts = cut[-n_test:]
# a training snapshot's label looks 30 days ahead; it must not reach into the test period
train_cuts = [c for c in cut[:-n_test] if pd.Timestamp(c) + pd.Timedelta(days=HORIZON_DAYS) <= pd.Timestamp(test_cuts[0])]
if not train_cuts:
    raise SystemExit("No training snapshots remain after the time gap. Use a longer dataset.")
tr, te = d[d.cutoff.isin(train_cuts)], d[d.cutoff.isin(test_cuts)]
Xtr, ytr, Xte, yte = tr[FEATURES], tr[LABEL_COLUMN], te[FEATURES], te[LABEL_COLUMN]
print(f"Train: {len(tr)} rows ({train_cuts[0]} .. {train_cuts[-1]}) | Test: {len(te)} rows ({test_cuts[0]} .. {test_cuts[-1]})")
print(f"Share of 'will repurchase' -> train {ytr.mean():.2f}, test {yte.mean():.2f}")

if ytr.nunique() < 2:
    raise SystemExit("Training needs both customers who returned and customers who did not.")
if len(train_cuts) < 4:
    raise SystemExit("Too few training dates to tune models. Use the full workbook.")

# Each fold holds out complete snapshot dates. Every training outcome must
# already be observable when the first validation snapshot begins.
dates = pd.DatetimeIndex(train_cuts)
row_dates = pd.to_datetime(tr["cutoff"])
horizon = pd.Timedelta(days=HORIZON_DAYS)
cv = []
for earlier, later in TimeSeriesSplit(n_splits=3).split(dates):
    validation_start = dates[later[0]]
    eligible = dates[earlier][dates[earlier] + horizon <= validation_start]
    train_rows = np.flatnonzero(row_dates.isin(eligible))
    validation_rows = np.flatnonzero(row_dates.isin(dates[later]))
    if len(train_rows) and ytr.iloc[train_rows].nunique() == 2:
        cv.append((train_rows, validation_rows))
        print(f"CV {len(cv)}: train through {eligible[-1].date()}, "
              f"validate {validation_start.date()} .. {dates[later[-1]].date()}")
if len(cv) < 2:
    raise SystemExit("Too few usable validation periods after the label gap. Use the full workbook.")
models = {
    "Baseline (always majority)": DummyClassifier(strategy="most_frequent"),
    "Decision Tree": GridSearchCV(DecisionTreeClassifier(random_state=RANDOM_STATE),
                                  {"max_depth": [3, 4, 5, 6, 8], "min_samples_leaf": [10, 30, 60]}, scoring="f1", cv=cv),
    "Random Forest": GridSearchCV(RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1),
                                  {"max_depth": [5, 8, None], "min_samples_leaf": [5, 20]}, scoring="f1", cv=cv),
}

rows, fitted = [], {}
for name, m in models.items():
    m.fit(Xtr, ytr)
    best = m.best_estimator_ if hasattr(m, "best_estimator_") else m
    if hasattr(m, "best_params_"): print(f"{name}: best settings {m.best_params_}")
    p = best.predict(Xte); proba = best.predict_proba(Xte)[:, 1]
    fitted[name] = (best, p)
    rows.append({"model": name, "accuracy": accuracy_score(yte, p),
                 "precision": precision_score(yte, p, zero_division=0), "recall": recall_score(yte, p, zero_division=0),
                 "f1": f1_score(yte, p, zero_division=0),
                 "roc_auc": roc_auc_score(yte, proba) if yte.nunique() == 2 else np.nan})
res = pd.DataFrame(rows).round(3)
print("\n", res.to_string(index=False))
res.to_csv(OUT / "model_comparison.csv", index=False)

# ---- confusion matrices ----
fig, ax = plt.subplots(1, 2, figsize=(9, 4))
for a, nm in zip(ax, ["Decision Tree", "Random Forest"]):
    ConfusionMatrixDisplay(confusion_matrix(yte, fitted[nm][1], labels=[0, 1])).plot(ax=a, colorbar=False)
    a.set_title(nm)
plt.tight_layout(); plt.savefig(OUT / "confusion_matrices.png", dpi=130); plt.close()

# ---- what did the models learn? ----
rf, dt = fitted["Random Forest"][0], fitted["Decision Tree"][0]
imp = pd.Series(rf.feature_importances_, index=FEATURES).sort_values()
imp.plot.barh(title="Random Forest: feature importance"); plt.tight_layout(); plt.savefig(OUT / "feature_importance.png", dpi=130); plt.close()
plt.figure(figsize=(16, 7)); plot_tree(dt, feature_names=FEATURES, class_names=["no", "yes"], filled=True, max_depth=3, fontsize=8)
plt.savefig(OUT / "decision_tree.png", dpi=130); plt.close()
rules = export_text(dt, feature_names=FEATURES, max_depth=3)
(OUT / "decision_tree_rules.txt").write_text(rules)
print("\nDecision-tree rules (top levels):\n", rules)
print("Feature importance:\n", imp.sort_values(ascending=False).round(3).to_string())
