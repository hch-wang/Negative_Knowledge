"""
BKdV-S1 Round 2: Round 1 stack + 2/3-rule dealiasing.

Only change vs Round 1: every nonlinear product (v², u·v, v·v_x, u·u_x)
is computed via pad/truncate so that wavenumbers > 2/3 of Nyquist are zeroed
before the IFFT, and the resulting field is in the 2/3 band.

Time integrator and dt are unchanged: classical RK4 over the entire RHS,
v_xxx treated explicitly, dt = 2e-4.
"""

import time
import numpy as np

# ------------------------------------------------------------
# Grid & operators
# ------------------------------------------------------------
L = 30.0
Nx = 256
dx = L / Nx
x = -15.0 + dx * np.arange(Nx)

k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k2 = k ** 2
k3 = k ** 3

# 2/3-rule dealiasing mask: keep |k_index| <= Nx/3
kx_idx = np.fft.fftfreq(Nx, d=1.0/Nx).astype(int)  # 0..Nx/2-1, -Nx/2..-1
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
    """zero modes above 2/3 Nyquist"""
    return np.real(np.fft.ifft(dealias_mask * np.fft.fft(f)))

def dx_dealiased_product(*fs):
    """compute d/dx of a product of (already-dealiased) fields, with dealiased input"""
    prod = fs[0].copy()
    for g in fs[1:]:
        prod = prod * g
    prod = dealias(prod)
    return np.real(np.fft.ifft(ik * np.fft.fft(prod)))

# ------------------------------------------------------------
# RHS with dealiasing on every nonlinear product
# ------------------------------------------------------------
def rhs(state):
    u, v = state
    # pre-dealias state to keep it in the 2/3 band before any product
    u = dealias(u)
    v = dealias(v)

    u_x = dx_spec(u)
    v_x = dx_spec(v)
    v_xx = dxx_spec(v)
    v_xxx = dxxx_spec(v)

    # u_t = -3 u u_x - d/dx(3 v² + v_xx)
    rhs_u = -3.0 * dealias(u * u_x) - 3.0 * dx_dealiased_product(v, v) - dx_spec(v_xx)
    # v_t = -6 v v_x - v_xxx - d/dx(u v)
    rhs_v = -6.0 * dealias(v * v_x) - v_xxx - dx_dealiased_product(u, v)
    return np.stack([rhs_u, rhs_v], axis=0)

def step_rk4(state, dt):
    k1 = rhs(state)
    k2_ = rhs(state + 0.5 * dt * k1)
    k3_ = rhs(state + 0.5 * dt * k2_)
    k4_ = rhs(state + dt * k3_)
    return state + (dt / 6.0) * (k1 + 2 * k2_ + 2 * k3_ + k4_)

# ------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------
def diagnostics(state):
    u, v = state
    mass_v = np.sum(v) * dx
    mass_u = np.sum(u) * dx
    energy = 0.5 * np.sum(u * u + v * v) * dx
    sup = max(np.max(np.abs(u)), np.max(np.abs(v)))
    finite = np.all(np.isfinite(u)) and np.all(np.isfinite(v))
    # high-k tail: fraction of |v_hat|^2 above Nx/3
    Vhat = np.fft.fft(v)
    psd = np.abs(Vhat) ** 2
    total = psd.sum()
    high = psd[np.abs(kx_idx) > cutoff].sum()
    tail_frac = float(high / total) if total > 0 else 0.0
    return dict(mass_u=mass_u, mass_v=mass_v, energy=energy, sup=sup, finite=finite, tail_frac=tail_frac)

# ------------------------------------------------------------
# IC
# ------------------------------------------------------------
amp = 1.5
v0 = amp * (1.0 / np.cosh(x + 5.0)) ** 2
u0 = 0.5 * v0 ** 2
state = np.stack([u0, v0], axis=0)
init = diagnostics(state)
print(f"[init] dx={dx:.4e} amp={amp} mass_v={init['mass_v']:.6e} energy={init['energy']:.6e} sup={init['sup']:.4e}", flush=True)

# ------------------------------------------------------------
# Time integration
# ------------------------------------------------------------
T = 10.0
dt = 2.0e-4
nsteps = int(round(T / dt))
print(f"[time] dt={dt:.4e} nsteps={nsteps}", flush=True)

# tighter report cadence so we see the early blow-up if it happens
report_every = max(1, nsteps // 100)
t0 = time.time()
blowup_t = None
for n in range(nsteps):
    state = step_rk4(state, dt)
    if (n + 1) % report_every == 0 or n == nsteps - 1:
        d = diagnostics(state)
        t = (n + 1) * dt
        print(f"[t={t:7.4f}] mass_v={d['mass_v']:+.4e} energy={d['energy']:.4e} sup={d['sup']:.4e} tail_frac={d['tail_frac']:.3e} finite={d['finite']}", flush=True)
        if not d['finite'] or d['sup'] > 1e6:
            blowup_t = t
            print(f"[BLOWUP] at t={t:.4f}", flush=True)
            break

elapsed = time.time() - t0
final = diagnostics(state)
print(f"[final] t_final={(n+1)*dt:.4f} sup={final['sup']:.4e} mass_v={final['mass_v']:+.4e} energy={final['energy']:.4e} finite={final['finite']} elapsed={elapsed:.2f}s", flush=True)
print(f"[summary] blowup_t={blowup_t} reached_T10={(blowup_t is None and (n+1)*dt >= T - 1e-9)}", flush=True)
