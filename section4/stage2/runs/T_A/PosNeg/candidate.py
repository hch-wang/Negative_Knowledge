"""
E3: IMEX-CN + 2/3 dealiasing — single-component upgrade over E2.
v equation: CN on v_xxx (implicit), explicit on nonlinear/coupling.
u equation: forward Euler on full RHS.
2/3 dealiasing on ALL nonlinear products (v*v_x, u*v, u*u_x).

PDE:
  u_t + 3 u u_x = -d/dx(3 v^2 + v_xx) = -6 v v_x - v_xxx
  v_t + 6 v v_x + v_xxx = -d/dx(u v)

IC: v0 = 2 sech^2(x+5); u0 = 0.5 v0^2 + 0.2 v0
"""
import numpy as np
import os

# --- grid ---
Nx = 256
L = 30.0
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = -1j * (k**3)

# 2/3 dealiasing mask
kmax = np.max(np.abs(k))
k_cut = (2.0 / 3.0) * kmax
dealias = (np.abs(k) <= k_cut).astype(float)

# --- IC ---
v0 = 2.0 * (1.0 / np.cosh(x + 5.0))**2
u0 = 0.5 * v0**2 + 0.2 * v0

# --- time ---
T = 8.0
dt = 2e-4
Nt = int(round(T / dt))
n_snapshots = 9
snap_steps = np.linspace(0, Nt, n_snapshots, dtype=int)
snap_set = set(snap_steps.tolist())

cn_num = 1.0 - 0.5 * dt * ik3
cn_den = 1.0 + 0.5 * dt * ik3

def dealias_field(f):
    """Project a real field to dealiased band."""
    fh = np.fft.fft(f) * dealias
    return np.real(np.fft.ifft(fh))

def dx_spec_of_field(f):
    fh = np.fft.fft(f)
    return np.real(np.fft.ifft(ik * fh))

def dxxx_spec_of_field(f):
    fh = np.fft.fft(f)
    return np.real(np.fft.ifft(ik3 * fh))

def dx_of_product(a, b):
    """d/dx(a*b) with 2/3 dealiasing applied to the product."""
    p = a * b
    p_hat = np.fft.fft(p) * dealias
    return np.real(np.fft.ifft(ik * p_hat))

def vvx_dealiased(v):
    """6 v v_x with dealiased product (use d/dx(v^2)/2 form for less aliasing) — but 6vv_x = 3 d/dx(v^2).
    Use the conservative form 3 d/dx(v^2) with dealiasing on v^2."""
    v_sq_hat = np.fft.fft(v * v) * dealias
    return 3.0 * np.real(np.fft.ifft(ik * v_sq_hat))

def uux_dealiased(u):
    """3 u u_x = (3/2) d/dx(u^2)."""
    u_sq_hat = np.fft.fft(u * u) * dealias
    return 1.5 * np.real(np.fft.ifft(ik * u_sq_hat))

def nonlinear_v(u, v):
    # N_v = -6 v v_x - d/dx(u v)
    return -vvx_dealiased(v) - dx_of_product(u, v)

def rhs_u(u, v):
    # u_t = -3 u u_x - 6 v v_x - v_xxx
    return -uux_dealiased(u) - vvx_dealiased(v) - dxxx_spec_of_field(v)

def imex_step(u, v, dt):
    Nv = nonlinear_v(u, v)
    Nu = rhs_u(u, v)
    u_new = u + dt * Nu
    v_hat = np.fft.fft(v)
    Nv_hat = np.fft.fft(Nv)
    v_hat_new = (v_hat * cn_num + dt * Nv_hat) / cn_den
    v_new = np.real(np.fft.ifft(v_hat_new))
    return u_new, v_new

# --- propagate ---
u = u0.copy()
v = v0.copy()

snaps = [np.stack([u.copy(), v.copy()], axis=0)]
snap_set.discard(0)

blew_up = False
for step in range(1, Nt + 1):
    u, v = imex_step(u, v, dt)
    if step in snap_set:
        snaps.append(np.stack([u.copy(), v.copy()], axis=0))
        snap_set.discard(step)
        umax = np.nanmax(np.abs(u))
        vmax = np.nanmax(np.abs(v))
        mass_v = float(np.sum(v) * dx)
        print(f"step={step} t={step*dt:.3f} |u|max={umax:.3e} |v|max={vmax:.3e} mass_v={mass_v:.4f}")
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)) or np.nanmax(np.abs(v)) > 1e4:
        print(f"BLOW-UP at step {step} t={step*dt:.4f}: |u|max={np.nanmax(np.abs(u))} |v|max={np.nanmax(np.abs(v))}")
        blew_up = True
        while len(snaps) < n_snapshots:
            snaps.append(np.stack([u.copy(), v.copy()], axis=0))
        break

arr = np.stack(snaps, axis=0)
print("=" * 60)
print("Final array shape:", arr.shape)
print("blew_up:", blew_up)
print("initial v mass:", float(np.sum(v0) * dx))
print("final   v mass:", float(np.sum(arr[-1, 1]) * dx))
print("mass drift:", float(abs(np.sum(arr[-1, 1]) - np.sum(v0)) * dx / (np.sum(v0) * dx)))
print("final |u|max:", float(np.nanmax(np.abs(arr[-1, 0]))))
print("final |v|max:", float(np.nanmax(np.abs(arr[-1, 1]))))

# Local maxima count of final v
v_final = arr[-1, 1]
maxima = 0
peak_x = []
for i in range(Nx):
    if v_final[i] > v_final[(i-1) % Nx] and v_final[i] > v_final[(i+1) % Nx]:
        maxima += 1
        peak_x.append((float(x[i]), float(v_final[i])))
print("local maxima count:", maxima)
print("top 5 peaks (x, v):", sorted(peak_x, key=lambda t: -t[1])[:5])

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", arr)
print("saved pred_results/T_A.npy")
