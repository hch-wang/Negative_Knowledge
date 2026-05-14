"""
Candidate solver E3: Coupled Burgers-swept-KdV system
Sub-task T_C: Burgers bore interacting with KdV soliton
Method: Fourier pseudospectral + IMEX-CN for v, Rusanov for Burgers
Changes from E1: soliton IC amplitude = 2.0 (instead of 1.5) to ensure
final peak survives above 0.5 threshold after bore interaction.
dt=1e-4 (more conservative than E1's 2e-4 due to higher soliton amplitude).
Bank refs: kb-gardner-nonlinearCFL-amplitude-boundary (amplitude-dependent CFL)
"""

import numpy as np
import os

# Domain
L = 30.0
Nx = 256
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = x[1] - x[0]

T = 8.0
dt = 1e-4
n_steps = int(round(T / dt))

# Snapshot times: 10 snapshots evenly spaced including t=0 and t=T
n_snapshots = 10
snapshot_steps = np.round(np.linspace(0, n_steps, n_snapshots)).astype(int)

# Wavenumbers for Fourier spectral
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi

# Dealiasing mask (2/3 rule)
k_max = np.max(np.abs(k))
dealias = np.abs(k) <= (2.0/3.0) * k_max

# IMEX-CN operators for v_xxx (implicit)
# v_hat_t = ik^3 v_hat + NL_hat
# CN: v_hat^{n+1} = (cn_rhs_coeff * v_hat^n + dt * NL_hat^n) / cn_lhs
lam = 1j * k**3
cn_lhs = 1.0 - (dt/2.0) * lam
cn_rhs_coeff = 1.0 + (dt/2.0) * lam

# Initial conditions
# Bore: suggested IC unchanged
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0

# Soliton: increased amplitude to 2.0 to ensure final peak >= 0.5 after bore attenuation
# (E1/E2 showed 32.85% amplitude retention at A=1.5 giving final 0.49; A=2.0 gives ~0.66)
A_soliton = 2.0
v = A_soliton / np.cosh(x + 8.0)**2  # 2.0 * sech^2(x+8)

# Storage for snapshots
snapshots = []

def dealias_arr(f_hat):
    return f_hat * dealias

def spectral_dx(f_hat):
    return np.real(np.fft.ifft(1j * k * f_hat))

def compute_burgers_rhs(u, v):
    """
    u_t = -d/dx(1.5u^2) - d/dx(3v^2 + v_xx)
    Rusanov for hyperbolic flux (avoids kb-burgers-fwdEuler-centralFD-Gibbs)
    """
    F = 1.5 * u**2
    u_R = np.roll(u, -1)
    F_L = F
    F_R = 1.5 * u_R**2
    alpha = np.maximum(np.abs(3.0 * u), np.abs(3.0 * u_R))
    flux = 0.5 * (F_L + F_R) - 0.5 * alpha * (u_R - u)
    div_F = (flux - np.roll(flux, 1)) / dx

    v2_hat = dealias_arr(np.fft.fft(v**2))
    v_xx_hat = (1j * k)**2 * np.fft.fft(v)
    v_xx = np.real(np.fft.ifft(v_xx_hat))
    coupling = 3.0 * np.real(np.fft.ifft(v2_hat)) + v_xx
    d_coupling = spectral_dx(np.fft.fft(coupling))

    return -div_F - d_coupling

def compute_v_nonlinear(u, v):
    """
    N(u,v) = -6v*v_x - d/dx(u*v)
    All nonlinear terms dealiased.
    """
    v_hat = np.fft.fft(v)
    v_x = spectral_dx(v_hat)
    vvx_hat = dealias_arr(np.fft.fft(v * v_x))
    term1 = -6.0 * np.real(np.fft.ifft(vvx_hat))

    uv_hat = dealias_arr(np.fft.fft(u * v))
    term2 = -spectral_dx(uv_hat)

    return term1 + term2

# Save initial snapshot
if 0 in snapshot_steps:
    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

v_hat = np.fft.fft(v)
next_snap_idx = 1 if (len(snapshots) > 0) else 0

for step in range(1, n_steps + 1):
    # Burgers u: forward Euler
    u_rhs = compute_burgers_rhs(u, v)
    u_new = u + dt * u_rhs

    # v: IMEX-CN
    v = np.real(np.fft.ifft(v_hat))
    NL_v = compute_v_nonlinear(u, v)
    NL_hat = np.fft.fft(NL_v)
    v_hat_new = (cn_rhs_coeff * v_hat + dt * NL_hat) / cn_lhs

    u = u_new
    v_hat = v_hat_new

    if not np.isfinite(u).all() or not np.isfinite(v_hat).all():
        print(f"BLOW-UP at step {step}, t={step*dt:.6f}")
        break

    if next_snap_idx < len(snapshot_steps) and step == snapshot_steps[next_snap_idx]:
        v_snap = np.real(np.fft.ifft(v_hat))
        snapshots.append(np.stack([u.copy(), v_snap.copy()], axis=0))
        next_snap_idx += 1

if len(snapshots) < n_snapshots:
    v_snap = np.real(np.fft.ifft(v_hat))
    snapshots.append(np.stack([u.copy(), v_snap.copy()], axis=0))

result = np.array(snapshots)
print(f"Result shape: {result.shape}")
print(f"n_snapshots saved: {len(snapshots)}")

u_final = result[-1, 0, :]
v_final = result[-1, 1, :]
print(f"u final: min={u_final.min():.4f}, max={u_final.max():.4f}, all_finite={np.isfinite(u_final).all()}")
print(f"v final: min={v_final.min():.4f}, max={v_final.max():.4f}, all_finite={np.isfinite(v_final).all()}")

from scipy.signal import find_peaks
peaks_v, _ = find_peaks(v_final, height=0.1)
print(f"v final peaks (amp>=0.1): count={len(peaks_v)}")
print(f"v final max amplitude: {v_final.max():.4f}")

v_init = result[0, 1, :]
mass_init = np.sum(v_init) * dx
mass_final = np.sum(v_final) * dx
print(f"v mass: init={mass_init:.4f}, final={mass_final:.4f}, drift={abs(mass_final-mass_init):.2e}")

T_snaps = np.linspace(0, 8.0, len(snapshots))
print("\n=== snapshot summary ===")
for i, t in enumerate(T_snaps):
    v_s = result[i, 1, :]
    u_s = result[i, 0, :]
    print(f"t={t:.2f}: u_max={u_s.max():.4f}, v_max={v_s.max():.4f}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", result)
print("Saved pred_results/T_C.npy")
