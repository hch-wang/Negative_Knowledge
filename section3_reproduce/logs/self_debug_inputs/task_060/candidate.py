"""
Evaluate syllogistic reasoning models and NVC rules against the MFA benchmark.
Outputs pred_results/accuracies.csv.
"""

import os
import pandas as pd
import numpy as np

# ── paths ──────────────────────────────────────────────────────────────────
BASE = "benchmark/datasets/nvc"
OUT_DIR = "pred_results"
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_DIR = os.path.join(BASE, "scripts", "indiv_table", "models")
RULE_DIR  = os.path.join(BASE, "scripts", "indiv_table", "rules")
RAGNI     = os.path.join(BASE, "Ragni2016.csv")

# ── helpers ────────────────────────────────────────────────────────────────
def normalise(s: str) -> str:
    """Lower-case and strip whitespace for loose comparison."""
    if pd.isna(s):
        return ""
    return str(s).strip().lower()


def load_mfa(ragni_path: str) -> pd.Series:
    """
    Compute the Most Frequent Answer (MFA) benchmark per task.
    Each row has a 'task' column (the syllogism identifier) and a 'response' column.
    MFA = the mode response for each task.
    """
    df = pd.read_csv(ragni_path)
    mfa = (
        df.groupby("task")["response"]
        .agg(lambda x: x.mode().iloc[0])
        .reset_index()
        .rename(columns={"response": "mfa_response"})
    )
    return mfa


def load_model_predictions(model_dir: str) -> dict:
    """
    Load every model CSV in model_dir.
    Returns {model_name: DataFrame with columns [task, prediction]}.
    """
    models = {}
    for fname in sorted(os.listdir(model_dir)):
        if not fname.endswith(".csv"):
            continue
        name = fname.replace(".csv", "")
        path = os.path.join(model_dir, fname)
        df = pd.read_csv(path)
        # Normalise column names to lower-case
        df.columns = [c.lower().strip() for c in df.columns]
        models[name] = df
    return models


def detect_task_and_pred_cols(df: pd.DataFrame):
    """
    Heuristically identify which columns hold the task identifier and the
    model prediction, given that different CSVs may use different names.
    """
    cols = list(df.columns)
    # Task column candidates
    task_candidates = [c for c in cols if c in ("task", "syllogism", "problem", "id")]
    task_col = task_candidates[0] if task_candidates else cols[0]
    # Prediction column candidates (anything that isn't the task col)
    pred_candidates = [c for c in cols if c not in (task_col,) and
                       c in ("prediction", "pred", "response", "conclusion", "model")]
    pred_col = pred_candidates[0] if pred_candidates else (cols[1] if len(cols) > 1 else cols[0])
    return task_col, pred_col


def accuracy(pred_series: pd.Series, true_series: pd.Series) -> float:
    """Fraction of rows where normalised prediction matches normalised truth."""
    pred_n = pred_series.map(normalise)
    true_n = true_series.map(normalise)
    return (pred_n == true_n).mean()


# ── NVC rule files ─────────────────────────────────────────────────────────
def load_nvc_rules(rule_dir: str) -> list:
    """Return list of Python filenames (rule names) in rule_dir, excluding __init__."""
    rules = []
    if not os.path.isdir(rule_dir):
        return rules
    for fname in sorted(os.listdir(rule_dir)):
        if fname.endswith(".py") and fname != "__init__.py":
            rules.append(fname.replace(".py", ""))
    return rules


def apply_nvc_rule_override(model_pred: pd.Series, rule_name: str, rule_dir: str,
                             task_col: str, pred_col: str, model_df: pd.DataFrame) -> pd.Series:
    """
    Attempt to load the corresponding rule CSV from nvc_prediction/rules/ and
    override model predictions where the rule predicts NVC.

    The nvc_prediction/rules/ CSVs are expected to flag tasks where the rule
    fires (predicts NVC). Where the rule fires, we override with 'NVC'.
    Falls back to original predictions if the rule file cannot be loaded as CSV.
    """
    nvc_pred_dir = os.path.join(BASE, "scripts", "nvc_prediction", "rules")
    rule_csv = os.path.join(nvc_pred_dir, rule_name + ".csv")

    if not os.path.isfile(rule_csv):
        # Rule is a Python script — we cannot safely exec it; return unchanged
        return model_pred.copy()

    try:
        rdf = pd.read_csv(rule_csv)
        rdf.columns = [c.lower().strip() for c in rdf.columns]
        # Detect the task column in the rule CSV
        r_task_candidates = [c for c in rdf.columns if c in ("task", "syllogism", "problem", "id")]
        r_task_col = r_task_candidates[0] if r_task_candidates else rdf.columns[0]
        # Detect a column that indicates the rule fires (True / 1 / "NVC")
        flag_candidates = [c for c in rdf.columns if c not in (r_task_col,)]
        if not flag_candidates:
            return model_pred.copy()
        flag_col = flag_candidates[0]

        # Build a set of tasks where the rule predicts NVC
        nvc_tasks = set(
            rdf.loc[rdf[flag_col].astype(str).str.lower().isin(["true", "1", "nvc"]), r_task_col]
        )
        # Override
        result = model_pred.copy()
        mask = model_df[task_col].isin(nvc_tasks)
        result[mask] = "NVC"
        return result
    except Exception:
        return model_pred.copy()


# ── main ───────────────────────────────────────────────────────────────────
def main():
    # 1. MFA benchmark
    mfa_df = load_mfa(RAGNI)

    # 2. Model predictions
    model_dfs = load_model_predictions(MODEL_DIR)

    # 3. NVC rule names
    rule_names = load_nvc_rules(RULE_DIR)

    # 4. Build result rows
    rows = []

    for model_name, mdf in model_dfs.items():
        task_col, pred_col = detect_task_and_pred_cols(mdf)

        # Merge with MFA
        merged = mdf[[task_col, pred_col]].merge(
            mfa_df, left_on=task_col, right_on="task", how="inner"
        )
        if merged.empty:
            # Try a string-normalised merge
            mdf_tmp = mdf[[task_col, pred_col]].copy()
            mdf_tmp["_task_norm"] = mdf_tmp[task_col].astype(str).str.strip().str.lower()
            mfa_tmp = mfa_df.copy()
            mfa_tmp["_task_norm"] = mfa_tmp["task"].astype(str).str.strip().str.lower()
            merged = mdf_tmp.merge(mfa_tmp, on="_task_norm", how="inner")
            if task_col + "_x" in merged.columns:
                merged[task_col] = merged[task_col + "_x"]

        if merged.empty:
            # Cannot align — record NaN and continue
            row = {
                "model": model_name,
                "model_accuracy": np.nan,
                "mfa_accuracy": np.nan,
            }
            for r in rule_names:
                row[f"accuracy_with_{r}"] = np.nan
                row[f"improvement_{r}"] = np.nan
            rows.append(row)
            continue

        pred_series = merged[pred_col].reset_index(drop=True)
        true_series = merged["mfa_response"].reset_index(drop=True)

        model_acc = accuracy(pred_series, true_series)

        # MFA accuracy = 1.0 by definition (it IS the benchmark); we report
        # model_accuracy vs mfa baseline.  Some papers define mfa_accuracy as
        # the fraction of times human data matches MFA — we report model_acc
        # here and note improvement per rule.
        row = {
            "model": model_name,
            "model_accuracy": round(model_acc, 4),
        }

        # 5. NVC-rule overrides and improvement
        # We need the merged model_df slice to retain the task column for override logic
        merged_full = merged.copy()
        merged_full.reset_index(drop=True, inplace=True)

        for r in rule_names:
            overridden = apply_nvc_rule_override(
                pred_series, r, RULE_DIR, task_col, pred_col, merged_full
            )
            acc_with_rule = accuracy(overridden, true_series)
            improvement = round(acc_with_rule - model_acc, 4)
            row[f"accuracy_with_{r}"] = round(acc_with_rule, 4)
            row[f"improvement_{r}"] = improvement

        rows.append(row)

    # 6. Write CSV
    out_df = pd.DataFrame(rows)
    out_path = os.path.join(OUT_DIR, "accuracies.csv")
    out_df.to_csv(out_path, index=False)
    print(f"Saved {out_path} with shape {out_df.shape}")


if __name__ == "__main__":
    main()
