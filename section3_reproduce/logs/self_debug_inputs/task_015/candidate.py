"""
Ames mutagenicity prediction using RDKit Morgan fingerprints + Random Forest.
Outputs test set SMILES and positive-class probabilities to pred_results/aai_preds.csv.
"""

import os
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
TRAIN_CSV = "benchmark/datasets/ames/train.csv"
VAL_CSV   = "benchmark/datasets/ames/val.csv"
TEST_CSV  = "benchmark/datasets/ames/test.csv"
OUTPUT_DIR = "pred_results"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "aai_preds.csv")

# ------------------------------------------------------------------
# Featurization
# ------------------------------------------------------------------
def smiles_to_fp(smiles: str, radius: int = 2, n_bits: int = 2048):
    """Convert a SMILES string to a Morgan fingerprint bit vector."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return np.zeros(n_bits, dtype=np.float32)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    return np.array(fp, dtype=np.float32)


def featurize(df: pd.DataFrame):
    """Return (X, y) numpy arrays from a DataFrame with Drug and Y columns."""
    X = np.vstack(df["Drug"].apply(smiles_to_fp).values)
    y = df["Y"].values.astype(int)
    return X, y


# ------------------------------------------------------------------
# Load data
# ------------------------------------------------------------------
train_df = pd.read_csv(TRAIN_CSV)
val_df   = pd.read_csv(VAL_CSV)
test_df  = pd.read_csv(TEST_CSV)

# Combine train + val for final model training
combined_df = pd.concat([train_df, val_df], ignore_index=True)

X_train, y_train = featurize(combined_df)
X_test,  y_test  = featurize(test_df)

# ------------------------------------------------------------------
# Train
# ------------------------------------------------------------------
clf = RandomForestClassifier(
    n_estimators=500,
    max_depth=None,
    min_samples_leaf=1,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)
clf.fit(X_train, y_train)

# ------------------------------------------------------------------
# Predict
# ------------------------------------------------------------------
prob_positive = clf.predict_proba(X_test)[:, 1]  # P(mutagenic)

# ------------------------------------------------------------------
# Save results
# ------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

results = pd.DataFrame({
    "Drug":        test_df["Drug"].values,   # SMILES column
    "probability": prob_positive,
})
results.to_csv(OUTPUT_CSV, index=False)

print(f"Saved {len(results)} predictions to {OUTPUT_CSV}")
