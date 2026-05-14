"""
E3 for T_A: coupled Burgers-swept-KdV.
PDE:
    u_t + 3 u u_x = -d_x (3 v^2 + v_xx)   =>  u_t = -3 u u_x - 6 v v_x - v_xxx
    v_t + 6 v v_x + v_xxx = -d_x (u v)    =>  v_t = -6 v v_x - v_xxx - d_x(u v)
Method: Fourier pseudospectral + 2/3-rule dealiasing on all nonlinear products,
explicit RK4. Single-component change vs E2: dt reduced from 5e-5 to 2e-5
to check if E2's amplitude decay is RK4 truncation accumulation or physics.
"""
import numpy as np
import os

# Grid
Nx = 256
L = 30.0
x = -15.0 + (L / Nx) * np.arange(Nx)
dx = L / Nx
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k * k
k3 = k * k * k

# 2/3 dealiasing mask
k_max = (Nx // 2)
kcut = (2.0 / 3.0) * k_max
# wavenumber index (positive) for each FFT mode
n_idx = np.fft.fftfreq(Nx, d=1.0/Nx)  # integer-ish wavenumbers
dealias = (np.abs(n_idx) <= kcut).astype(np.float64)

# IC
v0 = 2.0 * (1.0 / np.cosh(x + 5.0))**2
u0 = 0.5 * v0**2 + 0.2 * v0

# Time
T = 8.0
dt = 2e-5
n_steps = int(round(T / dt))
n_snapshots = 9  # t=0, T/8, ..., T
save_every = n_steps // (n_snapshots - 1)

def fft(a): return np.fft.fft(a)
def ifftr(A): return np.real(np.fft.ifft(A))

def deriv_hat(field_hat, mult):
    """Return d/dx via spectral with multiplier (e.g. ik, -k^2, -ik^3)."""
    return ifftr(mult * field_hat)

def nonlin_product(a, b):
    """Compute a*b with 2/3 dealiasing applied to inputs."""
    A = fft(a) * dealias
    B = fft(b) * dealias
    a_de = ifftr(A)
    b_de = ifftr(B)
    return a_de * b_de

def rhs(u, v):
    """Return du/dt, dv/dt with dealiased nonlinear products."""
    uhat = fft(u)
    vhat = fft(v)
    ux = ifftr(ik * uhat)
    vx = ifftr(ik * vhat)
    vxxx = ifftr(-1j * k3 * vhat)
    # nonlinear products (dealiased)
    uux = nonlin_product(u, ux)
    vvx = nonlin_product(v, vx)
    uv = nonlin_product(u, v)
    # d_x(u v) — take derivative of dealiased product
    uv_hat = fft(uv) * dealias
    duv_dx = ifftr(ik * uv_hat)
    # u_t = -3 u u_x - 6 v v_x - v_xxx
    du = -3.0 * uux - 6.0 * vvx - vxxx
    # v_t = -6 v v_x - v_xxx - d_x(u v)
    dv = -6.0 * vvx - vxxx - duv_dx
    return du, dv

def step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v)
    u_new = u + (dt/6.0)*(k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)
    return u_new, v_new

u = u0.copy()
v = v0.copy()

snaps_u = [u.copy()]
snaps_v = [v.copy()]
snap_times = [0.0]

abort = False
for i in range(1, n_steps + 1):
    u, v = step(u, v, dt)
    if i % 20000 == 0:
        if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
            print(f"NaN/Inf at step {i}, t={i*dt:.4f}")
            abort = True
            break
        print(f"step {i}/{n_steps}  t={i*dt:.4f}  max|v|={np.max(np.abs(v)):.4g}  max|u|={np.max(np.abs(u)):.4g}")
    if (i % save_every == 0) or (i == n_steps):
        snaps_u.append(u.copy())
        snaps_v.append(v.copy())
        snap_times.append(i * dt)
    if abort:
        break

n_snap = len(snaps_u)
out = np.zeros((n_snap, 2, Nx), dtype=np.float64)
for j in range(n_snap):
    out[j, 0, :] = snaps_u[j]
    out[j, 1, :] = snaps_v[j]

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", out)
print(f"\nsaved pred_results/T_A.npy, shape={out.shape}")
print(f"snap_times={snap_times}")
print(f"final max|v|={np.max(np.abs(v)):.4g}  final max|u|={np.max(np.abs(u)):.4g}")
print(f"v finite: {np.all(np.isfinite(v))}  u finite: {np.all(np.isfinite(u))}")
print(f"mass(v) initial={np.sum(v0)*dx:.6f}  final={np.sum(v)*dx:.6f}")
fv = v
peaks = 0
for j in range(Nx):
    jm = (j - 1) % Nx
    jp = (j + 1) % Nx
    if fv[j] > fv[jm] and fv[j] > fv[jp] and fv[j] > 0.1:
        peaks += 1
print(f"local maxima (>0.1) in final v: {peaks}")
print(f"peak v = {np.max(v):.4f}")
print(f"min v = {np.min(v):.4f}")
