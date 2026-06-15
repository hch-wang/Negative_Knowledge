import os
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV

# ── paths ──────────────────────────────────────────────────────────────────
TRAIN_CSV = "benchmark/datasets/dili/train.csv"
OUT_DIR   = "pred_results"
os.makedirs(OUT_DIR, exist_ok=True)

# ── featurisation ──────────────────────────────────────────────────────────
def smiles_to_fp(smiles: str, n_bits: int = 2048, radius: int = 2):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return np.zeros(n_bits, dtype=np.float32)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    return np.array(fp, dtype=np.float32)

# ── load & prepare data ────────────────────────────────────────────────────
df = pd.read_csv(TRAIN_CSV, index_col=0)

# row index ranges (1-based row numbers → 0-based pandas iloc)
# MC  : rows 1–173   → iloc 0..172
# LC  : rows 174–433 → iloc 173..432
# NC  : rows 434–660 → iloc 433..659
# sider: rows 661–923 → iloc 660..922

mc    = df.iloc[0:173]
lc    = df.iloc[173:433]
nc    = df.iloc[433:660]
sider = df.iloc[660:923]

POSITIVE_VALS = {"vMost-DILI-Concern", "vLess-DILI-Concern"}

def make_label(row_series):
    return row_series["vDILIConcern"].apply(
        lambda v: "DILI" if v in POSITIVE_VALS else "NoDILI"
    )

configs = {
    "MCNC":    pd.concat([mc, nc]),
    "MCLCNC":  pd.concat([mc, lc, nc]),
    "all":     pd.concat([mc, lc, nc, sider]),
}

# ── hyperparameter grid ────────────────────────────────────────────────────
param_grid = {
    "n_estimators":      [100, 300],
    "max_depth":         [None, 10, 20],
    "min_samples_split": [2, 5],
    "min_samples_leaf":  [1, 2],
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# ── train / predict for each config ───────────────────────────────────────
for conf_name, subset in configs.items():
    subset = subset.copy().reset_index(drop=True)
    labels = make_label(subset)

    X = np.vstack(subset["standardised_smiles"].apply(smiles_to_fp).values)
    y = labels.values  # "DILI" / "NoDILI"

    rf = RandomForestClassifier(random_state=42, n_jobs=-1)
    gs = GridSearchCV(
        rf,
        param_grid,
        cv=cv,
        scoring="balanced_accuracy",
        n_jobs=-1,
        refit=True,
    )
    gs.fit(X, y)

    best_model = gs.best_estimator_

    preds = best_model.predict(X)

    out_df = pd.DataFrame({
        "standardised_smiles": subset["standardised_smiles"].values,
        "label": preds,
    })
    out_path = os.path.join(OUT_DIR, f"{conf_name}_RF.csv")
    out_df.to_csv(out_path, index=False)
    print(f"[{conf_name}] best params: {gs.best_params_}  saved → {out_path}")
