"""
T_A E3: single-component upgrade over E2 = reduce dt from 2e-4 to 1e-4.

Everything else identical to E2:
  - Fourier pseudospectral, Nx=256, L=30
  - 2/3-rule dealiasing on every quadratic nonlinear product
  - Classical explicit RK4
  - Same IC v0=2 sech^2(x+5), u0=0.5 v0^2 + 0.2 v0

Bank rationale (negative): kb-gardner-nonlinearCFL-amplitude-boundary and
kb-gardner-cubicTerm-tightens-nonlinearCFL warn that dt validated at lower
amplitude does NOT transfer to higher amplitude — exactly our situation,
since BKdV-S1's validated dt=2e-4 was at v0-amp 1.5 / u0-peak 1.125, while
we have v0-amp 2 / u0-peak 2.4. Empirical CFL probe confirmed dt=2e-4 blows
up at step 29 (t=0.0058) while dt=1e-4 is stable past 200 steps. Single-
component upgrade: halve dt; do not change discretization, integrator,
dealiasing, or add new physics.
"""

import os
import numpy as np

# ---------------- grid ----------------
L = 30.0
Nx = 256
dx = L / Nx
x = -15.0 + dx * np.arange(Nx)
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k

# 2/3-rule dealiasing mask
k_idx = np.fft.fftfreq(Nx, d=1.0 / Nx)
dealias_mask = (np.abs(k_idx) <= Nx // 3).astype(np.float64)

def dealias(f_hat):
    return f_hat * dealias_mask

# ---------------- IC ----------------
v0 = 2.0 * (1.0 / np.cosh(x + 5.0)) ** 2
u0 = 0.5 * v0 ** 2 + 0.2 * v0

# dealias the ICs onto the 2/3 band
u0 = np.real(np.fft.ifft(dealias(np.fft.fft(u0))))
v0 = np.real(np.fft.ifft(dealias(np.fft.fft(v0))))

# ---------------- time ----------------
T_final = 8.0
dt = 1.0e-4                              # halved from E2's 2e-4 (still inside v_xxx CFL after dealias)
n_steps = int(np.ceil(T_final / dt))
dt = T_final / n_steps

n_snapshots = 9
snap_idx = np.linspace(0, n_steps, n_snapshots).astype(int)
snap_set = set(snap_idx.tolist())

def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def dxx_spec(f):
    return np.real(np.fft.ifft((-(k ** 2)) * np.fft.fft(f)))

def dxxx_spec(f):
    return np.real(np.fft.ifft((-1j * (k ** 3)) * np.fft.fft(f)))

def dealias_product(a, b):
    """a*b with 2/3-rule dealiasing applied to the product."""
    return np.real(np.fft.ifft(dealias(np.fft.fft(a * b))))

def rhs(u, v):
    """Coupled BKdV RHS with 2/3-rule dealiasing on every quadratic product."""
    u_x = dx_spec(u)
    v_x = dx_spec(v)
    uu_x = dealias_product(u, u_x)
    v2 = dealias_product(v, v)
    v_xx = dxx_spec(v)
    du = -3.0 * uu_x - dx_spec(3.0 * v2 + v_xx)
    vv_x = dealias_product(v, v_x)
    v_xxx = dxxx_spec(v)
    uv = dealias_product(u, v)
    dv = -6.0 * vv_x - v_xxx - dx_spec(uv)
    return du, dv

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new

# ---------------- integrate ----------------
u = u0.copy()
v = v0.copy()
snapshots = [np.stack([u.copy(), v.copy()], axis=0)]
snap_t = [0.0]
blew_up = False
nan_step = -1

with np.errstate(over="warn", invalid="warn"):
    for step in range(1, n_steps + 1):
        u, v = rk4_step(u, v, dt)
        if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
            blew_up = True
            nan_step = step
            print(f"[E3] BLOW-UP at step {step}, t={step*dt:.4f}")
            break
        if step in snap_set:
            snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
            snap_t.append(step * dt)

if blew_up:
    while len(snapshots) < n_snapshots:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        snap_t.append(float("nan"))

out = np.stack(snapshots, axis=0)        # (n_snap, 2, Nx)

# ---------------- diagnostics ----------------
v_final = out[-1, 1]
u_final = out[-1, 0]
v_init = out[0, 1]
u_init = out[0, 0]
print(f"[E3] n_steps={n_steps}, dt={dt:.3e}, blew_up={blew_up}, nan_step={nan_step}")
print(f"[E3] snap_t: {[f'{t:.3f}' for t in snap_t]}")
print(f"[E3] |v|_max init={np.nanmax(np.abs(v_init)):.4f}, final={np.nanmax(np.abs(v_final)):.4f}")
print(f"[E3] |u|_max init={np.nanmax(np.abs(u_init)):.4f}, final={np.nanmax(np.abs(u_final)):.4f}")
print(f"[E3] v_min init={np.min(v_init):.4f}, final={np.min(v_final):.4f}")
print(f"[E3] v_max init={np.max(v_init):.4f}, final={np.max(v_final):.4f}")
m_v0 = np.sum(v_init) * dx
m_vT = np.sum(v_final) * dx
print(f"[E3] mass_v init={m_v0:.6f}, final={m_vT:.6f}, drift={abs(m_vT-m_v0)/abs(m_v0)*100:.4f}%")
m_u0 = np.sum(u_init) * dx
m_uT = np.sum(u_final) * dx
print(f"[E3] mass_u init={m_u0:.6f}, final={m_uT:.6f}, drift={abs(m_uT-m_u0)/abs(m_u0)*100:.4f}%")

if np.all(np.isfinite(v_final)):
    # peak count with min-amp threshold
    peaks = []
    for i in range(Nx):
        if v_final[i] > v_final[(i-1) % Nx] and v_final[i] > v_final[(i+1) % Nx] and v_final[i] > 0.3:
            peaks.append((i, x[i], v_final[i]))
    print(f"[E3] v_final local maxima (>0.3): {len(peaks)}")
    for i, xi, vi in peaks[:10]:
        print(f"        x={xi:+.2f}  v={vi:.3f}")
    v_peak = np.max(v_final)
    print(f"[E3] dominant v peak amp={v_peak:.4f} (init was {np.max(v_init):.4f}; phenomenon target >= 1.0)")

# save output
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results"), exist_ok=True)
np.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results", "T_A.npy"), out)
print(f"[E3] saved {out.shape} to pred_results/T_A.npy")
