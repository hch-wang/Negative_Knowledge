"""
T_C — Burgers bore × KdV soliton (PosNeg condition, E2 with u-viscosity)
=========================================================================

System:
    u_t + 3 u u_x = -d_x (3 v^2 + v_xx) + nu * u_xx          (E2: added nu*u_xx)
    v_t + 6 v v_x + v_xxx = -d_x (u v)

E2 = E1 + single-component escalation: add explicit linear viscosity ν=5e-2
on u_xx, per BKdV-S6 deep-synthesis prescription, rejecting the BKdV-S4
safe envelope warning that ν_h ~ 1e-22 is 13 orders too weak for bore IC.

Stack remains:
    - Fourier pseudospectral (Nx=256, L=30)
    - 2/3-rule dealiasing on every nonlinear product
    - Classical explicit RK4 over the FULL RHS (now incl. nu*u_xx explicit)
    - dt=1e-4 unchanged

Stability check for nu*u_xx explicit-RK4 (parabolic):
    nu * k_max^2 * dt = 5e-2 * (pi/dx)^2 * 1e-4
                     ~ 5e-2 * 720       * 1e-4
                     ~ 3.6e-3  <<  2.785 (RK4 real-axis stability bound)
"""

import numpy as np
import os
import sys
import time


def main():
    # --- Grid ---
    Nx = 256
    L = 30.0
    x = np.linspace(-L / 2, L / 2, Nx, endpoint=False)
    dx = L / Nx
    k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
    ik = 1j * k
    k2 = k * k

    # --- 2/3-rule dealias mask ---
    k_max_index = Nx // 3
    dealias = np.abs(np.fft.fftfreq(Nx, d=1.0) * Nx).astype(int) <= k_max_index

    # --- IC ---
    u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
    v0 = 1.5 / np.cosh(x + 8.0) ** 2

    # --- u-side viscosity (BKdV-S6 prescription) ---
    nu = 5e-2

    # --- Time stepping ---
    T = 8.0
    dt = 1e-4
    n_steps = int(round(T / dt))

    # snapshot times
    n_snap = 17
    snap_times = np.linspace(0.0, T, n_snap)
    snap_steps = set(int(round(t / dt)) for t in snap_times)

    def dealias_field(fhat):
        out = fhat.copy()
        out[~dealias] = 0.0
        return out

    def rhs(u, v):
        u_hat = np.fft.fft(u)
        v_hat = np.fft.fft(v)

        u2 = u * u
        v2 = v * v
        uv = u * v

        u2_hat = dealias_field(np.fft.fft(u2))
        v2_hat = dealias_field(np.fft.fft(v2))
        uv_hat = dealias_field(np.fft.fft(uv))

        vxx_hat = -k2 * v_hat
        vxxx_hat = -1j * (k ** 3) * v_hat

        # u_t = -3/2 d_x(u^2) - d_x(3 v^2 + v_xx) + nu*u_xx
        ut_hat = -1.5 * ik * u2_hat - ik * (3.0 * v2_hat + vxx_hat) - nu * k2 * u_hat
        # v_t = -3 d_x(v^2) - v_xxx - d_x(uv)
        vt_hat = -3.0 * ik * v2_hat - vxxx_hat - ik * uv_hat

        return np.real(np.fft.ifft(ut_hat)), np.real(np.fft.ifft(vt_hat))

    def rk4_step(u, v, dt):
        k1u, k1v = rhs(u, v)
        k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
        k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
        k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
        un = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
        vn = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
        return un, vn

    snaps = [np.stack([u0.copy(), v0.copy()], axis=0)]
    snap_times_actual = [0.0]

    u = u0.copy()
    v = v0.copy()

    t0 = time.time()
    blew_up = False
    last_t = 0.0

    for step in range(1, n_steps + 1):
        u, v = rk4_step(u, v, dt)
        if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
            blew_up = True
            print(f"[E2] Blow-up at step {step}, t={step*dt:.4f}", file=sys.stderr)
            break
        if step in snap_steps:
            snaps.append(np.stack([u.copy(), v.copy()], axis=0))
            snap_times_actual.append(step * dt)
        last_t = step * dt

    elapsed = time.time() - t0
    print(f"[E2] integration done in {elapsed:.2f}s; last_t={last_t:.4f}; blew_up={blew_up}; nu={nu}")
    out = np.stack(snaps, axis=0)
    print(f"[E2] snapshots saved: {out.shape}, snap_times={[round(t,3) for t in snap_times_actual]}")

    u_final = snaps[-1][0]
    v_final = snaps[-1][1]
    print(f"[E2] u_final: max={u_final.max():.3f}, min={u_final.min():.3f}")
    print(f"[E2] v_final: max={v_final.max():.3f}, min={v_final.min():.3f}")
    tv_u = np.sum(np.abs(np.diff(u_final)))
    print(f"[E2] TV(u_final) = {tv_u:.3f} (IC TV={np.sum(np.abs(np.diff(u0))):.3f})")
    print(f"[E2] mass_u: {u0.sum()*dx:.6f} -> {u_final.sum()*dx:.6f}")
    print(f"[E2] mass_v: {v0.sum()*dx:.6f} -> {v_final.sum()*dx:.6f}")
    vf = v_final
    peaks = ((vf[1:-1] > vf[:-2]) & (vf[1:-1] > vf[2:]) & (vf[1:-1] > 0.1)).sum()
    print(f"[E2] n_peaks_v (height>0.1) = {peaks}")

    # trace
    for i, t in enumerate(snap_times_actual):
        u_s = snaps[i][0]
        v_s = snaps[i][1]
        print(f"   t={t:.2f}: u_max={u_s.max():.3f}, u_min={u_s.min():.3f}, v_max={v_s.max():.3f}")

    os.makedirs("pred_results", exist_ok=True)
    np.save("pred_results/T_C.npy", out)
    print(f"[E2] saved pred_results/T_C.npy with shape {out.shape}")


if __name__ == "__main__":
    main()
