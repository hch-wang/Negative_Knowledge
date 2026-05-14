"""
E2: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 for
coupled Burgers-swept-KdV bore x soliton interaction.

PDE:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

IC:
  u(x,0) = 1.5 * (1 - tanh(x/0.5)) / 2   (smoothed bore at x=0)
  v(x,0) = 1.5 * sech^2(x+8)             (KdV soliton at x=-8)

Domain: x in [-15, 15], Nx = 256, T = 8.0, dt = 1e-4
Single-component upgrade vs E1: ADD 2/3 dealiasing mask on nonlinear products.

Output: pred_results/T_C.npy  shape (n_snapshots, 2, Nx)
"""

import os
import numpy as np

# ----------------------------- grid -----------------------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k

# 2/3 dealiasing mask: zero modes with |k_idx| > Nx/3
k_idx = np.fft.fftfreq(Nx) * Nx        # signed integer index
dealias = (np.abs(k_idx) <= Nx / 3.0).astype(float)


def dealiased_product(a, b):
    """Compute (a*b) but with both operands and result restricted to
    the 2/3 spectral band. This blocks alias-folded modes from feeding
    quadratic products back into resolved wavenumbers."""
    aF = np.fft.fft(a) * dealias
    bF = np.fft.fft(b) * dealias
    a_filt = np.real(np.fft.ifft(aF))
    b_filt = np.real(np.fft.ifft(bF))
    prod = a_filt * b_filt
    prodF = np.fft.fft(prod) * dealias
    return np.real(np.fft.ifft(prodF))


# ----------------------------- IC -----------------------------
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 / np.cosh(x + 8.0) ** 2

# ----------------------------- time -----------------------------
T = 8.0
dt = 1e-4
n_steps = int(round(T / dt))
n_snapshots = 9
snap_every = n_steps // (n_snapshots - 1)


def rhs(u, v):
    """Compute (du/dt, dv/dt) per BKdV PDE with 2/3 dealiasing."""
    uF = np.fft.fft(u)
    vF = np.fft.fft(v)

    # linear / single-field spatial derivatives are alias-safe
    u_x = np.real(np.fft.ifft(ik * uF))
    v_x = np.real(np.fft.ifft(ik * vF))
    v_xx = np.real(np.fft.ifft(-(k**2) * vF))
    # v_xxx = ifft( (ik)^3 vF ) = ifft( -i k^3 vF )
    v_xxx = np.real(np.fft.ifft((-1j * k**3) * vF))

    # nonlinear products with 2/3 dealiasing
    uu_x = dealiased_product(u, u_x)
    vv_x = dealiased_product(v, v_x)
    v2 = dealiased_product(v, v)
    uv = dealiased_product(u, v)

    # d_x of these dealiased products (and v_xx is a linear field)
    d_v2_x = np.real(np.fft.ifft(ik * np.fft.fft(v2) * dealias))
    d_vxx_x = np.real(np.fft.ifft(ik * np.fft.fft(v_xx)))
    d_uv_x = np.real(np.fft.ifft(ik * np.fft.fft(uv) * dealias))

    # rhs: u_t = -3 u u_x - d_x(3 v^2 + v_xx)
    du = -3.0 * uu_x - 3.0 * d_v2_x - d_vxx_x
    # rhs: v_t = -6 v v_x - v_xxx - d_x(u v)
    dv = -6.0 * vv_x - v_xxx - d_uv_x

    return du, dv


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return u_new, v_new


# ----------------------------- run -----------------------------
u = u0.copy()
v = v0.copy()

snaps = [np.stack([u, v], axis=0)]
snap_times = [0.0]
mass_v0 = np.sum(v) * dx
mass_u0 = np.sum(u) * dx
print(f"t=0.0000  max|u|={np.max(np.abs(u)):.4f}  max|v|={np.max(np.abs(v)):.4f}  "
      f"mass_u={mass_u0:.4f}  mass_v={mass_v0:.4f}")

for n in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        print(f"BLOW-UP at step {n}, t={n*dt:.4f}")
        break
    if n % snap_every == 0 or n == n_steps:
        snaps.append(np.stack([u, v], axis=0))
        snap_times.append(n * dt)
        mu = np.sum(u) * dx
        mv = np.sum(v) * dx
        print(f"t={n*dt:.4f}  max|u|={np.max(np.abs(u)):.4f}  "
              f"max|v|={np.max(np.abs(v)):.4f}  "
              f"mass_u={mu:.4f}  mass_v={mv:.4f}  "
              f"d_mass_v={mv-mass_v0:.2e}")

snaps = np.array(snaps)  # (n_snapshots, 2, Nx)
print("Final shape:", snaps.shape, "  snap_times:", [f"{t:.2f}" for t in snap_times])

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", snaps)
print("Saved pred_results/T_C.npy")
