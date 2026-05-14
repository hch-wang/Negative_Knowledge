"""
T_B / NegOnly / E3: same as E2 (Fourier pseudospectral + RK4 + 2/3 dealias)
but with dt reduced 4x (1e-4 -> 2.5e-5). Single-component upgrade to verify
that E2's late-time soliton train is dt-converged (guards against
kb-gardner-cubicTerm-tightens-nonlinearCFL at amp=4, which is unprecedented in the bank).

PDE:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

IC: v(x,0) = 4*exp(-((x+5)^2)/2.25); u(x,0) = 0.
Domain: x in [-15, 15], Nx = 256, periodic.
T = 6.0.
"""
import numpy as np
import os

# --------- grid ---------
Nx = 256
L = 30.0
x = -15.0 + (L / Nx) * np.arange(Nx)
dx = L / Nx

# spectral wavenumbers
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * (k ** 3)

# 2/3-rule dealiasing mask
k_idx = np.fft.fftfreq(Nx, d=1.0 / Nx)
dealias_mask = (np.abs(k_idx) <= Nx / 3.0).astype(np.float64)

def dealias(f_hat):
    return f_hat * dealias_mask

# --------- IC ---------
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros_like(x)

# --------- params ---------
T = 6.0
dt = 2.5e-5  # 4x smaller than E2 for convergence check
nsteps = int(round(T / dt))
n_snapshots = 7
snap_times = np.linspace(0.0, T, n_snapshots)
snap_steps = np.round(snap_times / dt).astype(int)

# --------- spectral derivative helpers ---------
def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def d2x_spec(f):
    return np.real(np.fft.ifft(-(k ** 2) * np.fft.fft(f)))

def d3x_spec(f):
    return np.real(np.fft.ifft(-ik3 * np.fft.fft(f)))

def dealias_field(f):
    return np.real(np.fft.ifft(dealias(np.fft.fft(f))))

# --------- RHS ---------
def rhs(u, v):
    u = dealias_field(u)
    v = dealias_field(v)

    v_x = dx_spec(v)
    v_xx = d2x_spec(v)
    v_xxx = d3x_spec(v)
    u_x = dx_spec(u)

    v_sq = dealias_field(v * v)
    uv = dealias_field(u * v)
    u_ux = dealias_field(u * u_x)
    v_vx = dealias_field(v * v_x)

    inner_u_rhs = 3.0 * v_sq + v_xx
    inner_u_x = dx_spec(inner_u_rhs)

    uv_x = dx_spec(uv)

    du = -3.0 * u_ux - inner_u_x
    dv = -6.0 * v_vx - v_xxx - uv_x
    return du, dv

def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new

# --------- time loop ---------
u = u0.copy()
v = v0.copy()
snaps = np.zeros((n_snapshots, 2, Nx), dtype=np.float64)
snaps[0, 0, :] = u
snaps[0, 1, :] = v
snap_idx = 1
blew_up = False
for step in range(1, nsteps + 1):
    u, v = rk4_step(u, v, dt)
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        print(f"BLOW UP at step={step}, t={step*dt:.4f}")
        blew_up = True
        break
    if snap_idx < n_snapshots and step == snap_steps[snap_idx]:
        snaps[snap_idx, 0, :] = u
        snaps[snap_idx, 1, :] = v
        snap_idx += 1

if blew_up:
    for i in range(snap_idx, n_snapshots):
        snaps[i, 0, :] = snaps[snap_idx - 1, 0, :] if snap_idx > 0 else u0
        snaps[i, 1, :] = snaps[snap_idx - 1, 1, :] if snap_idx > 0 else v0

# --------- save ---------
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results", "T_B.npy")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
np.save(out_path, snaps)

# --------- diagnostics ---------
print(f"Saved to {out_path}; shape={snaps.shape}; blew_up={blew_up}")
mass_v_t0 = np.sum(snaps[0, 1, :]) * dx
mass_v_tT = np.sum(snaps[-1, 1, :]) * dx
print(f"mass_v(t=0)={mass_v_t0:.6f}, mass_v(t=T)={mass_v_tT:.6f}, drift={(mass_v_tT-mass_v_t0)/mass_v_t0*100:.4f}%")
mass_u_t0 = np.sum(snaps[0, 0, :]) * dx
mass_u_tT = np.sum(snaps[-1, 0, :]) * dx
print(f"mass_u(t=0)={mass_u_t0:.6f}, mass_u(t=T)={mass_u_tT:.6f}")
print(f"v_min={snaps[-1,1,:].min():.4f}, v_max={snaps[-1,1,:].max():.4f}")
print(f"u_min={snaps[-1,0,:].min():.4f}, u_max={snaps[-1,0,:].max():.4f}")
print(f"finite: u {np.all(np.isfinite(snaps[-1,0,:]))}, v {np.all(np.isfinite(snaps[-1,1,:]))}")

v_final = snaps[-1, 1, :]
peaks = []
for i in range(Nx):
    ip = (i + 1) % Nx
    im = (i - 1) % Nx
    if v_final[i] > v_final[ip] and v_final[i] > v_final[im] and v_final[i] > 0.5:
        peaks.append((i, v_final[i]))
print(f"n_peaks(v_final, thresh=0.5): {len(peaks)}")
peaks08 = [p for p in peaks if p[1] >= 0.8]
print(f"n_peaks(v_final, thresh=0.8): {len(peaks08)}; amps: {[round(p[1],3) for p in peaks08][:15]}")

# Print intermediate snapshots
for i, t in enumerate(snap_times):
    v = snaps[i, 1, :]
    u = snaps[i, 0, :]
    p08 = sum(1 for j in range(Nx) if v[j] > v[(j+1)%Nx] and v[j] > v[(j-1)%Nx] and v[j] >= 0.8)
    print(f"  t={t:.2f}: v in [{v.min():.3f},{v.max():.3f}], u in [{u.min():.3f},{u.max():.3f}], n_peaks>=0.8: {p08}")
