"""
Coupled Burgers-swept-KdV: bore-soliton interaction
Task T_C, PosNeg condition - E2

PDE:
  u_t + 3 u u_x = -d/dx (3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx (u v)

Domain: x in [-15,15], periodic, Nx=256, T=8.0

Method (E2):
- Fully spectral IMEX-CN for both u and v with 2/3 dealiasing
- u: CN on viscosity+hyperviscosity (nu_u*u_xx + mu_u*d^4u/dx^4) implicit
      explicit on -3uu_x and coupling -d/dx(3v^2 + v_xx)
  → (1 + (nu_u k^2 + mu_u k^4) dt/2) u_hat^{n+1} = ...
- v: CN on v_xxx + viscosity (nu_v*v_xx + mu_v*d^4v/dx^4) implicit
      explicit on -6vv_x - d/dx(uv)
  → (1 - (ik)^3 dt/2 + (nu_v k^2 + mu_v k^4) dt/2) v_hat^{n+1} = ...

Parameters validated by pre-run testing:
  nu_u=0.5 (bore regularization), nu_v=0.01 (soliton damping),
  mu_u=0.005, mu_v=0.0001 (hyperviscosity), dt=5e-5

Bank citations:
  Positive: kb-kdv-IMEX-CN-spectral-pass, kb-gardner-G2-IMEX-CN-dealiased-stableRadiation,
            kb-kdv-noDealiasing-aliasing-artifacts (must dealias)
  Rejected: kb-burgers-fwdEuler-centralFD-Gibbs (no central FD),
            kb-kdv-IFRK4-blowup (no IFRK4),
            kb-burgers-LaxFriedrichs-longTime-dissipation (no LxF for long-time)
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')
import os

# ---- Grid ----
L = 30.0
Nx = 256
dx = L / Nx
x = -15.0 + np.arange(Nx) * dx

T_final = 8.0
dt = 5e-5
Nt = int(round(T_final / dt))
n_snapshots = 8

# Wavenumbers
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi
k2 = k ** 2
k4 = k ** 4
k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)

# Viscosity / hyperviscosity coefficients
nu_u = 0.5    # bore regularization
nu_v = 0.01   # soliton damping
mu_u = 0.005  # hyperviscosity on u
mu_v = 1e-4   # hyperviscosity on v

# IMEX-CN operators
# u: implicit = nu_u * u_xx + mu_u * d^4u/dx^4  (note: d^4/dx^4 in Fourier = -k^4)
# CN gives: (1 + (nu_u k^2 + mu_u k^4) dt/2) u_hat^{n+1} = (1 - ...) u_hat^n + dt * NL^n
cn_u_denom = 1.0 + (nu_u * k2 + mu_u * k4) * 0.5 * dt
cn_u_numer = 1.0 - (nu_u * k2 + mu_u * k4) * 0.5 * dt

# v: implicit = v_xxx + nu_v * v_xx + mu_v * d^4v/dx^4
# CN: (1 - (ik)^3 dt/2 + (nu_v k^2 + mu_v k^4) dt/2) v_hat^{n+1} = ... - dt * NL^n
ik3 = (1j * k) ** 3
cn_v_denom = 1.0 - 0.5 * dt * ik3 + (nu_v * k2 + mu_v * k4) * 0.5 * dt
cn_v_numer = 1.0 + 0.5 * dt * ik3 - (nu_v * k2 + mu_v * k4) * 0.5 * dt

# ---- Initial conditions ----
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0  # smoothed bore
v = 1.5 / np.cosh(x + 8.0) ** 2             # KdV soliton at x=-8

def explicit_nl_u_hat(u, v):
    """Explicit RHS for u in Fourier space: -3uu_x - d/dx(3v^2 + v_xx)"""
    uh = np.fft.fft(u) * dealias
    ud = np.real(np.fft.ifft(uh))
    uxd = np.real(np.fft.ifft(1j * k * uh))
    nlu_h = -3.0 * np.fft.fft(ud * uxd) * dealias

    vh = np.fft.fft(v) * dealias
    vd = np.real(np.fft.ifft(vh))
    v2h = np.fft.fft(3.0 * vd ** 2) * dealias
    vxxh = -k2 * vh
    coupling_h = -1j * k * (v2h + vxxh)

    return nlu_h + coupling_h

def explicit_nl_v_hat(v, u):
    """Explicit RHS for v in Fourier space: -6vv_x - d/dx(uv)"""
    vh = np.fft.fft(v) * dealias
    vd = np.real(np.fft.ifft(vh))
    vxd = np.real(np.fft.ifft(1j * k * vh))
    term1_h = -np.fft.fft(6.0 * vd * vxd) * dealias  # NOTE: sign negative! 6vv_x goes to RHS with minus

    uv_h = np.fft.fft(u * v) * dealias
    term2_h = -1j * k * uv_h

    return term1_h + term2_h

def step(u, v):
    """One IMEX-CN step."""
    nl_u_h = explicit_nl_u_hat(u, v)
    uh = np.fft.fft(u)
    rhs_u_h = cn_u_numer * uh + dt * nl_u_h
    u_new = np.real(np.fft.ifft(rhs_u_h / cn_u_denom * dealias))

    nl_v_h = explicit_nl_v_hat(v, u)
    vh = np.fft.fft(v)
    rhs_v_h = cn_v_numer * vh + dt * nl_v_h
    v_new = np.real(np.fft.ifft(rhs_v_h / cn_v_denom * dealias))

    return u_new, v_new

# ---- Time integration ----
snapshots = []
snap_times = []
t_snap_targets = np.linspace(0.0, T_final, n_snapshots)

snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
snap_times.append(0.0)

t = 0.0
snap_idx = 1

for n in range(Nt):
    u, v = step(u, v)
    t += dt

    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        print(f"Blow-up at t={t:.4f}")
        break

    if snap_idx < n_snapshots and t >= t_snap_targets[snap_idx] - 0.5 * dt:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        snap_times.append(t)
        snap_idx += 1
        print(f"Snapshot {snap_idx-1} t={t:.3f}: u_max={u.max():.3f} v_max={v.max():.3f}")

while len(snapshots) < n_snapshots:
    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
    snap_times.append(t)

result = np.stack(snapshots, axis=0)

# ---- Diagnostics ----
print(f"\nResult shape: {result.shape}")
print(f"Snapshot times: {[f'{tt:.3f}' for tt in snap_times]}")
u_final = result[-1, 0, :]
v_final = result[-1, 1, :]

v_max_amp = v_final.max()
u_max_abs = np.abs(u_final).max()
v_peaks = np.sum((v_final[1:-1] > v_final[:-2]) & (v_final[1:-1] > v_final[2:]))

print(f"u final: [{u_final.min():.4f}, {u_final.max():.4f}], finite={np.all(np.isfinite(u_final))}")
print(f"v final: [{v_final.min():.4f}, {v_final.max():.4f}], n_peaks={v_peaks}")
print(f"Phenomenon: v_peak>={v_max_amp:.4f}>=0.5: {v_max_amp >= 0.5}, |u_max|={u_max_abs:.4f}<5: {u_max_abs < 5.0}")

for i, (snap, tt) in enumerate(zip(snapshots, snap_times)):
    us, vs = snap[0], snap[1]
    print(f"  snap {i} t={tt:.3f}: u=[{us.min():.3f},{us.max():.3f}] v=[{vs.min():.3f},{vs.max():.3f}] finite={np.all(np.isfinite(us)) and np.all(np.isfinite(vs))}")

# Save
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "T_C.npy"), result)
print(f"\nSaved pred_results/T_C.npy shape={result.shape}")
