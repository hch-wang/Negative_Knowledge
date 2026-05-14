"""
Stage-2 Class A v3, task T_B, condition NoKB — Experiment E3.

PDE (coupled Burgers-swept-KdV):
    u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d/dx (u v)

IC: v(x,0) = 4 * exp(-(x+5)^2/2.25), u(x,0) = 0
Domain: x in [-15, 15], Nx = 256, periodic
T_final = 6.0

Method (E3 = E2 with dt reduced 10x; one component change):
    - Spatial derivatives: Fourier pseudospectral
    - Aliasing control: 2/3-rule on quadratic product spectra (3v^2, uv)
    - Time integration: explicit RK4
    - dt = 5e-5 (was 5e-4 in E2; chosen to satisfy RK4 CFL on v_xxx:
      dt * k_max^3 = 5e-5 * 26.8^3 ~ 0.96 < 2.83 = RK4 imag axis bound)
"""
import numpy as np
import os

# --- grid setup ---------------------------------------------------------------
L = 30.0
Nx = 256
x = -15.0 + L * np.arange(Nx) / Nx
dx = L / Nx
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k

# 2/3-rule dealiasing mask
k_max = np.max(np.abs(k))
dealias_mask = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(np.float64)

# --- initial condition --------------------------------------------------------
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros_like(x)


def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))


def d2x_spec(f):
    return np.real(np.fft.ifft((ik ** 2) * np.fft.fft(f)))


def d3x_spec(f):
    return np.real(np.fft.ifft((ik ** 3) * np.fft.fft(f)))


def dealiased_product(a, b):
    """Compute a*b in physical space with 2/3-rule dealiasing on inputs and output."""
    A = np.fft.fft(a) * dealias_mask
    B = np.fft.fft(b) * dealias_mask
    a_f = np.real(np.fft.ifft(A))
    b_f = np.real(np.fft.ifft(B))
    p = a_f * b_f
    P = np.fft.fft(p) * dealias_mask
    return np.real(np.fft.ifft(P))


def rhs(u, v):
    ux = dx_spec(u)
    vx = dx_spec(v)
    vxx = d2x_spec(v)
    vxxx = d3x_spec(v)
    # Quadratic products with dealiasing
    v_sq = dealiased_product(v, v)         # v^2
    uv = dealiased_product(u, v)            # u*v
    u_ux = dealiased_product(u, ux)         # u * u_x
    v_vx = dealiased_product(v, vx)         # v * v_x
    # d/dx (3 v^2 + v_xx)  — v_xx is linear so just spectral derivative; sum is linear in spectrum
    rhs_force_u = dx_spec(3.0 * v_sq + vxx)
    rhs_force_v = dx_spec(uv)
    du_dt = -3.0 * u_ux - rhs_force_u
    dv_dt = -6.0 * v_vx - vxxx - rhs_force_v
    return du_dt, dv_dt


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return u_new, v_new


def main():
    T = 6.0
    dt = 5e-5
    n_steps = int(round(T / dt))
    dt = T / n_steps

    n_snapshots = 13
    snap_every = n_steps // (n_snapshots - 1)

    snaps = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
    snaps[0, 0, :] = u0
    snaps[0, 1, :] = v0

    u = u0.copy()
    v = v0.copy()
    snap_idx = 1
    mass_v0 = np.sum(v) * dx
    diverged = False
    for step in range(1, n_steps + 1):
        u, v = rk4_step(u, v, dt)
        if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
            print(f"  ! NaN/Inf at step {step} (t={step*dt:.4f})")
            diverged = True
            break
        if step % snap_every == 0 and snap_idx < n_snapshots:
            snaps[snap_idx, 0, :] = u
            snaps[snap_idx, 1, :] = v
            mass_v = np.sum(v) * dx
            v_max = np.max(np.abs(v))
            u_max = np.max(np.abs(u))
            print(f"  snap {snap_idx}: t={step*dt:.4f}  |v|max={v_max:.4f}  |u|max={u_max:.4f}  mass(v)={mass_v:.6f}  drift={(mass_v-mass_v0)/abs(mass_v0)*100:+.3f}%")
            snap_idx += 1

    if diverged:
        for i in range(snap_idx, n_snapshots):
            snaps[i, 0, :] = u
            snaps[i, 1, :] = v

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "T_B.npy")
    np.save(out_path, snaps)
    print(f"Saved {snaps.shape} -> {out_path}")
    print(f"Final |v|max = {np.max(np.abs(snaps[-1,1])):.4f}, |u|max = {np.max(np.abs(snaps[-1,0])):.4f}")
    print(f"mass(v) initial = {mass_v0:.6f}, final = {np.sum(snaps[-1,1])*dx:.6f}")


if __name__ == "__main__":
    main()
