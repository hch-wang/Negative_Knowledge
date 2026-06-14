"""
ScienceAgentBench task_067 — CogSci pattern similarity
Compute cosine similarity between each cognitive model's prediction vector
and the pre-computed high-conscientiousness / high-openness W patterns.
"""

import os
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# ── paths ──────────────────────────────────────────────────────────────────
BASE = "benchmark/datasets/CogSci_pattern_high_sim_data"
OUT_DIR = "pred_results"
OUT_FILE = os.path.join(OUT_DIR, "CogSci_pattern_high_sim_data_pred.csv")

# ── load personality-trait W patterns ─────────────────────────────────────
W_conscientiousness = np.load(
    os.path.join(BASE, "fit_result_conscientiousness_W_high.npy")
)
W_openness = np.load(
    os.path.join(BASE, "fit_result_openness_W_high.npy")
)

# Flatten to 1-D reference vectors (one pattern per trait)
ref_con = W_conscientiousness.flatten()
ref_open = W_openness.flatten()

# ── cognitive-model CSV files ──────────────────────────────────────────────
MODEL_FILES = {
    "Atmosphere":   os.path.join(BASE, "Atmosphere.csv"),
    "Conversion":   os.path.join(BASE, "Conversion.csv"),
    "Matching":     os.path.join(BASE, "Matching.csv"),
    "MMT":          os.path.join(BASE, "MMT.csv"),
    "PHM":          os.path.join(BASE, "PHM.csv"),
    "PSYCOP":       os.path.join(BASE, "PSYCOP.csv"),
    "VerbalModels": os.path.join(BASE, "VerbalModels.csv"),
}

# ── helper: build a binary response vector from a model CSV ───────────────
def build_vector(csv_path: str, response_set: list[str]) -> np.ndarray:
    """
    Each row has a 'Prediction' column with semicolon-separated responses.
    We concatenate all responses across all syllogisms into a multi-hot
    vector over the universal response vocabulary.
    """
    df = pd.read_csv(csv_path)
    counts = {r: 0 for r in response_set}
    for pred_str in df["Prediction"].dropna():
        for resp in pred_str.split(";"):
            resp = resp.strip()
            if resp in counts:
                counts[resp] += 1
    return np.array([counts[r] for r in response_set], dtype=float)

# ── collect all unique responses to form the vocabulary ───────────────────
all_responses: set[str] = set()
for path in MODEL_FILES.values():
    df = pd.read_csv(path)
    for pred_str in df["Prediction"].dropna():
        for resp in pred_str.split(";"):
            all_responses.add(resp.strip())

response_vocab = sorted(all_responses)

# ── build model vectors & compute similarities ────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)

records = []
for model_name, csv_path in MODEL_FILES.items():
    vec = build_vector(csv_path, response_vocab)

    # cosine_similarity expects 2-D arrays
    sim_con = cosine_similarity(vec.reshape(1, -1), ref_con.reshape(1, -1))[0, 0]
    sim_open = cosine_similarity(vec.reshape(1, -1), ref_open.reshape(1, -1))[0, 0]

    records.append({
        "model":            model_name,
        "conscientiousness": float(sim_con),
        "openness":          float(sim_open),
    })

results_df = pd.DataFrame(records).set_index("model")
results_df.to_csv(OUT_FILE)
print(f"Saved similarity scores to {OUT_FILE}")
print(results_df)
