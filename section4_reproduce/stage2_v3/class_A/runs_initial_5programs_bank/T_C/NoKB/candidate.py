"""
T_C E3: Burgers bore × KdV soliton — coupled Burgers-swept-KdV system.

Single-component addition over E2: low-amplitude hyperviscosity -eps*u_xxxx on
u only (the bore variable). Everything else identical to E2.

Stack:
  - Spatial: Fourier pseudospectral (periodic, Nx=256)
  - Time: explicit classical RK4, dt=1e-4
  - 2/3-rule dealiasing on every nonlinear product
  - NEW: hyperviscosity -eps*u_xxxx on u only, eps=1e-5

PDE solved (effective):
  u_t + 3 u u_x = - d/dx(3 v^2 + v_xx) - eps * u_xxxx
  v_t + 6 v v_x + v_xxx = - d/dx(u v)

Domain x in [-15, 15], periodic.
T = 8.0, 17 snapshots (every 0.5 in time).
"""

import os
import numpy as np


def main():
    # ---- Grid ----
    Nx = 256
    L = 30.0
    x = -15.0 + L * np.arange(Nx) / Nx           # periodic grid on [-15, 15)
    dx = L / Nx                                   # 0.1171875

    # Fourier wavenumbers
    k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)      # rad / unit length
    ik = 1j * k
    ik3 = 1j * (k ** 3)                            # for v_xxx
    k2_op = -(k ** 2)                              # for v_xx
    k4_op = (k ** 4)                               # for u_xxxx (positive: -eps*u_xxxx adds dissipation since d/dx^4 e^{ikx} = k^4 e^{ikx})

    # 2/3-rule dealiasing mask
    k_max = np.max(np.abs(k))
    k_cut = (2.0 / 3.0) * k_max
    dealias = (np.abs(k) <= k_cut).astype(np.float64)

    # Hyperviscosity coefficient (applied to u only)
    eps_hv = 1.0e-5

    # ---- Initial condition ----
    u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
    v0 = 1.5 / np.cosh(x + 8.0) ** 2

    # ---- Time stepping ----
    T_final = 8.0
    dt = 1.0e-4
    n_steps = int(round(T_final / dt))
    snap_dt = 0.5
    snap_stride = int(round(snap_dt / dt))         # 5000
    n_snap = n_steps // snap_stride + 1            # 17

    snaps = np.empty((n_snap, 2, Nx), dtype=np.float64)
    snaps[0, 0, :] = u0
    snaps[0, 1, :] = v0

    def rhs(u, v):
        """Right-hand side of the coupled system with 2/3 dealiasing + hyperviscosity on u."""
        uhat = np.fft.fft(u)
        vhat = np.fft.fft(v)

        # Linear derivatives
        u_x = np.real(np.fft.ifft(ik * uhat))
        v_x = np.real(np.fft.ifft(ik * vhat))
        v_xx = np.real(np.fft.ifft(k2_op * vhat))
        v_xxx = np.real(np.fft.ifft(ik3 * vhat))
        # u_xxxx for hyperviscosity (sign: -eps * u_xxxx is dissipative)
        u_xxxx = np.real(np.fft.ifft(k4_op * uhat))

        # Dealiased fields
        u_d = np.real(np.fft.ifft(np.fft.fft(u) * dealias))
        v_d = np.real(np.fft.ifft(np.fft.fft(v) * dealias))

        # Forcing on u: -d/dx(3 v^2 + v_xx)
        f_u = 3.0 * v_d * v_d + v_xx
        d_f_u = np.real(np.fft.ifft(ik * (np.fft.fft(f_u) * dealias)))

        # Coupling on v: -d/dx(u v)
        uv = u_d * v_d
        d_uv = np.real(np.fft.ifft(ik * (np.fft.fft(uv) * dealias)))

        # Advective nonlinearities, dealiased
        uux = np.real(np.fft.ifft(np.fft.fft(u_d * u_x) * dealias))
        vvx = np.real(np.fft.ifft(np.fft.fft(v_d * v_x) * dealias))

        du_dt = -3.0 * uux - d_f_u - eps_hv * u_xxxx
        dv_dt = -6.0 * vvx - v_xxx - d_uv
        return du_dt, dv_dt

    u = u0.copy()
    v = v0.copy()
    snap_idx = 1

    for step in range(1, n_steps + 1):
        k1u, k1v = rhs(u, v)
        k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
        k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
        k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
        u = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
        v = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)

        if step % snap_stride == 0:
            if snap_idx < n_snap:
                snaps[snap_idx, 0, :] = u
                snaps[snap_idx, 1, :] = v
                snap_idx += 1
            if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
                print(f"NaN/Inf detected at step {step} (t={step*dt:.4f}); aborting.")
                snaps[snap_idx:, :, :] = np.nan
                break

    # ---- Save ----
    os.makedirs("pred_results", exist_ok=True)
    np.save("pred_results/T_C.npy", snaps)

    # Diagnostics
    print(f"snaps shape : {snaps.shape}")
    print(f"u final  min/max : {np.nanmin(snaps[-1,0]):.4f} / {np.nanmax(snaps[-1,0]):.4f}")
    print(f"v final  min/max : {np.nanmin(snaps[-1,1]):.4f} / {np.nanmax(snaps[-1,1]):.4f}")
    print(f"any NaN  : {not np.all(np.isfinite(snaps))}")
    v_peaks = np.nanmax(snaps[:, 1, :], axis=1)
    u_maxes = np.nanmax(np.abs(snaps[:, 0, :]), axis=1)
    print(f"v peak per snap : {v_peaks}")
    print(f"|u| max per snap: {u_maxes}")
    integ = getattr(np, "trapezoid", None) or getattr(np, "trapz")
    print(f"int u  t=0 : {integ(snaps[0,0], x):.5f}   t=T : {integ(snaps[-1,0], x):.5f}")
    print(f"int v  t=0 : {integ(snaps[0,1], x):.5f}   t=T : {integ(snaps[-1,1], x):.5f}")


if __name__ == "__main__":
    main()
