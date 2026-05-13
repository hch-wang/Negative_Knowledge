"""
Phenomenon-based eval for Stage 2 Burgers-swept-KdV sub-tasks.

No closed-form solution exists. Checks based on physics observables:
- valid_exec: no NaN/Inf in (u, v)
- mass_drift_v: |mass(v_T) - mass(v_0)| / |mass(v_0)|
- amplitude_check: task-specific
- peak_count_check: task-specific
- boundedness: max(|u|, |v|) under threshold

Each task takes a (T, 2, Nx) array (time-series of u and v) OR (2, Nx) final state.
Returns (useful_result: bool, diag: dict).
"""
import numpy as np
import json
import sys
from scipy.signal import find_peaks


L = 30.0  # domain [-15, 15]
NX = 256
DX = L / NX
X = -15 + DX * np.arange(NX)


def _load_array(npy_path):
    a = np.load(npy_path)
    return a


def _normalize_shape(a):
    """Accept (2, Nx) final-state or (T_save, 2, Nx) snapshots. Always return (T_save, 2, Nx)."""
    if a.ndim == 2:
        return a[None, ...]
    return a


def _amp_and_peaks(v, threshold=0.5):
    """Count well-separated peaks of v with amplitude >= threshold."""
    peaks, props = find_peaks(v, height=threshold, distance=8)
    return peaks, props


def check_basic(snapshots, max_field=15.0):
    """Common diagnostics: finite-ness, mass drift, boundedness."""
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
    """T-A: Soliton stability in coupled BKdV with non-zero m IC.
    Useful = finite, mass drift < 8%, final state still has 1 dominant peak with amp >= 0.5*initial.
    """
    a = _normalize_shape(_load_array(pred_path))
    if a.shape[1:] != (2, NX):
        return False, {"error": f"wrong shape {a.shape}, expected (T_save, 2, {NX}) or (2, {NX})"}
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

    pks_T, _ = _amp_and_peaks(vT, threshold=0.5)
    d["n_dominant_peaks_vT"] = int(len(pks_T))

    useful = (
        d["mass_drift_rel"] < 0.08
        and d["amp_ratio"] >= 0.5
        and d["n_dominant_peaks_vT"] >= 1
    )
    d["useful"] = bool(useful)
    if not useful:
        reasons = []
        if d["mass_drift_rel"] >= 0.08: reasons.append(f"mass drift {d['mass_drift_rel']:.2%} >= 8%")
        if d["amp_ratio"] < 0.5: reasons.append(f"amp ratio {d['amp_ratio']:.2f} < 0.5")
        if d["n_dominant_peaks_vT"] < 1: reasons.append("no dominant peak in final v")
        d["reason"] = "; ".join(reasons)
    return useful, d


def eval_T_B(pred_path):
    """T-B: Gaussian -> soliton train.
    Useful = finite, mass drift < 8%, final state has >= 2 well-separated peaks with amp >= 0.8.
    """
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
    """T-C: Bore x soliton interaction.
    Useful = finite, bore (u) bounded, soliton (v) survived (max amplitude >= 0.5).
    Phase shift / refraction can't be auto-detected without a free-propagation comparison;
    we only check survival + boundedness.
    """
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
        and d["u_max"] < 5.0  # bore didn't blow up
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
        print("usage: phenomenon_checks.py <task_id> <pred_npy>")
        sys.exit(2)
    task_id, pred = sys.argv[1], sys.argv[2]
    useful, diag = EVALS[task_id](pred)
    print(json.dumps({"useful": useful, "diag": diag}, indent=2, default=float))
