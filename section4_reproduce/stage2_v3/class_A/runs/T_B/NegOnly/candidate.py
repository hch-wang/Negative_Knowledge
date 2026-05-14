"""
T_B / NegOnly / E2.

Coupled Burgers-swept-KdV system:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx) + nu * u_xx     <-- nu added (E2)
  v_t + 6 v v_x + v_xxx = -d_x(u v)                  <-- unchanged

Explicit form:
  u_t = -3 u u_x - 6 v v_x - v_xxx + nu * u_xx
  v_t = -6 v v_x - v_xxx - u_x v - u v_x

IC:
  v(x,0) = 4 * exp(-(x+5)^2 / 2.25)
  u(x,0) = 0

Domain: x in [-15, 15) periodic, Nx=256, L=30.
Final time: T=6.0.

Method:
  - Fourier pseudospectral, 2/3-rule dealiasing on all quadratic products.
  - Classical explicit RK4, dt=2e-4.
  - Explicit linear viscosity nu*u_xx on u-equation ONLY (single-component
    upgrade over E1 per BKdV-S6 deep synthesis: nu=5e-2 recommended for
    bore-like u-gradient regimes; CFL-trivial at this dt).

Output: pred_results/T_B.npy, shape (n_snapshots, 2, 256), channel (u, v).
"""

import os
import numpy as np


def main():
    # ---- Grid ----
    Nx = 256
    L = 30.0
    dx = L / Nx
    x = -L / 2.0 + dx * np.arange(Nx)   # x in [-15, -15+dx, ..., 15-dx)

    # Spectral wavenumbers (FFT order)
    k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
    ik = 1j * k
    k2 = k * k
    k3 = k2 * k

    # 2/3 dealiasing mask
    k_max_idx = Nx // 3
    dealias = np.ones(Nx, dtype=np.float64)
    freq_idx = np.fft.fftfreq(Nx, d=1.0 / Nx).astype(int)
    dealias[np.abs(freq_idx) > k_max_idx] = 0.0

    # ---- Physical / numerical parameters ----
    nu_u = 5e-2     # linear viscosity on u (BKdV-S6 recommended default)

    # ---- IC ----
    v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
    u0 = np.zeros(Nx, dtype=np.float64)

    # ---- Time stepping ----
    T = 6.0
    dt = 2e-4
    nsteps = int(round(T / dt))
    assert abs(nsteps * dt - T) < 1e-10

    # 13 snapshots evenly spaced
    n_snapshots = 13
    snap_steps = np.linspace(0, nsteps, n_snapshots).round().astype(int)
    snap_set = set(snap_steps.tolist())
    snapshots = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)

    def rhs(u, v):
        """RHS of (u_t, v_t)."""
        u_hat = np.fft.fft(u)
        v_hat = np.fft.fft(v)

        # Dealias fields BEFORE computing nonlinear products
        u_hat_d = u_hat * dealias
        v_hat_d = v_hat * dealias

        # Real-space dealiased fields
        u_d = np.fft.ifft(u_hat_d).real
        v_d = np.fft.ifft(v_hat_d).real

        # Spectral derivatives
        u_x = np.fft.ifft(ik * u_hat_d).real
        u_xx = np.fft.ifft(-k2 * u_hat_d).real
        v_x = np.fft.ifft(ik * v_hat_d).real
        v_xxx = np.fft.ifft(-1j * k3 * v_hat_d).real

        # Nonlinear products
        uu_x = u_d * u_x
        vv_x = v_d * v_x
        uv = u_d * v_d
        uv_hat = np.fft.fft(uv) * dealias
        uv_x = np.fft.ifft(ik * uv_hat).real

        # RHS
        ut = -3.0 * uu_x - 6.0 * vv_x - v_xxx + nu_u * u_xx
        vt = -6.0 * vv_x - v_xxx - uv_x

        return ut, vt

    # ---- Main loop ----
    u = u0.copy()
    v = v0.copy()

    snap_idx = 0
    if 0 in snap_set:
        snapshots[snap_idx, 0] = u
        snapshots[snap_idx, 1] = v
        snap_idx += 1

    finite_warn = False
    blowup_step = -1

    for step in range(1, nsteps + 1):
        k1u, k1v = rhs(u, v)
        k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
        k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
        k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
        u = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
        v = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)

        if not finite_warn and not (np.isfinite(u).all() and np.isfinite(v).all()):
            finite_warn = True
            blowup_step = step
            print(f"[WARN] non-finite at step {step}, t={step*dt:.4f}")

        if step in snap_set:
            snapshots[snap_idx, 0] = u
            snapshots[snap_idx, 1] = v
            snap_idx += 1

    # ---- Save ----
    out_path = os.path.join(os.path.dirname(__file__), "pred_results", "T_B.npy")
    np.save(out_path, snapshots)

    # ---- Diagnostics ----
    v_final = snapshots[-1, 1]
    u_final = snapshots[-1, 0]
    v_initial = snapshots[0, 1]
    mass_v_initial = v_initial.sum() * dx
    mass_v_final = v_final.sum() * dx
    mass_drift = abs(mass_v_final - mass_v_initial) / max(abs(mass_v_initial), 1e-30)
    finite_all = np.isfinite(snapshots).all()

    def count_peaks(y, min_amp=0.8, min_sep=8):
        peaks = []
        N = len(y)
        for i in range(N):
            l = (i - 1) % N
            r = (i + 1) % N
            if y[i] > y[l] and y[i] > y[r] and y[i] >= min_amp:
                peaks.append((i, y[i]))
        # Merge nearby peaks (keep highest within min_sep)
        peaks.sort(key=lambda p: -p[1])
        kept = []
        for (idx, amp) in peaks:
            keep = True
            for (idx_k, _) in kept:
                d_pbc = min(abs(idx - idx_k), N - abs(idx - idx_k))
                if d_pbc < min_sep:
                    keep = False
                    break
            if keep:
                kept.append((idx, amp))
        kept.sort(key=lambda p: p[0])
        return kept, peaks

    peaks_kept, peaks_raw = count_peaks(v_final, min_amp=0.8, min_sep=8)

    print(f"finite_all: {finite_all}")
    print(f"blowup_step: {blowup_step}")
    print(f"shape: {snapshots.shape}")
    print(f"mass_v initial: {mass_v_initial:.6f}, final: {mass_v_final:.6f}, drift: {mass_drift*100:.3f}%")
    print(f"u_final range: [{u_final.min():.4f}, {u_final.max():.4f}]")
    print(f"v_final range: [{v_final.min():.4f}, {v_final.max():.4f}]")
    print(f"v_final raw peaks (any pixel-local max >=0.8): {len(peaks_raw)}")
    print(f"v_final peaks with min separation 8 indices: {len(peaks_kept)}")
    for (i, a) in peaks_kept:
        print(f"  idx={i:3d} x={x[i]:+7.3f}  v={a:.4f}")

    # Trajectory u_max
    print("\ntrajectory:")
    snap_ts = np.linspace(0, T, n_snapshots)
    for j in range(n_snapshots):
        uj = snapshots[j, 0]; vj = snapshots[j, 1]
        print(f" t={snap_ts[j]:.2f}: u=[{uj.min():+7.3f},{uj.max():+7.3f}]  v=[{vj.min():+7.3f},{vj.max():+7.3f}]")


if __name__ == "__main__":
    main()
