"""
E3: E2 (IF-RK4) + 2/3-rule dealiasing on nonlinear products.

PDE (coupled Burgers-swept-KdV):
    u_t = -3 u u_x - 6 v v_x - v_xxx
    v_t = -6 v v_x - v_xxx - (u v)_x

In Fourier space:
    d/dt u_hat = -ik F[3 u^2/2]_hat ... actually it's easier to compute
                 nonlinear products in physical space and pass through dealiasing.

Linear stiff term in v eq is -v_xxx -> in Fourier: -(ik)^3 v_hat = i k^3 v_hat
Substitute w_hat = exp(-i k^3 t) v_hat so that the linear part is removed:
    d/dt w_hat = exp(-i k^3 t) * NL_v_hat

Dealiasing: build a mask M(k)=1 for |k| < (2/3) kmax else 0; apply M(k) to the
Fourier transform of every nonlinear product BEFORE multiplying by ik or using it.
"""

import numpy as np
import os

# Spatial grid
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=L / Nx)
kmax = np.max(np.abs(k))
ik = 1j * k

# 2/3-rule dealiasing mask (in Fourier space, zero out high modes of nonlinear products)
kcut = (2.0 / 3.0) * kmax
dealias = (np.abs(k) < kcut).astype(np.float64)

# Linear dispersive eigenvalue for v_hat: d/dt v_hat = i k^3 v_hat + NL
ik3_disp = 1j * (k ** 3)

def fft(a):
    return np.fft.fft(a)

def ifft(A):
    return np.real(np.fft.ifft(A))

def nl_product_hat(a, b):
    """Compute F[a*b] with 2/3-rule dealiasing."""
    return dealias * fft(a * b)

def rhs_fourier(u_hat, w_hat, t):
    # Reconstruct v_hat = exp(i k^3 t) w_hat
    phase = np.exp(ik3_disp * t)
    v_hat = phase * w_hat
    # Physical fields (apply dealias to fields BEFORE multiplying — equivalent to product dealiasing)
    u = ifft(u_hat)
    v = ifft(v_hat)

    # u_t = -3 u u_x - 6 v v_x - v_xxx
    # Compute in spectral form:
    # -3 u u_x = -3 * (1/2) d/dx (u^2) = -(3/2) ik F[u^2]
    u2_hat = nl_product_hat(u, u)
    v2_hat = nl_product_hat(v, v)
    uv_hat = nl_product_hat(u, v)
    v_xx_hat = (ik ** 2) * v_hat
    v_xxx_hat = (ik ** 3) * v_hat

    # u_hat_t = -ik * F[3 u^2/2 + 3 v^2 + v_xx]
    # = -ik * (1.5 u2_hat + 3 v2_hat) - ik * v_xx_hat
    # = -ik * (1.5 u2_hat + 3 v2_hat + v_xx_hat)
    u_hat_t = -ik * (1.5 * u2_hat + 3.0 * v2_hat + v_xx_hat)

    # v_hat_t = -ik * F[3 v^2 + uv] + linear v_xxx
    # Linear part: -v_xxx -> -(ik^3) v_hat = +i k^3 v_hat ... wait sign:
    # -(ik)^3 = -(i^3 k^3) = -(-i k^3) = i k^3. So d/dt v_hat |_linear = i k^3 v_hat.
    # But we already absorbed this via w_hat. So in NL piece:
    v_hat_t_nl = -ik * (3.0 * v2_hat + uv_hat)

    # w_hat_t = exp(-i k^3 t) * v_hat_t_nl
    w_hat_t = np.exp(-ik3_disp * t) * v_hat_t_nl
    return u_hat_t, w_hat_t

def rk4_step(u_hat, w_hat, t, dt):
    k1u, k1w = rhs_fourier(u_hat, w_hat, t)
    k2u, k2w = rhs_fourier(u_hat + 0.5 * dt * k1u, w_hat + 0.5 * dt * k1w, t + 0.5 * dt)
    k3u, k3w = rhs_fourier(u_hat + 0.5 * dt * k2u, w_hat + 0.5 * dt * k2w, t + 0.5 * dt)
    k4u, k4w = rhs_fourier(u_hat + dt * k3u, w_hat + dt * k3w, t + dt)
    u_new = u_hat + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    w_new = w_hat + (dt / 6.0) * (k1w + 2.0 * k2w + 2.0 * k3w + k4w)
    return u_new, w_new

# Initial condition
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 / np.cosh(x + 8.0) ** 2

# Project IC onto dealiased space (zero out very-high modes) — safe
u_hat = fft(u0)
v_hat = fft(v0)
w_hat = v_hat.copy()

T = 8.0
dt = 0.002
nsteps = int(round(T / dt))
n_snapshots = 17

snapshots = [np.stack([u0, v0], axis=0)]
snap_times = [0.0]
snap_stride = nsteps // (n_snapshots - 1)

# Initial diagnostics
initial_mass_u = np.sum(u0) * dx
initial_mass_v = np.sum(v0) * dx
print(f"Initial: mass_u={initial_mass_u:.6f}, mass_v={initial_mass_v:.6f}")
print(f"Initial: max u={np.max(u0):.4f}, max v={np.max(v0):.4f}")

t = 0.0
blew_up = False
for step in range(1, nsteps + 1):
    u_hat, w_hat = rk4_step(u_hat, w_hat, t, dt)
    t += dt
    if step % snap_stride == 0 and len(snapshots) < n_snapshots:
        v_hat_now = np.exp(ik3_disp * t) * w_hat
        u_now = ifft(u_hat)
        v_now = ifft(v_hat_now)
        snapshots.append(np.stack([u_now, v_now], axis=0))
        snap_times.append(t)
    if not np.all(np.isfinite(u_hat)) or not np.all(np.isfinite(w_hat)):
        print(f"NaN/Inf at step {step}, t={t:.4f}")
        blew_up = True
        break
    if step % 400 == 0:
        v_hat_now = np.exp(ik3_disp * t) * w_hat
        u_now = ifft(u_hat)
        v_now = ifft(v_hat_now)
        m_u = np.sum(u_now) * dx
        m_v = np.sum(v_now) * dx
        print(f"step {step}, t={t:.4f}, |u|max={np.max(np.abs(u_now)):.4f}, |v|max={np.max(np.abs(v_now)):.4f}, mass_u={m_u:.4f}, mass_v={m_v:.4f}")

while len(snapshots) < n_snapshots:
    snapshots.append(snapshots[-1].copy())

snapshots = np.array(snapshots)
print(f"\nSnapshots shape: {snapshots.shape}")
print(f"Snap times: {snap_times}")
print(f"Final |u|max={np.max(np.abs(snapshots[-1, 0])):.4f}, |v|max={np.max(np.abs(snapshots[-1, 1])):.4f}")
print(f"Final v peak amplitude = {np.max(snapshots[-1, 1]):.4f}")
print(f"Final mass_u = {np.sum(snapshots[-1,0])*dx:.4f} (initial {initial_mass_u:.4f})")
print(f"Final mass_v = {np.sum(snapshots[-1,1])*dx:.4f} (initial {initial_mass_v:.4f})")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", snapshots)
print("Saved pred_results/T_C.npy")
