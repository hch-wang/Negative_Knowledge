"""
T_B / PosOnly — E2: baseline + 2/3-rule dealiasing (single-component upgrade vs E1).

PDE: coupled Burgers-swept-KdV
    u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
    v_t + 6 v v_x + v_xxx = -d_x(u v)

IC (reference): v(x,0) = 4*exp(-(x+5)^2/2.25), u(x,0) = 0
Domain: periodic [-15, 15], Nx=256, T=6.0.

Method: Fourier pseudospectral + 2/3-rule dealiasing on every nonlinear product
        (v^2, u*v, v*v_x, u*u_x) + classical explicit RK4 over the full RHS.

Stack validated by BKdV-S1 (r1, r2) at amp=1.5 and amp=3.0 for T=10.
"""
import numpy as np
import os
import time

# ---------- Grid ----------
L = 30.0
Nx = 256
x = np.linspace(-L/2, L/2, Nx, endpoint=False)
dx = L / Nx
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k * k
k3 = k * k * k

# ---------- 2/3 dealiasing mask ----------
# Zero modes with |k_idx| > Nx/3 (i.e. keep 171/256 modes around zero)
k_idx = np.fft.fftfreq(Nx, d=1.0) * Nx           # signed integer wavenumber indices
cutoff = Nx // 3
dealias_mask = (np.abs(k_idx) <= cutoff).astype(np.float64)

def dealias_product(a, b):
    """Compute a*b after low-pass filtering each factor to the 2/3 band, return product
    (then also low-pass the product to keep nonlinear injections inside the band).
    """
    a_hat = np.fft.fft(a) * dealias_mask
    b_hat = np.fft.fft(b) * dealias_mask
    af = np.real(np.fft.ifft(a_hat))
    bf = np.real(np.fft.ifft(b_hat))
    prod = af * bf
    prod_hat = np.fft.fft(prod) * dealias_mask
    return np.real(np.fft.ifft(prod_hat)), prod_hat

# ---------- IC ----------
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros_like(x)

# ---------- Time ----------
T_final = 6.0
dt = 2e-4
n_steps = int(round(T_final / dt))
n_snapshots = 25            # >= 5 snapshots required
snap_interval = max(1, n_steps // (n_snapshots - 1))

# ---------- RHS in spectral space (with 2/3 dealiasing) ----------
def rhs(u, v):
    """Compute (du/dt, dv/dt) via Fourier pseudospectral with 2/3 dealiasing.
    Eq u: u_t = -3 u u_x - 3 d_x(v^2) - d_x(v_xx)
    Eq v: v_t = -6 v v_x - v_xxx - d_x(u v)
    """
    u_hat = np.fft.fft(u) * dealias_mask
    v_hat = np.fft.fft(v) * dealias_mask

    # Linear spectral derivatives (already in the 2/3 band)
    v_xxx_hat = (1j * k3) * (-1.0) * v_hat   # d^3/dx^3 acts as (ik)^3 = -i k^3
    # Note: (ik)^3 = -i k^3. Construct directly:
    v_xxx_hat = (ik * ik * ik) * v_hat
    v_xxx = np.real(np.fft.ifft(v_xxx_hat))

    # d_x(v_xx) = i k * (ik)^2 v_hat = -i k^3 v_hat = same as v_xxx — simplification
    # explicitly: d_x(v_xx) = v_xxx, so the u equation's -d_x(v_xx) term is -v_xxx.
    # Compute via spectral pipeline to keep dealiasing consistent (linear so unaffected).
    v_xx_x = v_xxx  # mathematically identical

    # dealias_product for nonlinears
    _, v2_hat = dealias_product(v, v)
    v2_x = np.real(np.fft.ifft(ik * v2_hat))

    _, uv_hat = dealias_product(u, v)
    uv_x = np.real(np.fft.ifft(ik * uv_hat))

    # u u_x and v v_x: compute u_x, v_x in spectral (already filtered), then product+filter
    u_x = np.real(np.fft.ifft(ik * u_hat))
    v_x = np.real(np.fft.ifft(ik * v_hat))
    uux, _ = dealias_product(u, u_x)
    vvx, _ = dealias_product(v, v_x)

    du_dt = -3.0 * uux - 3.0 * v2_x - v_xx_x
    dv_dt = -6.0 * vvx - v_xxx - uv_x

    # Final safety: low-pass the rhs as well so we never leak energy outside the 2/3 band
    du_dt = np.real(np.fft.ifft(np.fft.fft(du_dt) * dealias_mask))
    dv_dt = np.real(np.fft.ifft(np.fft.fft(dv_dt) * dealias_mask))

    return du_dt, dv_dt


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new


# ---------- Integrate ----------
u = u0.copy()
v = v0.copy()
mass_v_init = np.sum(v) * dx

snapshots = []
times = []
snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
times.append(0.0)

t0 = time.time()
diverged = False
for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if not np.all(np.isfinite(u)) or not np.all(np.isfinite(v)):
        print(f"BLOWUP at step {step}, t={step*dt:.4f}")
        diverged = True
        break
    if step % snap_interval == 0 or step == n_steps:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        times.append(step * dt)

elapsed = time.time() - t0
arr = np.stack(snapshots, axis=0)  # (n_snap, 2, Nx)

# ---------- Diagnostics ----------
print(f"Elapsed: {elapsed:.2f}s, snapshots={arr.shape}, diverged={diverged}")
if not diverged:
    mass_v_final = np.sum(v) * dx
    print(f"mass_v init={mass_v_init:.6e}, final={mass_v_final:.6e}, drift={(mass_v_final-mass_v_init)/mass_v_init*100:.4f}%")
    print(f"|v|_inf final={np.max(np.abs(v)):.4f}, |u|_inf final={np.max(np.abs(u)):.4f}")
    # Peak-count diagnostic: peaks above 0.8
    vfin = v
    thresh = 0.8
    # local maxima
    peaks_idx = []
    for i in range(Nx):
        if vfin[i] > thresh and vfin[i] > vfin[(i - 1) % Nx] and vfin[i] > vfin[(i + 1) % Nx]:
            peaks_idx.append(i)
    print(f"Final v: {len(peaks_idx)} peaks above {thresh} at positions x={[x[i] for i in peaks_idx]}, amps={[float(vfin[i]) for i in peaks_idx]}")

# ---------- Save ----------
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", arr.astype(np.float64))
print(f"Saved pred_results/T_B.npy with shape {arr.shape}, times[0:3]={times[:3]}, times[-1]={times[-1]:.4f}")
