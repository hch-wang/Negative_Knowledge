"""
Physics-aware phenomenon eval v2 for Stage 2 BKdV sub-tasks.

Key changes vs v1 (`phenomenon_checks.py`):

- **T_A**: amp_ratio threshold lowered from 0.5 to 0.25 (matches BKdV-S7 deep
  synthesis quantitative prediction: sech² off-manifold IC at A=1.5 → -62.8%
  v_max decay over T=10; our T_A IC at A=2.0 with extra +0.2v perturbation
  decays similarly to ~0.32 ratio). Also adds an *explicit single-dominant-peak*
  check: n_peaks_above_0.4 == 1 OR dominance_ratio (top/second peak) > 1.5.
  This rejects chaotic fragmentation cases (e.g. 14 peaks each ~1.3) that the
  v1 eval mechanically passed because n_peaks >= 1.

- **T_B**: unchanged (v1 eval correctly distinguishes bank-aware with S6
  viscosity from non-bank-aware via u_max < 15 boundedness).

- **T_C**: unchanged (v1 eval correctly distinguishes via u_max < 5).
"""
import numpy as np
import json
import sys
from scipy.signal import find_peaks


L = 30.0
NX = 256
DX = L / NX
X = -15 + DX * np.arange(NX)


def _load_array(npy_path):
    a = np.load(npy_path)
    return a


def _normalize_shape(a):
    if a.ndim == 2:
        return a[None, ...]
    return a


def _amp_and_peaks(v, threshold=0.5):
    peaks, props = find_peaks(v, height=threshold, distance=8)
    return peaks, props


def check_basic(snapshots, max_field=15.0):
    diag = {}
    u_all = snapshots[:, 0, :]
    v_all = snapshots[:, 1, :]
    diag["all_finite"] = bool(np.isfinite(snapshots).all())
    if not diag["all_finite"]:
        diag["n_nan"] = int(np.isnan(snapshots).sum())
        return diag
    mass_v0 = float(v_all[0].sum() * DX)
    mass_vT = float(v_all[-1].sum() * DX)
    diag["mass_v0"] = mass_v0
    diag["mass_vT"] = mass_vT
    diag["mass_drift_rel"] = abs(mass_vT - mass_v0) / max(abs(mass_v0), 1e-12)
    diag["u_max"] = float(np.max(np.abs(u_all)))
    diag["v_max"] = float(np.max(np.abs(v_all)))
    diag["bounded"] = bool(diag["u_max"] < max_field and diag["v_max"] < max_field)
    return diag


def eval_T_A(pred_path):
    """T-A: Soliton stability under m=u-v²/2 perturbation.

    Physics-aware criteria (v2):
    - finite, bounded (max < 15)
    - mass drift < 8%
    - amp_ratio = vT_max / v0_max >= 0.25 (was 0.5; matches BKdV-S7 deep)
    - SINGLE dominant peak: n_peaks_above_0.4 == 1 OR dominance_ratio > 1.5
      (rejects chaotic fragmentation that v1 passed mechanically)
    """
    a = _normalize_shape(_load_array(pred_path))
    if a.shape[1:] != (2, NX):
        return False, {"error": f"wrong shape {a.shape}, expected (T_save, 2, {NX})"}
    d = check_basic(a)
    if not d["all_finite"] or not d["bounded"]:
        d["useful"] = False
        d["reason"] = "non-finite or unbounded"
        return False, d
    v0 = a[0, 1, :]; vT = a[-1, 1, :]
    v0_max = float(v0.max()); vT_max = float(vT.max())
    d["v0_max"] = v0_max
    d["vT_max"] = vT_max
    d["amp_ratio"] = vT_max / max(v0_max, 1e-12)

    # Peaks above lower 0.4 threshold (matches the new amp_ratio floor 0.25 × v0_max=2)
    pks_T, props = _amp_and_peaks(vT, threshold=0.4)
    d["n_peaks_above_0.4"] = int(len(pks_T))

    # Dominance ratio: top peak / second peak
    if len(pks_T) >= 1:
        heights = props['peak_heights']
        sorted_h = sorted(heights, reverse=True)
        d["top_peak"] = float(sorted_h[0])
        d["second_peak"] = float(sorted_h[1]) if len(sorted_h) > 1 else 0.0
        d["dominance_ratio"] = d["top_peak"] / max(d["second_peak"], 1e-6)
    else:
        d["top_peak"] = 0.0
        d["second_peak"] = 0.0
        d["dominance_ratio"] = 0.0

    is_single_dominant = (d["n_peaks_above_0.4"] == 1) or (d["dominance_ratio"] > 1.5)
    d["is_single_dominant"] = bool(is_single_dominant)

    useful = (
        d["mass_drift_rel"] < 0.08
        and d["amp_ratio"] >= 0.25
        and is_single_dominant
    )
    d["useful"] = bool(useful)
    if not useful:
        reasons = []
        if d["mass_drift_rel"] >= 0.08: reasons.append(f"mass drift {d['mass_drift_rel']:.2%} >= 8%")
        if d["amp_ratio"] < 0.25: reasons.append(f"amp ratio {d['amp_ratio']:.2f} < 0.25")
        if not is_single_dominant: reasons.append(f"not single dominant: {d['n_peaks_above_0.4']} peaks above 0.4, dominance ratio {d['dominance_ratio']:.2f}")
        d["reason"] = "; ".join(reasons)
    return useful, d


def eval_T_B(pred_path):
    """T-B: Gaussian → soliton train. (Unchanged from v1.)"""
    a = _normalize_shape(_load_array(pred_path))
    if a.shape[1:] != (2, NX):
        return False, {"error": f"wrong shape {a.shape}"}
    d = check_basic(a)
    if not d["all_finite"] or not d["bounded"]:
        d["useful"] = False
        d["reason"] = "non-finite or unbounded"
        return False, d
    v0 = a[0, 1, :]; vT = a[-1, 1, :]
    d["v0_max"] = float(v0.max()); d["vT_max"] = float(vT.max())
    pks_T, props = _amp_and_peaks(vT, threshold=0.8)
    d["n_dominant_peaks_vT"] = int(len(pks_T))
    if len(pks_T) >= 2:
        d["peak_separations"] = [int(pks_T[i+1] - pks_T[i]) for i in range(len(pks_T)-1)]
    useful = (
        d["mass_drift_rel"] < 0.08
        and d["n_dominant_peaks_vT"] >= 2
        and d["vT_max"] >= 0.8
    )
    d["useful"] = bool(useful)
    if not useful:
        reasons = []
        if d["mass_drift_rel"] >= 0.08: reasons.append(f"mass drift {d['mass_drift_rel']:.2%} >= 8%")
        if d["n_dominant_peaks_vT"] < 2: reasons.append(f"only {d['n_dominant_peaks_vT']} peaks (need >= 2)")
        if d["vT_max"] < 0.8: reasons.append(f"vT_max {d['vT_max']:.2f} < 0.8")
        d["reason"] = "; ".join(reasons)
    return useful, d


def eval_T_C(pred_path):
    """T-C: Bore × soliton. (Unchanged from v1.)"""
    a = _normalize_shape(_load_array(pred_path))
    if a.shape[1:] != (2, NX):
        return False, {"error": f"wrong shape {a.shape}"}
    d = check_basic(a, max_field=10.0)
    if not d["all_finite"] or not d["bounded"]:
        d["useful"] = False
        d["reason"] = "non-finite or unbounded"
        return False, d
    vT = a[-1, 1, :]
    d["vT_max"] = float(vT.max())
    d["vT_min"] = float(vT.min())
    pks_T, _ = _amp_and_peaks(vT, threshold=0.5)
    d["n_dominant_peaks_vT"] = int(len(pks_T))
    useful = (
        d["vT_max"] >= 0.5
        and d["n_dominant_peaks_vT"] >= 1
        and d["u_max"] < 5.0
    )
    d["useful"] = bool(useful)
    if not useful:
        reasons = []
        if d["vT_max"] < 0.5: reasons.append(f"vT_max {d['vT_max']:.2f} < 0.5 (soliton destroyed)")
        if d["n_dominant_peaks_vT"] < 1: reasons.append("no peak in final v")
        if d["u_max"] >= 5.0: reasons.append(f"u_max {d['u_max']:.2f} too large (bore blew up)")
        d["reason"] = "; ".join(reasons)
    return useful, d


EVALS = {"T_A": eval_T_A, "T_B": eval_T_B, "T_C": eval_T_C}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: phenomenon_checks_v2.py <task_id> <pred_npy>")
        sys.exit(2)
    task_id, pred = sys.argv[1], sys.argv[2]
    useful, diag = EVALS[task_id](pred)
    print(json.dumps({"useful": useful, "diag": diag}, indent=2, default=float))
