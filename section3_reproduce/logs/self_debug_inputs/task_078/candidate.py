"""
Predict deltaTm for protein point mutations using the pucci dataset.
Pipeline: parse PDB chain-A sequences -> build mutant sequences -> featurize -> train MLP -> predict test set.
"""
import os
import re
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor

# ── constants ────────────────────────────────────────────────────────────────
DATA_DIR = "benchmark/datasets/pucci"
PDB_DIR  = os.path.join(DATA_DIR, "PDBs")
OUT_DIR  = "pred_results"
OUT_FILE = os.path.join(OUT_DIR, "pucci-proteins_test_pred.csv")

# Three-letter -> one-letter amino acid mapping
THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "MSE": "M",  # selenomethionine -> methionine
}

# 20 standard amino acids (alphabetical)
AA_ORDER = list("ACDEFGHIKLMNPQRSTVWY")
AA_INDEX = {aa: i for i, aa in enumerate(AA_ORDER)}

# ── helpers ───────────────────────────────────────────────────────────────────
def parse_chain_a_sequence(pdb_id: str):
    """Return dict {res_number: one_letter} for chain A from the PDB file."""
    path = os.path.join(PDB_DIR, f"{pdb_id.lower()}.pdb")
    seq = {}
    seen = set()
    try:
        with open(path) as fh:
            for line in fh:
                if not line.startswith("ATOM"):
                    continue
                chain = line[21]
                if chain != "A":
                    continue
                res3 = line[17:20].strip()
                try:
                    resn = int(line[22:26].strip())
                except ValueError:
                    continue
                aa1 = THREE_TO_ONE.get(res3)
                if aa1 and resn not in seen:
                    seen.add(resn)
                    seq[resn] = aa1
    except FileNotFoundError:
        pass
    return seq


def make_mutant_sequence(wt_seq: dict, resn: int, mut_aa1: str):
    """Apply a point mutation to the wild-type sequence dict and return list of aa."""
    seq = dict(wt_seq)
    if resn in seq:
        seq[resn] = mut_aa1
    return [seq[k] for k in sorted(seq.keys())]


def composition_features(seq_list):
    """20-dim amino acid composition vector."""
    arr = np.zeros(20)
    if not seq_list:
        return arr
    for aa in seq_list:
        if aa in AA_INDEX:
            arr[AA_INDEX[aa]] += 1
    arr /= len(seq_list)
    return arr


def build_features(df: pd.DataFrame, wt_seqs: dict):
    """
    Build feature matrix for every row in df.
    Features (per row):
      - 20 composition features of mutant sequence
      - Tmexp [wt]  (wild-type melting temperature)
      - sequence length
      - wild-type residue one-hot (20 dims)
      - mutant residue one-hot (20 dims)
    Total: 63 features
    """
    rows = []
    for _, row in df.iterrows():
        pdb_id  = str(row["PDBid"]).lower()
        resn    = int(row["RESN"])
        res_wt  = str(row["RESwt"]).strip()
        res_mut = str(row["RESmut"]).strip()
        tm_wt   = float(row["Tmexp [wt]"]) if not pd.isna(row["Tmexp [wt]"]) else 0.0

        wt_aa1  = THREE_TO_ONE.get(res_wt, "G")
        mut_aa1 = THREE_TO_ONE.get(res_mut, "G")

        wt_seq = wt_seqs.get(pdb_id, {})
        mut_seq_list = make_mutant_sequence(wt_seq, resn, mut_aa1)

        comp = composition_features(mut_seq_list)
        seq_len = len(mut_seq_list) if mut_seq_list else 100

        wt_oh  = np.zeros(20)
        mut_oh = np.zeros(20)
        if wt_aa1  in AA_INDEX: wt_oh [AA_INDEX[wt_aa1 ]] = 1.0
        if mut_aa1 in AA_INDEX: mut_oh[AA_INDEX[mut_aa1]] = 1.0

        feat = np.concatenate([comp, [tm_wt, seq_len], wt_oh, mut_oh])
        rows.append(feat)
    return np.array(rows, dtype=np.float32)


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Load CSVs
    train_df = pd.read_csv(os.path.join(DATA_DIR, "pucci-proteins_train.csv"), index_col=0)
    test_df  = pd.read_csv(os.path.join(DATA_DIR, "pucci-proteins_test.csv"),  index_col=0)
    dev_df   = pd.read_csv(os.path.join(DATA_DIR, "pucci-proteins_dev.csv"),   index_col=0)

    # Combine train + dev for fitting
    fit_df = pd.concat([train_df, dev_df], ignore_index=True)

    # Parse all needed PDB files once
    all_pdb_ids = set(fit_df["PDBid"].str.lower().unique()) | set(test_df["PDBid"].str.lower().unique())
    wt_seqs = {pid: parse_chain_a_sequence(pid) for pid in all_pdb_ids}

    # Build feature matrices
    X_train = build_features(fit_df,  wt_seqs)
    X_test  = build_features(test_df, wt_seqs)

    # Target: ΔTmexp column (may be named with unicode delta)
    target_col = None
    for col in fit_df.columns:
        if "Tm" in col and col.startswith("Δ"):
            target_col = col
            break
    if target_col is None:
        # Fallback: find column whose name starts with 'delta' or is exactly 'ΔTmexp'
        for col in fit_df.columns:
            low = col.lower()
            if "deltaTm" in col or ("Δ" in col and "exp" in col):
                target_col = col
                break
    if target_col is None:
        # Last resort: use 4th column after index
        target_col = fit_df.columns[3]

    y_train = fit_df[target_col].astype(float).values

    # Standardise features
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # MLP regressor
    model = MLPRegressor(
        hidden_layer_sizes=(256, 128, 64),
        activation="relu",
        solver="adam",
        max_iter=500,
        learning_rate_init=1e-3,
        early_stopping=True,
        validation_fraction=0.1,
        random_state=42,
        n_iter_no_change=20,
    )
    model.fit(X_train_s, y_train)

    # Predict and save
    preds = model.predict(X_test_s)
    out_df = pd.DataFrame({"deltaTm": preds})
    out_df.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(preds)} predictions to {OUT_FILE}")


if __name__ == "__main__":
    main()
