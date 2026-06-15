"""
BKdV-S1 Round 3: same solver as Round 2 (Fourier spectral + 2/3-rule
dealiasing + classical RK4, dt = 2e-4). Single change vs R2: push the IC
amplitude to amp = 3.0, the top of the required range [1, 3].

Goal: test whether the R2 stack is amp-robust or develops a second
failure mode at high amplitude.
"""

import time
import numpy as np

L = 30.0
Nx = 256
dx = L / Nx
x = -15.0 + dx * np.arange(Nx)

k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k ** 2
k3 = k ** 3

kx_idx = np.fft.fftfreq(Nx, d=1.0/Nx).astype(int)
cutoff = Nx // 3
dealias_mask = (np.abs(kx_idx) <= cutoff).astype(float)
print(f"[init] 2/3-dealias: keeping {int(dealias_mask.sum())} of {Nx} modes (cutoff |k_idx|<={cutoff})", flush=True)

def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))

def dxx_spec(f):
    return np.real(np.fft.ifft(-k2 * np.fft.fft(f)))

def dxxx_spec(f):
    return np.real(np.fft.ifft(-1j * k3 * np.fft.fft(f)))

def dealias(f):
    return np.real(np.fft.ifft(dealias_mask * np.fft.fft(f)))

def dx_dealiased_product(*fs):
    prod = fs[0].copy()
    for g in fs[1:]:
        prod = prod * g
    prod = dealias(prod)
    return np.real(np.fft.ifft(ik * np.fft.fft(prod)))

def rhs(state):
    u, v = state
    u = dealias(u)
    v = dealias(v)
    u_x = dx_spec(u)
    v_x = dx_spec(v)
    v_xx = dxx_spec(v)
    v_xxx = dxxx_spec(v)
    rhs_u = -3.0 * dealias(u * u_x) - 3.0 * dx_dealiased_product(v, v) - dx_spec(v_xx)
    rhs_v = -6.0 * dealias(v * v_x) - v_xxx - dx_dealiased_product(u, v)
    return np.stack([rhs_u, rhs_v], axis=0)

def step_rk4(state, dt):
    k1 = rhs(state)
    k2_ = rhs(state + 0.5 * dt * k1)
    k3_ = rhs(state + 0.5 * dt * k2_)
    k4_ = rhs(state + dt * k3_)
    return state + (dt / 6.0) * (k1 + 2 * k2_ + 2 * k3_ + k4_)

def diagnostics(state):
    u, v = state
    mass_v = np.sum(v) * dx
    mass_u = np.sum(u) * dx
    energy = 0.5 * np.sum(u * u + v * v) * dx
    sup_u = np.max(np.abs(u))
    sup_v = np.max(np.abs(v))
    sup = max(sup_u, sup_v)
    finite = np.all(np.isfinite(u)) and np.all(np.isfinite(v))
    Vhat = np.fft.fft(v)
    psd = np.abs(Vhat) ** 2
    total = psd.sum()
    # near-band-edge concentration: fraction of |v_hat|^2 in top 10% of resolved band
    edge_band = (np.abs(kx_idx) > 0.9 * cutoff) & (np.abs(kx_idx) <= cutoff)
    edge_frac = float(psd[edge_band].sum() / total) if total > 0 else 0.0
    tail_frac = float(psd[np.abs(kx_idx) > cutoff].sum() / total) if total > 0 else 0.0
    return dict(mass_u=mass_u, mass_v=mass_v, energy=energy,
                sup=sup, sup_u=sup_u, sup_v=sup_v,
                finite=finite, tail_frac=tail_frac, edge_frac=edge_frac)

# IC at the top of the required amp range
amp = 3.0
v0 = amp * (1.0 / np.cosh(x + 5.0)) ** 2
u0 = 0.5 * v0 ** 2
state = np.stack([u0, v0], axis=0)
init = diagnostics(state)
print(f"[init] dx={dx:.4e} amp={amp} mass_v={init['mass_v']:.6e} energy={init['energy']:.6e} sup_u={init['sup_u']:.4e} sup_v={init['sup_v']:.4e}", flush=True)

T = 10.0
dt = 2.0e-4
nsteps = int(round(T / dt))
print(f"[time] dt={dt:.4e} nsteps={nsteps}", flush=True)

# very tight cadence to capture early dynamics if blow-up develops
report_every = max(1, nsteps // 200)
t0 = time.time()
blowup_t = None
edge_alert_t = None
for n in range(nsteps):
    state = step_rk4(state, dt)
    if (n + 1) % report_every == 0 or n == nsteps - 1:
        d = diagnostics(state)
        t = (n + 1) * dt
        print(f"[t={t:7.4f}] mass_v={d['mass_v']:+.4e} energy={d['energy']:.4e} sup_u={d['sup_u']:.4e} sup_v={d['sup_v']:.4e} edge_frac={d['edge_frac']:.3e} finite={d['finite']}", flush=True)
        if edge_alert_t is None and d['edge_frac'] > 1e-4:
            edge_alert_t = t
            print(f"[EDGE_ALERT] energy at top 10% of resolved band exceeds 1e-4 at t={t:.4f}", flush=True)
        if not d['finite'] or d['sup'] > 1e6:
            blowup_t = t
            print(f"[BLOWUP] at t={t:.4f}", flush=True)
            break

elapsed = time.time() - t0
final = diagnostics(state)
print(f"[final] t_final={(n+1)*dt:.4f} sup_u={final['sup_u']:.4e} sup_v={final['sup_v']:.4e} mass_v={final['mass_v']:+.4e} energy={final['energy']:.4e} finite={final['finite']} elapsed={elapsed:.2f}s", flush=True)
print(f"[summary] blowup_t={blowup_t} edge_alert_t={edge_alert_t} reached_T10={(blowup_t is None and (n+1)*dt >= T - 1e-9)}", flush=True)
