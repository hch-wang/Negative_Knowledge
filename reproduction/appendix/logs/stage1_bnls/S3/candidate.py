"""
S3 final candidate: focusing 1D NLS via Madelung-Psi split-step Fourier (Strang).

Equation (kappa=+1, no Burgers boost):
    i * Psi_t = -(1/2) * Psi_xx - kappa * |Psi|^2 * Psi
with Psi(x,0) = A * exp(-(x+5)^2 / 4.5) for A in {1.0, 1.5, 2.0, 2.5, 3.0}.

Method (best-working):
    Strang split-step Fourier: linear half-step in k-space, full nonlinear
    step in x-space (exact, since |Psi|^2 is conserved by the pure nonlinear
    flow), linear half-step in k-space.

Default discretization is the CONVERGED setting determined in E3:
    Nx = 1024, dt = 0.00025, L = 60.0 (dx ~ 0.058, ~6 grid points per
    fundamental-soliton FWHM at A=3.0).

This script does the full amplitude sweep in one execution and writes
named arrays for each A into pred_results/S3.npz. Diagnostics also saved
into pred_results/S3_diag.json.

Resolution lessons (see reasoning.md, F1/F2/F3):
    * At the prompt-default Nx=256, dt=0.001, L=30 the method NEVER fails
      (no NaN, mass conserved to 1e-13), but for A >= 2 the result is
      under-resolved: dx = 0.117 is comparable to the soliton FWHM (~1/A),
      so peak counts and peak heights are unreliable.
    * Doubling Nx (dx -> 0.058) changes both peak count and peak height for
      A >= 2 (e.g. at A = 2.5 the under-resolved baseline reports 3 peaks
      with linf=4.22, the converged hi-res reports 2 peaks with linf=2.74).
    * Domain size L (30 vs 60) matters less than dx for this IC at T=6
      because soliton groups travel only a few units in time T.
"""

from __future__ import annotations

import json
import os

import numpy as np
from scipy.signal import find_peaks


def build_grid(Nx: int, L: float):
    dx = L / Nx
    x = -L / 2.0 + dx * np.arange(Nx)
    k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
    return x, k, dx


def initial_condition(x: np.ndarray, A: float) -> np.ndarray:
    return A * np.exp(-((x + 5.0) ** 2) / 4.5) + 0.0j


def strang_step(Psi: np.ndarray, k: np.ndarray, dt: float, kappa: float = 1.0) -> np.ndarray:
    Psi_hat = np.fft.fft(Psi)
    Psi_hat *= np.exp(-1j * (k**2) * 0.5 * (dt * 0.5))
    Psi = np.fft.ifft(Psi_hat)
    Psi = Psi * np.exp(1j * kappa * np.abs(Psi) ** 2 * dt)
    Psi_hat = np.fft.fft(Psi)
    Psi_hat *= np.exp(-1j * (k**2) * 0.5 * (dt * 0.5))
    Psi = np.fft.ifft(Psi_hat)
    return Psi


def integrate(A: float, Nx: int, dt: float, T: float, L: float, kappa: float = 1.0):
    x, k, dx = build_grid(Nx, L)
    Psi = initial_condition(x, A)
    n_steps = int(round(T / dt))
    assert abs(n_steps * dt - T) < 1e-9

    n_log = 121
    log_every = max(1, n_steps // (n_log - 1))
    ts_log = [0.0]
    mass_log = [float(np.sum(np.abs(Psi) ** 2) * dx)]
    linf_log = [float(np.max(np.abs(Psi)))]
    mass0 = mass_log[0]
    nan_at = -1

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
    # Use a physical separation threshold of 0.3 (a few FWHMs at A~3) so
    # we count distinct solitons rather than discretization wiggles.
    min_sep_grid = max(1, int(0.3 / dx))
    peaks, props = find_peaks(intensity, height=height_thr, distance=min_sep_grid)
    peaks_25, _ = find_peaks(intensity, height=0.25 * intensity.max(), distance=min_sep_grid)

    diag = {
        "A": float(A),
        "Nx": int(Nx),
        "dt": float(dt),
        "T": float(T),
        "L": float(L),
        "kappa": float(kappa),
        "n_steps_target": int(n_steps),
        "nan_at_step": int(nan_at),
        "success": bool(nan_at < 0),
        "mass_init": float(mass0),
        "mass_final": float(mass_log[-1]) if nan_at < 0 else float("nan"),
        "mass_drift_abs": float(mass_log[-1] - mass0) if nan_at < 0 else float("nan"),
        "mass_drift_rel": float((mass_log[-1] - mass0) / mass0) if nan_at < 0 else float("nan"),
        "linf_init": float(linf_log[0]),
        "linf_final": float(linf_log[-1]) if nan_at < 0 else float("nan"),
        "linf_max_over_t": float(linf_log.max()) if nan_at < 0 else float("nan"),
        "spectral_tail_frac_final": tail_frac,
        "n_peaks_5pct": int(len(peaks)),
        "n_peaks_25pct": int(len(peaks_25)),
        "peak_x_5pct": x[peaks].tolist(),
        "peak_heights_5pct": props.get("peak_heights", np.array([])).tolist(),
        "peak_x_25pct": x[peaks_25].tolist(),
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


def karpman_maslov_predictions():
    out = {}
    for A in (1.0, 1.5, 2.0, 2.5, 3.0):
        # Prompt convention: N_sol ~ int(A * (sigma_eff) * sqrt(2)) with
        # sigma_eff = 1.5/sqrt(2) -> int(A * 1.5)
        a_prompt = int(np.floor(A * 1.5))
        # Standard KM (sigma=1.5 directly): floor(A*sigma*sqrt(2)) = floor(A*1.5*sqrt(2))
        b_std = int(np.floor(A * 1.5 * np.sqrt(2.0)))
        out[f"A={A}"] = {"km_prompt_convention": a_prompt, "km_standard_convention": b_std}
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "pred_results")
    os.makedirs(out_dir, exist_ok=True)

    # Best-working / converged config from E3
    Nx = 1024
    dt = 0.00025
    T = 6.0
    L = 60.0
    kappa = 1.0
    A_list = [1.0, 1.5, 2.0, 2.5, 3.0]

    results = {}
    per_A_diags = []

    for A in A_list:
        print(f"--- A = {A} ---", flush=True)
        r = integrate(A, Nx=Nx, dt=dt, T=T, L=L, kappa=kappa)
        d = r["diag"]
        per_A_diags.append(d)
        print(
            f"  success={d['success']} n_peaks_5%={d['n_peaks_5pct']} "
            f"n_peaks_25%={d['n_peaks_25pct']} linf_final={d['linf_final']:.4g} "
            f"linf_max={d['linf_max_over_t']:.4g} "
            f"mass_drift_rel={d['mass_drift_rel']:.3e} "
            f"tail_frac={d['spectral_tail_frac_final']:.3e}",
            flush=True,
        )
        results[f"final_A_{A:.1f}_x"] = r["x"]
        results[f"final_A_{A:.1f}_intensity_final"] = r["intensity_final"]
        results[f"final_A_{A:.1f}_Psi_final_real"] = r["Psi_final"].real
        results[f"final_A_{A:.1f}_Psi_final_imag"] = r["Psi_final"].imag
        results[f"final_A_{A:.1f}_ts"] = r["ts_log"]
        results[f"final_A_{A:.1f}_mass"] = r["mass_log"]
        results[f"final_A_{A:.1f}_linf"] = r["linf_log"]

    # Merge with existing S3.npz to keep all method comparison arrays
    out_npz = os.path.join(out_dir, "S3.npz")
    base = {}
    if os.path.exists(out_npz):
        with np.load(out_npz) as f:
            base = {k: f[k] for k in f.files}
    base.update(results)
    np.savez(out_npz, **base)
    print(f"Saved (merged) {out_npz}", flush=True)

    summary = {
        "config": dict(Nx=Nx, dt=dt, T=T, L=L, kappa=kappa),
        "A_list": A_list,
        "per_A": per_A_diags,
        "karpman_maslov_predictions": karpman_maslov_predictions(),
    }
    with open(os.path.join(out_dir, "S3_diag.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("Saved S3_diag.json")


if __name__ == "__main__":
    main()
