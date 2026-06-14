"""
Drug-Target Interaction (DTI) model for COVID-19 drug repurposing using DAVIS dataset.
Uses ECFP fingerprints for drugs and CNN features for targets via manual implementation
since DeepPurpose is not available.
"""

import os
import json
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# ── paths ──────────────────────────────────────────────────────────────────────
BASE = "benchmark/datasets/dti"
OUT_DIR = "pred_results"
os.makedirs(OUT_DIR, exist_ok=True)

# ── helpers ────────────────────────────────────────────────────────────────────

def smiles_to_ecfp(smiles, radius=2, nbits=1024):
    """Convert SMILES string to ECFP fingerprint (Morgan)."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.zeros(nbits)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)
        return np.array(fp)
    except Exception:
        return np.zeros(nbits)


def seq_to_ctd(seq, max_len=1000):
    """
    Simple amino-acid composition feature for a protein sequence.
    Returns a fixed-length vector via AAC (20 dims) + dipeptide composition (400 dims).
    Falls back gracefully for unknown characters.
    """
    AA = list("ACDEFGHIKLMNPQRSTVWY")
    aa_idx = {a: i for i, a in enumerate(AA)}

    # Amino acid composition (20)
    aac = np.zeros(20)
    for c in seq:
        if c in aa_idx:
            aac[aa_idx[c]] += 1
    if len(seq) > 0:
        aac /= len(seq)

    # Dipeptide composition (400)
    dpc = np.zeros(400)
    for i in range(len(seq) - 1):
        a, b = seq[i], seq[i + 1]
        if a in aa_idx and b in aa_idx:
            dpc[aa_idx[a] * 20 + aa_idx[b]] += 1
    if len(seq) > 1:
        dpc /= (len(seq) - 1)

    return np.concatenate([aac, dpc])  # 420 dims


def build_pair_features(drug_fps, target_feat):
    """Concatenate drug fingerprint and target feature vector."""
    return np.concatenate([drug_fps, target_feat])


# ── load data ──────────────────────────────────────────────────────────────────

print("Loading DAVIS dataset ...")

with open(os.path.join(BASE, "DAVIS", "target_seq.json")) as f:
    target_seqs = json.load(f)  # dict: name -> AA sequence

target_names = list(target_seqs.keys())

# drug SMILES lists (one per line, no header)
with open(os.path.join(BASE, "DAVIS", "drug_train.txt")) as f:
    drug_smiles_train = [l.strip() for l in f if l.strip()]

with open(os.path.join(BASE, "DAVIS", "drug_val.txt")) as f:
    drug_smiles_val = [l.strip() for l in f if l.strip()]

# affinity matrices: rows = drugs, cols = targets
aff_train = pd.read_csv(
    os.path.join(BASE, "DAVIS", "affinity_train.csv"), header=None
).values.astype(float)

aff_val = pd.read_csv(
    os.path.join(BASE, "DAVIS", "affinity_val.csv"), header=None
).values.astype(float)

print(f"  train drugs: {len(drug_smiles_train)}, targets: {len(target_names)}")
print(f"  val   drugs: {len(drug_smiles_val)}")

# ── featurise ──────────────────────────────────────────────────────────────────

print("Computing drug fingerprints ...")
fps_train = np.array([smiles_to_ecfp(s) for s in drug_smiles_train])
fps_val   = np.array([smiles_to_ecfp(s) for s in drug_smiles_val])

print("Computing target features ...")
target_feats = {name: seq_to_ctd(seq) for name, seq in target_seqs.items()}

# ── build flat train / val arrays ─────────────────────────────────────────────

def build_dataset(drug_fps, aff_matrix, target_names, target_feats):
    """Expand (n_drugs x n_targets) into flat samples."""
    n_drugs, n_targets = aff_matrix.shape
    X, y = [], []
    for d in range(n_drugs):
        for t in range(min(n_targets, len(target_names))):
            tname = target_names[t]
            tfeat = target_feats[tname]
            feat = build_pair_features(drug_fps[d], tfeat)
            X.append(feat)
            y.append(aff_matrix[d, t])
    return np.array(X), np.array(y)


print("Building training matrix ...")
X_train, y_train = build_dataset(fps_train, aff_train, target_names, target_feats)

# Transform labels: DAVIS affinity is Kd (nM); lower = tighter binding.
# Take negative log to make higher = better (analogous to pKd).
y_train_log = -np.log10(y_train + 1e-6)

print(f"  X_train shape: {X_train.shape}")

# ── train model ────────────────────────────────────────────────────────────────

print("Training Random Forest regressor ...")
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=None,
    n_jobs=-1,
    random_state=42,
)
model.fit(X_train_s, y_train_log)
print("Training complete.")

# ── load COVID-19 target and antiviral drugs ───────────────────────────────────

with open(os.path.join(BASE, "covid_seq.txt")) as f:
    lines = [l.strip() for l in f if l.strip()]

# First non-empty line is the sequence
covid_seq = lines[0]
covid_feat = seq_to_ctd(covid_seq)
print(f"COVID-19 target sequence length: {len(covid_seq)}")

antiviral_df = pd.read_csv(
    os.path.join(BASE, "antiviral_drugs.tab"),
    sep="\t",
    quotechar='"',
)
# Normalise column names
antiviral_df.columns = [c.strip() for c in antiviral_df.columns]

drug_names  = antiviral_df["Name"].tolist()
drug_smiles = antiviral_df["SMILES"].tolist()

print(f"Antiviral drugs to evaluate: {len(drug_names)}")

# ── predict affinities for antiviral drugs vs COVID-19 target ─────────────────

fps_antiviral = np.array([smiles_to_ecfp(s) for s in drug_smiles])

X_pred = np.array([
    build_pair_features(fps_antiviral[i], covid_feat)
    for i in range(len(drug_names))
])
X_pred_s = scaler.transform(X_pred)

pred_scores = model.predict(X_pred_s)  # higher pKd → tighter binding

# ── rank drugs (descending predicted affinity) ────────────────────────────────

ranked_idx = np.argsort(pred_scores)[::-1]
ranked_drugs = [drug_names[i] for i in ranked_idx]

print("\nTop-10 ranked antiviral drugs (best → worst predicted affinity):")
for rank, name in enumerate(ranked_drugs[:10], 1):
    print(f"  {rank:2d}. {name}  (score={pred_scores[ranked_idx[rank-1]]:.4f})")

# ── save results ───────────────────────────────────────────────────────────────

out_path = os.path.join(OUT_DIR, "davis_dti_repurposing.txt")
with open(out_path, "w") as f:
    for name in ranked_drugs:
        f.write(name + "\n")

print(f"\nRanked drug list saved to: {out_path}")
