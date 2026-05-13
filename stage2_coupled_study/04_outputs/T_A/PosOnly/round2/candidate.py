"""
Coupled Burgers-swept-KdV soliton stability solver. Round 2.
Method: Fourier pseudospectral IMEX-Crank-Nicolson with 2/3 dealiasing.
  - Dispersive term v_xxx handled implicitly (CN denominator).
  - All nonlinear and coupling terms handled explicitly (Adams-Bashforth 2-step after 1 Euler step).
  - Dealiasing mask applied consistently at all spectral derivative points.
  - Bug fix from r1: dealias_mask was referenced before definition in the main loop.
    Now all references use the module-level 'dealias' array, consistently named.
"""

import numpy as np
import os

# ---------- domain ----------
L = 30.0          # x in [-15, 15]
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# ---------- wavenumbers ----------
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)

# ---------- dealiasing mask (2/3 rule) ----------
k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)

# ---------- time parameters ----------
T_final = 8.0
dt = 0.0005
n_steps = int(round(T_final / dt))   # 16000

# ---------- snapshots: 9 evenly spaced from t=0 to T_final ----------
n_snapshots = 9
snapshot_steps = set(int(round(i / (n_snapshots - 1) * n_steps))
                     for i in range(n_snapshots))
snapshot_steps.add(n_steps)          # guarantee final step is captured
snapshot_list = sorted(snapshot_steps)

# ---------- initial condition ----------
v = 2.0 / np.cosh(x + 5.0)**2
u = 0.5 * v**2 + 0.2 * v


def dx_spec(f):
    """Spectral x-derivative with dealiasing."""
    return np.real(np.fft.ifft(1j * k * dealias * np.fft.fft(f)))


def dx3_hat(f_hat):
    """Return (ik)^3 * dealiased f_hat (stays in spectral space)."""
    return (1j * k)**3 * dealias * f_hat


def rhs_u(u, v):
    """Explicit RHS for u: -3 u u_x - d/dx(3v^2 + v_xx)."""
    v_hat = np.fft.fft(v) * dealias
    v_xx = np.real(np.fft.ifft((1j * k)**2 * v_hat))
    src = 3.0 * v**2 + v_xx
    return -3.0 * u * dx_spec(u) - dx_spec(src)


def rhs_v_explicit(u, v):
    """Explicit RHS for v: -6 v v_x - d/dx(u v).  (v_xxx handled implicitly.)"""
    return -6.0 * v * dx_spec(v) - dx_spec(u * v)


# ---- IMEX-CN for v (dispersive term implicit, nonlinear explicit) ----
# v_t + v_xxx = N(u, v)
# CN: (v^{n+1} - v^n)/dt + (v^{n+1}_xxx + v^n_xxx)/2 = N^n
# => (1 + dt/2 * (ik)^3) v_hat^{n+1} = (1 - dt/2 * (ik)^3) v_hat^n + dt * N_hat^n

denom_v = 1.0 + 0.5 * dt * (1j * k)**3 * dealias
numer_coeff = 1.0 - 0.5 * dt * (1j * k)**3 * dealias

# ---------- storage for Adams-Bashforth 2 ----------
rhs_u_prev = None
rhs_v_prev = None

# ---------- snapshot storage ----------
snapshots = []   # list of (step, u_copy, v_copy)


def save_snap(step, u, v):
    snapshots.append((step, u.copy(), v.copy()))


# ---------- time loop ----------
save_snap(0, u, v)

for step in range(1, n_steps + 1):
    # --- explicit RHS at current time ---
    Ru = rhs_u(u, v)
    Rv = rhs_v_explicit(u, v)

    # --- Adams-Bashforth 2 for u; IMEX-CN for v ---
    if rhs_u_prev is None:
        # First step: forward Euler
        u_new = u + dt * Ru

        v_hat = np.fft.fft(v) * dealias
        N_hat = np.fft.fft(Rv) * dealias
        v_hat_new = (numer_coeff * v_hat + dt * N_hat) / denom_v
        v_new = np.real(np.fft.ifft(v_hat_new))
    else:
        # Adams-Bashforth 2 for u
        u_new = u + dt * (1.5 * Ru - 0.5 * rhs_u_prev)

        # AB2 predictor for the explicit v part
        v_hat = np.fft.fft(v) * dealias
        N_hat = np.fft.fft(1.5 * Rv - 0.5 * rhs_v_prev) * dealias
        v_hat_new = (numer_coeff * v_hat + dt * N_hat) / denom_v
        v_new = np.real(np.fft.ifft(v_hat_new))

    rhs_u_prev = Ru
    rhs_v_prev = Rv

    u = u_new
    v = v_new

    if step in snapshot_list:
        save_snap(step, u, v)

# ---------- assemble and save ----------
# Sort by step and build array (n_snapshots, 2, Nx)
snapshots.sort(key=lambda t: t[0])
arr = np.stack([[s[1], s[2]] for s in snapshots], axis=0)   # (n_snap, 2, 256)

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_A.npy")
np.save(out_path, arr)
print(f"Saved {arr.shape} to {out_path}")
print(f"Final u: max={u.max():.4f}, min={u.min():.4f}")
print(f"Final v: max={v.max():.4f}, min={v.min():.4f}")
