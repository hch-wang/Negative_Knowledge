"""
ScienceAgentBench – task_002
Generate elemental features for material diffusion data and select 20 features via SHAP.
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import shap

# mastml ElementalFeatureGenerator
from mastml.feature_generators import ElementalFeatureGenerator

# ── paths ─────────────────────────────────────────────────────────────────────
WORK_DIR = "/Users/dietcoke/Documents/Project/00-simulation_software/paper/experiments/pilot_2026-05-10/runs/task_002/primary_4.6/v3/round1"
DATA_PATH = os.path.join(WORK_DIR, "benchmark/datasets/mat_diffusion/diffusion_data_nofeatures_new.xlsx")
OUT_DIR   = os.path.join(WORK_DIR, "pred_results")
OUT_PATH  = os.path.join(OUT_DIR, "mat_diffusion_features.csv")

os.makedirs(OUT_DIR, exist_ok=True)

# ── load data ─────────────────────────────────────────────────────────────────
df = pd.read_excel(DATA_PATH)

target_col = "E_regression"
comp_col   = "Material compositions joined"   # e.g. "AgAg", "AgCo", …

# ── featurise with MastML ElementalFeatureGenerator ───────────────────────────
# ElementalFeatureGenerator expects a DataFrame with a composition column.
efg = ElementalFeatureGenerator(composition_df=df[[comp_col]],
                                 feature_types="composition_avg")
# generate() returns (features_df, target_series_or_none)
X_all, _ = efg.generate()

# Drop columns that are entirely NaN or have zero variance
X_all = X_all.dropna(axis=1, how="all")
X_all = X_all.loc[:, X_all.std() > 0]

y = df[target_col].values

# ── train random forest for SHAP ──────────────────────────────────────────────
rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
rf.fit(X_all, y)

# ── SHAP feature importance ───────────────────────────────────────────────────
explainer   = shap.TreeExplainer(rf)
shap_values = explainer.shap_values(X_all)         # shape (n_samples, n_features)

mean_abs_shap = np.abs(shap_values).mean(axis=0)   # mean |SHAP| per feature

importance_df = pd.DataFrame({
    "feature":        X_all.columns,
    "mean_abs_shap":  mean_abs_shap,
}).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

top20_features = importance_df["feature"].head(20).tolist()

# ── save selected features ────────────────────────────────────────────────────
result_df = X_all[top20_features].copy()
result_df.to_csv(OUT_PATH, index=False)

print(f"Saved {result_df.shape[1]} features for {result_df.shape[0]} samples → {OUT_PATH}")
print("Selected features:", top20_features)
