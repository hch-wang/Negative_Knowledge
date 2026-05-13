"""
Eval for BKdV-T2: KdV single soliton.

Loads pred_results/kdv_T2.npy (shape (256,)) and checks:
- peak position within +/-0.5 of x=+3
- peak amplitude within +/-0.15 of 2.0
- mass conserved within 1% (initial mass = integral of 2*sech^2(x+5) ≈ 4.0)
"""
import numpy as np

def eval():
    pred_path = "pred_results/kdv_T2.npy"
    import os
    if not os.path.exists(pred_path):
        return 0, f"missing output: {pred_path}"
    v = np.load(pred_path)
    if v.shape != (256,):
        return 0, f"wrong shape: got {v.shape}, expected (256,)"
    if not np.all(np.isfinite(v)):
        n_nan = int(np.isnan(v).sum())
        return 0, f"non-finite: {n_nan} NaN/Inf (blow-up — likely explicit scheme on stiff dispersion)"

    L = 30.0; Nx = 256; dx = L / Nx
    x = -15 + dx * np.arange(Nx)
    peak_i = int(np.argmax(v))
    peak_x = float(x[peak_i])
    peak_amp = float(v[peak_i])
    mass = float(v.sum() * dx)
    # reference mass: integral of 2 sech^2(x+5) ≈ 4.0 (exact ∫_{-∞}^{∞} 2 sech² = 4)

    pos_ok = abs(peak_x - 3.0) < 0.5
    amp_ok = abs(peak_amp - 2.0) < 0.15
    mass_ok = abs(mass - 4.0) / 4.0 < 0.01

    diag = {"peak_x": peak_x, "peak_amp": peak_amp, "mass": mass,
            "pos_ok": pos_ok, "amp_ok": amp_ok, "mass_ok": mass_ok}

    if pos_ok and amp_ok and mass_ok:
        return 1, str(diag)

    # diagnose
    if peak_amp < 1.5:
        diag["diagnosis"] = "soliton amplitude decayed -- over-diffusive (implicit Euler too damping?)"
    elif peak_amp > 2.5:
        diag["diagnosis"] = "amplitude grew -- unstable / wrong sign of dispersion"
    elif not pos_ok:
        diag["diagnosis"] = f"soliton at wrong position (got x={peak_x:.2f}, want x=3.0). Wrong speed or numerical phase error"
    elif not mass_ok:
        diag["diagnosis"] = f"mass not conserved (got {mass:.3f}, want 4.0). Need conservative scheme"
    else:
        diag["diagnosis"] = "amplitude or position off threshold"
    return 0, str(diag)

if __name__ == "__main__":
    print(eval())
