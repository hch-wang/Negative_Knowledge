"""
E3 candidate (NoKB): coupled Burgers-swept-KdV system.

Single-component upgrade over E2 (Fourier + 2/3 dealiasing + RK4):
- Add small spectral hyperviscosity (k^8 dissipation), still inside RK4.

Reason: E2 stayed bounded only until t~3.0; between t=3 and t=3.5 the u-channel
exploded to |u|~1500 while v reached |v|~600. Mass(v) was perfectly conserved
throughout (dealiasing is symmetry-preserving), so the blow-up is NOT alias
cascade — it is the Burgers component 3 u u_x in the u-equation forming a shock
in the off-manifold dynamics (m = u - v^2/2 starts at -v^2/2, not zero, so the
system is not on the Gardner reduction). A small high-order hyperviscosity
absorbs only the smallest scales near k_max while leaving the dispersive
soliton dynamics (whose Fourier mass lives at k <~ 4) essentially untouched.

PDE (modified):
    u_t + 3 u u_x      = -d/dx (3 v^2 + v_xx) - epsilon k^8 u   (spectral)
    v_t + 6 v v_x + v_xxx = -d/dx (u v)       - epsilon k^8 v
"""
import numpy as np
import os

# ------------------------------ Grid -------------------------------------- #
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]

k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = 1j * (k ** 3)
mk2 = -(k ** 2)
k_max = np.max(np.abs(k))
k_c = (2.0 / 3.0) * k_max
dealias = (np.abs(k) <= k_c).astype(float)

# Hyperviscosity: -epsilon k^{2p} with p=4, picked so that at the dealiasing
# cutoff k=k_c the dissipation rate epsilon*k_c^8 ~ 10 (timescale 0.1 s).
p = 4
target_rate_at_kc = 10.0
epsilon = target_rate_at_kc / (k_c ** (2 * p))
hyperv = -epsilon * (k ** (2 * p))   # eigenvalue spectrum of linear hyperviscous op

# ------------------------------ IC ---------------------------------------- #
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros_like(x)

# ------------------------------ Time stepping ----------------------------- #
T_final = 6.0
dt = 5.0e-5
nsteps = int(np.round(T_final / dt))
dt = T_final / nsteps

n_snapshots = 13
snap_every = nsteps // (n_snapshots - 1)


def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))


def dxx_spec(f):
    return np.real(np.fft.ifft(mk2 * np.fft.fft(f)))


def dxxx_spec(f):
    return np.real(np.fft.ifft(ik3 * np.fft.fft(f)))


def dealiased_product(a, b):
    fa = np.fft.fft(a) * dealias
    fb = np.fft.fft(b) * dealias
    a_filt = np.real(np.fft.ifft(fa))
    b_filt = np.real(np.fft.ifft(fb))
    prod = a_filt * b_filt
    fp = np.fft.fft(prod) * dealias
    return np.real(np.fft.ifft(fp))


def rhs(u, v):
    """Full RHS = nonlinear (dealiased) + hyperviscosity (spectral)."""
    ux = dx_spec(u)
    vx = dx_spec(v)
    u_ux = dealiased_product(u, ux)
    v_vx = dealiased_product(v, vx)
    v2 = dealiased_product(v, v)
    uv = dealiased_product(u, v)
    du_nl = -3.0 * u_ux - dx_spec(3.0 * v2 + dxx_spec(v))
    dv_nl = -6.0 * v_vx - dxxx_spec(v) - dx_spec(uv)
    hu = np.real(np.fft.ifft(hyperv * np.fft.fft(u)))
    hv = np.real(np.fft.ifft(hyperv * np.fft.fft(v)))
    return du_nl + hu, dv_nl + hv


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new


# ------------------------------ Run --------------------------------------- #
u = u0.copy()
v = v0.copy()
snaps = [np.stack([u.copy(), v.copy()], axis=0)]
snap_times = [0.0]

mass_v0 = np.sum(v) * dx
amp_v0 = float(np.max(np.abs(v)))

blew_up = False
last_n = 0
for n in range(1, nsteps + 1):
    u, v = rk4_step(u, v, dt)
    last_n = n
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        print(f"BLOW-UP at step {n}, t={n*dt:.4f}")
        blew_up = True
        break
    if np.max(np.abs(v)) > 1e3:
        print(f"OVERFLOW at step {n}, t={n*dt:.4f}, max|v|={np.max(np.abs(v)):.3e}")
        blew_up = True
        break
    if n % snap_every == 0 and len(snaps) < n_snapshots:
        snaps.append(np.stack([u.copy(), v.copy()], axis=0))
        snap_times.append(n * dt)

while len(snaps) < n_snapshots:
    snaps.append(np.stack([u.copy(), v.copy()], axis=0))
    snap_times.append(last_n * dt)

out = np.stack(snaps, axis=0)
print("output shape", out.shape)
print("snap times", [f"{t:.3f}" for t in snap_times])
print(f"mass(v) initial = {mass_v0:.6f}, final = {np.sum(v)*dx:.6f}, drift = "
      f"{abs((np.sum(v)*dx - mass_v0)/mass_v0)*100:.3f}%")
print(f"max|v| init = {amp_v0:.4f}, final = {np.max(np.abs(v)):.4f}")
print(f"max|u| final = {np.max(np.abs(u)):.4f}")
print(f"hyperviscosity epsilon = {epsilon:.3e}, target rate at k_c = {target_rate_at_kc}")

vf = out[-1, 1]
peaks = []
for i in range(Nx):
    iL = (i - 1) % Nx
    iR = (i + 1) % Nx
    if vf[i] >= 0.8 and vf[i] > vf[iL] and vf[i] > vf[iR]:
        peaks.append((x[i], vf[i]))
print(f"peaks (>=0.8) in final v: {len(peaks)}")
for px, pv in peaks:
    print(f"  x={px:.3f}  v={pv:.4f}")

# intermediate diagnostics
print("\nIntermediate snapshots (t, max|v|, max|u|, mass(v) drift %):")
for i, t in enumerate(snap_times):
    ui = out[i, 0]; vi = out[i, 1]
    drift = abs((np.sum(vi)*dx - mass_v0) / mass_v0) * 100
    print(f"  t={t:.3f}  max|v|={np.max(np.abs(vi)):8.3f}  max|u|={np.max(np.abs(ui)):8.3f}  mass drift={drift:.3f}%")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", out)
print("saved pred_results/T_B.npy")
