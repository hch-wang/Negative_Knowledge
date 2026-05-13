"""
Eval for BKdV-T1: Inviscid Burgers shock.

Loads pred_results/burgers_T05.npy (shape (200,)), compares to reference,
returns (pass:int, message:str).
"""
import numpy as np
import os

def eval():
    pred_path = "pred_results/burgers_T05.npy"
    ref_path = "${PROJECT_ROOT}/ref_results/burgers_T05_REF.npy"
    if not os.path.exists(pred_path):
        return 0, f"missing output: {pred_path}"
    pred = np.load(pred_path)
    if pred.shape != (200,):
        return 0, f"wrong shape: got {pred.shape}, expected (200,)"
    if not np.all(np.isfinite(pred)):
        n_nan = int(np.isnan(pred).sum())
        n_inf = int(np.isinf(pred).sum())
        return 0, f"non-finite values: {n_nan} NaN, {n_inf} Inf (numerical blow-up)"

    ref = np.load(ref_path)
    L1 = float(np.abs(pred - ref).mean())
    Linf = float(np.abs(pred - ref).max())
    # detect oscillations: jumps between adjacent cells beyond what reference has
    pred_max_jump = float(np.abs(np.diff(pred)).max())
    ref_max_jump = float(np.abs(np.diff(ref)).max())
    diag = {"L1": L1, "Linf": Linf, "pred_max_jump": pred_max_jump, "ref_max_jump": ref_max_jump,
            "pred_max": float(pred.max()), "pred_min": float(pred.min())}

    if L1 < 0.10:
        return 1, str(diag)
    # diagnose failure mode
    if pred_max_jump > 3 * ref_max_jump:
        diag["diagnosis"] = "oscillations near shock (Gibbs-like; need TVD/limiter)"
    elif pred.max() < 0.6 or pred.min() > -0.6:
        diag["diagnosis"] = "shock smeared / amplitude lost (too diffusive)"
    else:
        diag["diagnosis"] = f"L1={L1:.3f} > 0.10 threshold; shape disagrees with reference"
    return 0, str(diag)

if __name__ == "__main__":
    print(eval())
