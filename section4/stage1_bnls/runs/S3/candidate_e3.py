"""
S3 Experiment 3: convergence check at high A.

At A=3.0, the L=60, Nx=512 run still has spectral tail fraction ~ 1.5e-3,
indicating under-resolution of the emitted narrow soliton (FWHM ~ 1/A ~ 0.33
vs dx = 60/512 ~ 0.117 — only ~3 grid points per FWHM). We re-run A=2.0, 2.5,
3.0 at Nx=1024 (dx ~ 0.058 -> ~6 points per FWHM) and dt=0.00025 on L=60.

Also include A=1.0 as a control (no surprise expected, but confirms agreement).
This is the same Madelung-Psi Strang split-step method, just resolution check.
"""

from __future__ import annotations

import json
import os

import numpy as np
from scipy.signal import find_peaks


def build_grid(Nx, L):
    dx = L / Nx
    x = -L / 2.0 + dx * np.arange(Nx)
    k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
    return x, k, dx


def initial_condition(x, A):
    return A * np.exp(-((x + 5.0) ** 2) / 4.5) + 0.0j


def strang_step(Psi, k, dt, kappa=1.0):
    Psi_hat = np.fft.fft(Psi)
    Psi_hat *= np.exp(-1j * (k**2) * 0.5 * (dt * 0.5))
    Psi = np.fft.ifft(Psi_hat)
    Psi = Psi * np.exp(1j * kappa * np.abs(Psi) ** 2 * dt)
    Psi_hat = np.fft.fft(Psi)
    Psi_hat *= np.exp(-1j * (k**2) * 0.5 * (dt * 0.5))
    Psi = np.fft.ifft(Psi_hat)
    return Psi


def integrate(A, Nx, dt, T, L, kappa=1.0):
    x, k, dx = build_grid(Nx, L)
    Psi = initial_condition(x, A)
    n_steps = int(round(T / dt))
    n_log = 121
    log_every = max(1, n_steps // (n_log - 1))
    ts_log = [0.0]
    mass_log = [float(np.sum(np.abs(Psi) ** 2) * dx)]
    linf_log = [float(np.max(np.abs(Psi)))]
    nan_at = -1
    mass0 = mass_log[0]
    for n in range(1, n_steps + 1):
        Psi = strang_step(Psi, k, dt, kappa=kappa)
        if not np.all(np.isfinite(Psi)):
            nan_at = n
            break
        if n % log_every == 0 or n == n_steps:
            ts_log.append(n * dt)
            mass_log.append(float(np.sum(np.abs(Psi) ** 2) * dx))
            linf_log.append(float(np.max(np.abs(Psi))))

    ts_log = np.asarray(ts_log)
    mass_log = np.asarray(mass_log)
    linf_log = np.asarray(linf_log)

    Psi_hat = np.fft.fft(Psi)
    Pk = np.abs(Psi_hat) ** 2
    total = float(np.sum(Pk))
    k_abs = np.abs(k)
    mask = k_abs > (k_abs.max() * 0.5)
    tail_frac = float(np.sum(Pk[mask]) / total) if total > 0 else float("nan")

    intensity = np.abs(Psi) ** 2
    height_thr = 0.05 * intensity.max() if intensity.max() > 0 else 0.0
    peaks, props = find_peaks(intensity, height=height_thr, distance=int(0.3 / dx))
    peaks_robust, _ = find_peaks(intensity, height=0.25 * intensity.max(), distance=int(0.3 / dx))

    diag = {
        "A": float(A),
        "Nx": int(Nx),
        "dt": float(dt),
        "T": float(T),
        "L": float(L),
        "kappa": float(kappa),
        "nan_at_step": int(nan_at),
        "success": bool(nan_at < 0),
        "mass_init": float(mass0),
        "mass_final": float(mass_log[-1]) if nan_at < 0 else float("nan"),
        "mass_drift_rel": float((mass_log[-1] - mass0) / mass0) if nan_at < 0 else float("nan"),
        "linf_init": float(linf_log[0]),
        "linf_final": float(linf_log[-1]) if nan_at < 0 else float("nan"),
        "linf_max_over_t": float(linf_log.max()) if nan_at < 0 else float("nan"),
        "spectral_tail_frac_final": tail_frac,
        "n_peaks_5pct": int(len(peaks)),
        "n_peaks_25pct": int(len(peaks_robust)),
        "peak_x_5pct": x[peaks].tolist(),
        "peak_heights_5pct": props.get("peak_heights", np.array([])).tolist(),
        "peak_x_25pct": x[peaks_robust].tolist(),
    }
    return {
        "x": x,
        "Psi_final": Psi,
        "intensity_final": intensity,
        "ts_log": ts_log,
        "mass_log": mass_log,
        "linf_log": linf_log,
        "diag": diag,
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "pred_results")
    os.makedirs(out_dir, exist_ok=True)

    T = 6.0
    kappa = 1.0
    tag = "hires_Nx1024_dt2.5e-4_L60"
    cfg = dict(Nx=1024, dt=0.00025, L=60.0)
    A_list = [1.0, 1.5, 2.0, 2.5, 3.0]

    diags = []
    arrays = {}
    for A in A_list:
        r = integrate(A, T=T, kappa=kappa, **cfg)
        d = r["diag"]
        d["config"] = tag
        diags.append(d)
        print(
            f"[{tag}] A={A} ok={d['success']} "
            f"peaks5%={d['n_peaks_5pct']} peaks25%={d['n_peaks_25pct']} "
            f"linf_final={d['linf_final']:.4g} "
            f"linf_max={d['linf_max_over_t']:.4g} "
            f"mass_drift_rel={d['mass_drift_rel']:.2e} "
            f"tail_frac={d['spectral_tail_frac_final']:.2e}",
            flush=True,
        )
        if A in (1.0, 2.0, 3.0):
            print(f"   peak_x_5%={d['peak_x_5pct']}", flush=True)
            print(f"   peak_h_5%={d['peak_heights_5pct']}", flush=True)
        key = f"{tag}_A_{A:.1f}"
        arrays[f"{key}_x"] = r["x"]
        arrays[f"{key}_intensity_final"] = r["intensity_final"]
        arrays[f"{key}_ts"] = r["ts_log"]
        arrays[f"{key}_linf"] = r["linf_log"]
        arrays[f"{key}_mass"] = r["mass_log"]

    base_path = os.path.join(out_dir, "S3.npz")
    base = {}
    if os.path.exists(base_path):
        with np.load(base_path) as f:
            base = {k: f[k] for k in f.files}
    base.update(arrays)
    np.savez(base_path, **base)
    print(f"Saved (merged) {base_path}")

    with open(os.path.join(out_dir, "S3_diag_e3.json"), "w") as f:
        json.dump(diags, f, indent=2)
    print("Saved S3_diag_e3.json")


if __name__ == "__main__":
    main()
