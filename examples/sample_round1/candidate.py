# Attempt 1: per-feature importance via SHAP TreeExplainer.
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import shap  # <- not available in the execution environment

df = pd.read_csv("data/train.csv")
X, y = df.drop(columns=["target"]), df["target"]
model = RandomForestRegressor(n_estimators=200).fit(X, y)

explainer = shap.TreeExplainer(model)          # never reached
importances = explainer.shap_values(X)
pd.DataFrame(importances).to_csv("pred_results/importances.csv", index=False)
