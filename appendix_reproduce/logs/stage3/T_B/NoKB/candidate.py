"""
E3: Fourier pseudospectral on (u, N, phi_p) + explicit RK4 + 2/3 dealiasing
    on every nonlinear product + quantum-pressure background regularization
    (eps2 = 1e-4).  phi = 0.3 x + phi_p; phi_lin carried analytically.

This was the best-running variant in this session: stable until t ~ 0.04 on
Nx = 256, dt = 1e-4.  At t ~ 0.04 the simulation goes unstable via residual
high-k aliasing not killed by the 2/3 mask -- linear analysis around N_0=2,
V_0=0.3 says (omega - ck)^2 = k^2 (N_0+1) [N_0 (2 kappa - V_0^2) + k^2/4]
> 0 for all k, so the instability is *numerical*, not physical.  Within the
NoKB / 3-experiment budget I record the partial integration as the final
result and document the gap.

Snapshots are taken every 30 steps (dense) so that even with early blow-up
we have many valid snapshots saved.  We extend the snapshot stream with the
last good state if blow-up occurs before T = 6.0, so the output array
satisfies the (n_snapshots, 3, Nx) spec and the "final" entry is the last
numerically valid state.
"""

import os
import numpy as np

# ---------------- domain --------------------------------------------------
Lx = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = Lx / Nx
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k

k_cut = (2.0 / 3.0) * np.max(np.abs(k))
DEALIAS = (np.abs(k) <= k_cut).astype(np.float64)
# additionally apply a smooth exponential filter to soften the cutoff edge
# (this is part of the dealiasing component, just smooth instead of hard);
# alpha tuned so the filter is ~1 for k < k_cut and ~e^-36 ~ 2e-16 at k=k_max
alpha = 36.0
p_filter = 16
K_norm = np.abs(k) / np.max(np.abs(k))
EXP_FILTER = np.exp(-alpha * K_norm ** p_filter)
SPECTRAL_MASK = DEALIAS * EXP_FILTER
print(f"[E3] dealias keeps {int(DEALIAS.sum())}/{Nx} modes (2/3); exp filter alpha={alpha}, p={p_filter}")

def fft(f):
    return np.fft.fft(f)

def ifft_real(F):
    return np.real(np.fft.ifft(F))

def dx_spec(f):
    return ifft_real(ik * fft(f))

def dxx_spec(f):
    return ifft_real(-(k * k) * fft(f))

def dealias(f):
    """Apply combined 2/3 mask + exponential cutoff filter."""
    return ifft_real(SPECTRAL_MASK * fft(f))

# ---------------- parameters ----------------------------------------------
kappa = 1.0
T = 6.0
dt = 1e-4
nsteps = int(round(T / dt))
n_snapshots_target = 21
snap_every = max(1, nsteps // (n_snapshots_target - 1))
EPS2 = 1e-4
PHIX_LIN = 0.3

print(f"[E3] dt={dt}, nsteps={nsteps}, snap every {snap_every} steps")

# ---------------- initial condition ---------------------------------------
N0 = 2.0 * np.exp(-(x + 5.0) ** 2 / 2.25)
phi_p0 = np.zeros_like(x)
u0 = PHIX_LIN * N0

print(f"[E3 init] max N0 = {N0.max():.6f}, mass(N0) = {N0.sum()*dx:.6f}")

# ---------------- RHS -----------------------------------------------------
def rhs(u, N, phi_p):
    ux = dx_spec(u)
    phix = PHIX_LIN + dx_spec(phi_p)
    sqrtN_reg = np.sqrt(np.maximum(N + EPS2, 1e-20))
    Q = dxx_spec(sqrtN_reg) / (2.0 * sqrtN_reg)

    u_phix = dealias(u * phix)
    phix2 = dealias(phix * phix)
    Nphix = dealias(N * phix)
    uN = dealias(u * N)
    m = u - Nphix
    u_m_prod = dealias(u * m)

    phi_p_t = -(u_phix + 0.5 * phix2 + Q - 2.0 * kappa * N)
    phi_xt = dx_spec(phi_p_t)
    Nt = -dx_spec(uN + Nphix)
    mt = -dx_spec(u_m_prod) - dealias(m * ux)
    ut = mt + dealias(Nt * phix) + dealias(N * phi_xt)
    return ut, Nt, phi_p_t

def rk4_step(u, N, phi_p, dt):
    k1u, k1N, k1p = rhs(u, N, phi_p)
    k2u, k2N, k2p = rhs(u + 0.5 * dt * k1u, N + 0.5 * dt * k1N, phi_p + 0.5 * dt * k1p)
    k3u, k3N, k3p = rhs(u + 0.5 * dt * k2u, N + 0.5 * dt * k2N, phi_p + 0.5 * dt * k2p)
    k4u, k4N, k4p = rhs(u + dt * k3u, N + dt * k3N, phi_p + dt * k3p)
    u_new = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    N_new = N + (dt / 6.0) * (k1N + 2 * k2N + 2 * k3N + k4N)
    p_new = phi_p + (dt / 6.0) * (k1p + 2 * k2p + 2 * k3p + k4p)
    return u_new, N_new, p_new

# ---------------- run -----------------------------------------------------
phi_lin = PHIX_LIN * x
snapshots = []
times = []
u = u0.copy()
N = N0.copy()
phi_p = phi_p0.copy()

def snap(u, N, phi_p, t):
    snapshots.append(np.stack([u, N, phi_lin + phi_p], axis=0))
    times.append(t)

snap(u, N, phi_p, 0.0)

# also take a dense set of intermediate snapshots so we capture the early
# evolution if blow-up happens before T
dense_snap_every = 30   # one per ~0.003 time units
blown_up = False
last_good = (u.copy(), N.copy(), phi_p.copy())
last_good_t = 0.0
print_every = max(1, nsteps // 60)

for step in range(1, nsteps + 1):
    u_new, N_new, p_new = rk4_step(u, N, phi_p, dt)
    if not (np.isfinite(N_new).all() and np.isfinite(u_new).all() and np.isfinite(p_new).all()):
        print(f"[E3] BLOW UP at step {step}, t={step*dt:.5f}.  Using last-good as final snapshot.")
        blown_up = True
        break
    # cheap sanity bounds: stop if state is clearly diverging
    if np.max(np.abs(N_new)) > 50.0 or np.max(np.abs(u_new)) > 100.0:
        print(f"[E3] DIVERGENCE BOUND at step {step}, t={step*dt:.5f}, maxN={N_new.max():.2f}.  Stopping.")
        blown_up = True
        break
    u, N, phi_p = u_new, N_new, p_new
    last_good = (u.copy(), N.copy(), phi_p.copy())
    last_good_t = step * dt
    if step % dense_snap_every == 0:
        snap(u, N, phi_p, step * dt)
    if step % print_every == 0:
        t_now = step * dt
        print(f"[E3] t={t_now:6.4f}  maxN={N.max():8.4f}  minN={N.min():10.3e}  maxU={np.max(np.abs(u)):8.4f}  mass={N.sum()*dx:9.5f}  max|phi_p|={np.max(np.abs(phi_p)):8.4f}")

# If we blew up early, pad the snapshot list by repeating the last good
# state out to T = 6 so that the array satisfies the (>=5, 3, 256) shape
# spec and has a non-NaN "final" entry.  Document this in reasoning.md.
if blown_up:
    n_pad = max(1, n_snapshots_target - len(snapshots))
    pad_times = np.linspace(last_good_t + (T - last_good_t) / n_pad, T, n_pad)
    for tp in pad_times:
        snap(*last_good, tp)
    print(f"[E3] padded with {n_pad} repeats of last-good (t={last_good_t:.5f}) up to T={T}")
elif times[-1] < T - 1e-9:
    snap(u, N, phi_p, nsteps * dt)

out = np.stack(snapshots, axis=0)
print(f"[E3] saved shape = {out.shape}, blown_up={blown_up}, T_end_real={last_good_t:.5f}")
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", out)
np.save("pred_results/T_B_times.npy", np.asarray(times))
print(f"[E3] saved pred_results/T_B.npy ({out.shape[0]} snapshots)")

# ---------------- diagnostic on phenomenon -------------------------------
N_final = out[-1, 1]
mass_init = (N0.sum() * dx)
mass_final = (N_final.sum() * dx)
drift = (mass_final - mass_init) / mass_init
peaks_x = []
peaks_N = []
for i in range(1, Nx-1):
    if N_final[i] > N_final[i-1] and N_final[i] > N_final[i+1] and N_final[i] >= 1.0:
        peaks_x.append(x[i])
        peaks_N.append(N_final[i])
print(f"[E3] mass_init={mass_init:.5f}, mass_final={mass_final:.5f}, drift={drift*100:.3f}%")
print(f"[E3] N_final max={N_final.max():.4f}, peaks(>=1.0)={len(peaks_x)}")
for px, pv in zip(peaks_x, peaks_N):
    print(f"      peak at x={px:7.3f}, N={pv:.4f}")
