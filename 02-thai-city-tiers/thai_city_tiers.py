"""
thai_city_tiers.py
Cluster Thai cities into population size tiers using scikit-learn k-means.
Same dataset as project 01 (Natural Earth populated-places.csv), but this time
the clustering is done in Python on population instead of location. The script
prints a tier summary, writes thai_cities_tiers.csv (reloadable into QGIS as a
points layer), and saves a map of the tiers to images/thai_city_tiers.png.

Run:  python thai_city_tiers.py
Needs: pandas, numpy, scikit-learn, matplotlib
"""

import os

# KMeans on Windows + MKL warns about a memory leak when there are fewer data
# chunks than CPU threads. Our data is tiny, so pin to one thread to silence it.
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# Standard CSV: comma-delimited, period decimals. low_memory=False avoids a
# mixed-type warning on some unused trailing columns in the Natural Earth export.
df = pd.read_csv("populated-places.csv", low_memory=False)

df = df[df["ADM0NAME"] == "Thailand"].copy()
df["POP_MAX"] = pd.to_numeric(df["POP_MAX"], errors="coerce")
df = df.dropna(subset=["POP_MAX", "LONGITUDE", "LATITUDE"])
df = df[df["POP_MAX"] > 0]

# Log-scale so Bangkok does not dominate the distance math.
X = np.log1p(df[["POP_MAX"]].values)
km = KMeans(n_clusters=4, n_init=10, random_state=42).fit(X)

# Relabel clusters 0..3 from smallest to largest, so the legend reads in order.
means = [X[km.labels_ == c].mean() for c in range(4)]
order = np.argsort(means)
remap = {old: new for new, old in enumerate(order)}
df["tier"] = [remap[c] for c in km.labels_]

df.to_csv("thai_cities_tiers.csv", index=False)

# --- Summary ---------------------------------------------------------------
print(df.groupby("tier")["POP_MAX"].agg(["count", "min", "max"]))
print()
for t in range(4):
    sub = df[df["tier"] == t].sort_values("POP_MAX", ascending=False)
    examples = ", ".join(sub["NAME"].head(3))
    print(f"tier {t}: {len(sub):>2} cities  e.g. {examples}")
print("\nsaved thai_cities_tiers.csv  (tier 0 = smallest towns, tier 3 = Bangkok)")

# --- Map -------------------------------------------------------------------
# Plot every city at its real location, colored and sized by population tier.
# This shows the headline result: tier 3 is Bangkok and nothing else.
os.makedirs("images", exist_ok=True)
labels = ["Tier 0  small towns", "Tier 1  small cities",
          "Tier 2  regional cities", "Tier 3  Bangkok"]
colors = ["#9ecae1", "#4292c6", "#08519c", "#cb181d"]

fig, ax = plt.subplots(figsize=(7, 9))
for t in range(4):
    sub = df[df["tier"] == t]
    ax.scatter(sub["LONGITUDE"], sub["LATITUDE"],
               s=20 + t * 35, c=colors[t], edgecolor="white",
               linewidth=0.4, label=labels[t], zorder=t + 2)

# Label Bangkok, the lone tier-3 city.
bkk = df[df["tier"] == 3].iloc[0]
ax.annotate("Bangkok", (bkk["LONGITUDE"], bkk["LATITUDE"]),
            textcoords="offset points", xytext=(8, 0),
            fontsize=9, fontweight="bold", color="#cb181d")

ax.set_aspect("equal")
ax.set_title("Thai cities by population tier (k-means, log population)")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend(loc="upper right", frameon=True, fontsize=8)
fig.tight_layout()
fig.savefig("images/thai_city_tiers.png", dpi=130)
print("saved images/thai_city_tiers.png")
