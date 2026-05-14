"""
S1 candidate solver: NLS focusing bright soliton.

System under test: i*Psi_t + (1/2)*Psi_xx + kappa*|Psi|^2*Psi = 0  (focusing, kappa=+1)
This is the standard NLS reached from the B-NLS system with u=0 via the
Madelung transform Psi = sqrt(N)*exp(i*phi). The IC + ground truth in
meta.json (peak amplitude 2 preserved, peak translates at speed 0.25,
mass = 2*sqrt(2) conserved) are consistent with exactly this convention.

Methods compared (3 Experiments in one driver):
  E1  Strang split-step Fourier on Psi  (sweep dt, Nx)         -- primary
  E2  Lie (first-order) split-step Fourier on Psi              -- order check
  E3  ETD-RK1 (exponential Euler) in Fourier on Psi            -- different family

Output: pred_results/S1.npz with named arrays for every (method, dt, Nx) we ran.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "pred_results"
OUT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------ problem
X_MIN, X_MAX = -15.0, 15.0
T_FINAL = 8.0
KAPPA = 1.0           # focusing
A = np.sqrt(2.0)      # soliton amplitude
V = 0.25              # group velocity for Psi (= v/2 of the prompt)
X0 = -5.0


def initial_psi(x: np.ndarray) -> np.ndarray:
    """Psi(x,0) = sqrt(2)*sech(sqrt(2)*(x+5))*exp(i*0.25*x)."""
    return A / np.cosh(A * (x - X0)) * np.exp(1j * V * x)


def exact_psi(x: np.ndarray, t: float) -> np.ndarray:
    """Exact NLS bright soliton for i*Psi_t + (1/2)*Psi_xx + |Psi|^2*Psi = 0.

    Psi = A*sech(A*(x - v*t - x0))*exp(i*(v*x - (v^2 - A^2)/2 * t)).
    """
    envelope = A / np.cosh(A * (x - V * t - X0))
    phase = V * x - 0.5 * (V * V - A * A) * t
    return envelope * np.exp(1j * phase)


# ------------------------------------------------------------------ helpers
def make_grid(Nx: int):
    dx = (X_MAX - X_MIN) / Nx
    x = X_MIN + dx * np.arange(Nx)
    k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
    return x, k, dx


def mass(Psi: np.ndarray, dx: float) -> float:
    return float(np.sum(np.abs(Psi) ** 2) * dx)


def energy(Psi: np.ndarray, k: np.ndarray, dx: float, kappa: float = KAPPA) -> float:
    """H = integral [ (1/2)|Psi_x|^2 - (kappa/2)|Psi|^4 ] dx (focusing, conserved)."""
    Psi_k = np.fft.fft(Psi)
    Psi_x = np.fft.ifft(1j * k * Psi_k)
    kinetic = 0.5 * np.sum(np.abs(Psi_x) ** 2) * dx
    pot = 0.5 * kappa * np.sum(np.abs(Psi) ** 4) * dx
    return float(kinetic - pot)


def peak_amplitude(Psi: np.ndarray) -> float:
    return float(np.max(np.abs(Psi)))


def peak_position(x: np.ndarray, Psi: np.ndarray) -> float:
    """Parabolic interpolation around argmax of |Psi|^2 for sub-grid accuracy."""
    a = np.abs(Psi) ** 2
    i = int(np.argmax(a))
    Nx = len(x)
    im = (i - 1) % Nx
    ip = (i + 1) % Nx
    y0, y1, y2 = a[im], a[i], a[ip]
    denom = (y0 - 2.0 * y1 + y2)
    if abs(denom) < 1e-30:
        delta = 0.0
    else:
        delta = 0.5 * (y0 - y2) / denom
    dx = x[1] - x[0]
    return float(x[i] + delta * dx)


def phase_winding(Psi: np.ndarray, dx: float, mask_thresh: float = 1e-3) -> float:
    """Unwrap phase where |Psi| > mask_thresh * max|Psi|, then return total phase change across the supported region."""
    amp = np.abs(Psi)
    mask = amp > mask_thresh * amp.max()
    if not mask.any():
        return float("nan")
    ph = np.angle(Psi)
    ph_m = np.unwrap(ph[mask])
    return float(ph_m[-1] - ph_m[0])


# ------------------------------------------------------------------ solvers
def step_strang(Psi: np.ndarray, k: np.ndarray, dt: float, kappa: float = KAPPA) -> np.ndarray:
    """Strang split-step Fourier:
        N(dt/2) -> L(dt) -> N(dt/2)
    Nonlinear step exact in physical space (preserves |Psi|^2):
        Psi <- Psi * exp(i * kappa * |Psi|^2 * dt)
    Linear step exact in Fourier space for i*Psi_t = -(1/2)*Psi_xx:
        Psi_k <- exp(-i * (1/2) * k^2 * dt) * Psi_k
    Hence linear propagator multiplier: exp(-i * 0.5 * k^2 * dt).
    """
    # N(dt/2)
    Psi = Psi * np.exp(1j * kappa * np.abs(Psi) ** 2 * (0.5 * dt))
    # L(dt)
    Psi_k = np.fft.fft(Psi)
    Psi_k *= np.exp(-1j * 0.5 * k * k * dt)
    Psi = np.fft.ifft(Psi_k)
    # N(dt/2)
    Psi = Psi * np.exp(1j * kappa * np.abs(Psi) ** 2 * (0.5 * dt))
    return Psi


def step_lie(Psi: np.ndarray, k: np.ndarray, dt: float, kappa: float = KAPPA) -> np.ndarray:
    """Lie (first-order) splitting: L(dt) o N(dt)."""
    Psi = Psi * np.exp(1j * kappa * np.abs(Psi) ** 2 * dt)
    Psi_k = np.fft.fft(Psi)
    Psi_k *= np.exp(-1j * 0.5 * k * k * dt)
    return np.fft.ifft(Psi_k)


def step_etdrk1(Psi: np.ndarray, k: np.ndarray, dt: float, kappa: float = KAPPA) -> np.ndarray:
    """ETD-RK1 (exponential Euler):
        Psi_k(t+dt) = E*Psi_k(t) + ((E-1)/L) * N_hat(t)
    where dPsi/dt = L*Psi + N(Psi), L = i*(1/2)*k^2 (so iPsi_t = -(1/2)*Psi_xx),
    N(Psi) = i*kappa*|Psi|^2*Psi.

    From i*Psi_t = -(1/2)*Psi_xx - kappa*|Psi|^2*Psi:
        Psi_t = +i*(1/2)*Psi_xx + i*kappa*|Psi|^2*Psi
        In Fourier: Psi_k_t = -i*(1/2)*k^2*Psi_k + i*kappa*FFT(|Psi|^2*Psi)
    so L = -i*(1/2)*k^2 (note sign), and N_hat = i*kappa*FFT(|Psi|^2*Psi).
    """
    L = -1j * 0.5 * (k * k)
    E = np.exp(L * dt)
    # (E - 1)/L, regularize near L=0 (only L=0 mode if k=0)
    Q = np.where(np.abs(L) > 1e-14, (E - 1.0) / np.where(np.abs(L) > 1e-14, L, 1.0), dt)
    Psi_k = np.fft.fft(Psi)
    N_hat = 1j * kappa * np.fft.fft(np.abs(Psi) ** 2 * Psi)
    Psi_k_new = E * Psi_k + Q * N_hat
    return np.fft.ifft(Psi_k_new)


# ------------------------------------------------------------------ driver
def run(method: str, dt: float, Nx: int, T: float = T_FINAL):
    """Run one method with given (dt, Nx). Returns dict with diagnostics + final Psi."""
    x, k, dx = make_grid(Nx)
    Psi = initial_psi(x).astype(np.complex128)
    Psi0 = Psi.copy()

    M0 = mass(Psi, dx)
    E0 = energy(Psi, k, dx)

    n_steps = int(round(T / dt))
    actual_dt = T / n_steps   # adjust so that n_steps*dt = T exactly
    nan_step = -1

    t0 = time.time()
    if method == "strang":
        step = step_strang
    elif method == "lie":
        step = step_lie
    elif method == "etdrk1":
        step = step_etdrk1
    else:
        raise ValueError(method)

    for i in range(n_steps):
        Psi = step(Psi, k, actual_dt)
        if not np.all(np.isfinite(Psi)):
            nan_step = i
            break
    wall = time.time() - t0

    finite = bool(np.all(np.isfinite(Psi)))
    Psi_exact_T = exact_psi(x, T)
    if finite:
        Mf = mass(Psi, dx)
        Ef = energy(Psi, k, dx)
        peak_amp = peak_amplitude(Psi)
        peak_pos = peak_position(x, Psi)
        winding = phase_winding(Psi, dx)
        L2_err = float(np.sqrt(np.sum(np.abs(Psi - Psi_exact_T) ** 2) * dx))
        Linf_err = float(np.max(np.abs(Psi - Psi_exact_T)))
        rel_L2 = L2_err / float(np.sqrt(np.sum(np.abs(Psi_exact_T) ** 2) * dx))
    else:
        Mf = float("nan")
        Ef = float("nan")
        peak_amp = float("nan")
        peak_pos = float("nan")
        winding = float("nan")
        L2_err = float("nan")
        Linf_err = float("nan")
        rel_L2 = float("nan")

    return {
        "method": method,
        "dt": float(actual_dt),
        "Nx": int(Nx),
        "T": float(T),
        "n_steps": int(n_steps),
        "wall_seconds": float(wall),
        "finite": finite,
        "nan_step": int(nan_step),
        "mass_initial": float(M0),
        "mass_final": float(Mf),
        "mass_drift_abs": float(abs(Mf - M0)) if finite else float("nan"),
        "mass_drift_rel": float(abs(Mf - M0) / M0) if finite else float("nan"),
        "energy_initial": float(E0),
        "energy_final": float(Ef),
        "energy_drift_abs": float(abs(Ef - E0)) if finite else float("nan"),
        "energy_drift_rel": float(abs(Ef - E0) / abs(E0)) if finite and abs(E0) > 1e-30 else float("nan"),
        "peak_amplitude_final": float(peak_amp),
        "peak_position_final": float(peak_pos),
        "phase_winding": float(winding),
        "L2_error_vs_exact": float(L2_err),
        "Linf_error_vs_exact": float(Linf_err),
        "relL2_error_vs_exact": float(rel_L2),
        "x": x,
        "Psi_final": Psi,
        "Psi_initial": Psi0,
        "Psi_exact_final": Psi_exact_T,
    }


def fmt(r):
    return (f"  {r['method']:7s} dt={r['dt']:.5g} Nx={r['Nx']:4d}  "
            f"finite={r['finite']}  "
            f"|dM|/M={r['mass_drift_rel']:.3e}  "
            f"|dE|/|E|={r['energy_drift_rel']:.3e}  "
            f"peak_amp={r['peak_amplitude_final']:.6f} (gt=2.0000)  "
            f"peak_pos={r['peak_position_final']:+.4f} (gt=-3.0000)  "
            f"relL2={r['relL2_error_vs_exact']:.3e}  "
            f"wall={r['wall_seconds']:.2f}s")


def main():
    print("S1 NLS focusing bright soliton -- method/parameter sweep")
    print(f"Domain x in [{X_MIN},{X_MAX}], T={T_FINAL}, kappa={KAPPA}, A=sqrt(2), v={V}, x0={X0}")
    print(f"Ground truth: |Psi|_inf = {A:.10f} -> |Psi|^2_max = 2.0; "
          f"peak position at T={T_FINAL}: {X0 + V*T_FINAL:+.4f}; "
          f"mass = 2*A = {2*A:.10f}")
    print()

    results = []

    # ---------- Experiment 1: Strang split-step Fourier, sweep dt x Nx ----------
    print("[E1] Strang split-step Fourier on Psi  (sweep dt x Nx)")
    dt_grid = [0.01, 0.001, 0.0001]
    Nx_grid = [128, 256, 512]
    for Nx in Nx_grid:
        for dt in dt_grid:
            r = run("strang", dt, Nx)
            results.append(r)
            print(fmt(r))
    print()

    # ---------- Experiment 2: Lie split-step (first-order) at Nx=256 ----------
    print("[E2] Lie (first-order) split-step Fourier on Psi at Nx=256")
    for dt in dt_grid:
        r = run("lie", dt, 256)
        results.append(r)
        print(fmt(r))
    print()

    # ---------- Experiment 3: ETD-RK1 (exponential Euler) at Nx=256 ----------
    print("[E3] ETD-RK1 (exponential Euler) on Psi at Nx=256")
    for dt in dt_grid:
        r = run("etdrk1", dt, 256)
        results.append(r)
        print(fmt(r))
    print()

    # ---------- Save NPZ with all arrays ----------
    save_dict = {}
    summary_rows = []
    for r in results:
        tag = f"{r['method']}_dt{r['dt']:.0e}_Nx{r['Nx']}".replace("e-0", "em").replace("e+0", "ep")
        save_dict[f"x_{tag}"] = r["x"]
        save_dict[f"Psi_final_{tag}"] = r["Psi_final"]
        save_dict[f"Psi_initial_{tag}"] = r["Psi_initial"]
        save_dict[f"Psi_exact_{tag}"] = r["Psi_exact_final"]
        summary_rows.append({k: v for k, v in r.items() if k not in ("x", "Psi_final", "Psi_initial", "Psi_exact_final")})

    # also save a JSON-like array of summary diagnostics
    summary_json = json.dumps(summary_rows, indent=2)
    save_dict["summary_json"] = np.array(summary_json)

    np.savez(OUT_DIR / "S1.npz", **save_dict)
    print(f"Saved {OUT_DIR / 'S1.npz'} with {len(save_dict)} arrays.")

    # also dump summary to a side file for the wrap-up
    with open(HERE / "_summary_diagnostics.json", "w") as f:
        f.write(summary_json)
    print(f"Wrote _summary_diagnostics.json with {len(summary_rows)} rows.")


if __name__ == "__main__":
    main()
