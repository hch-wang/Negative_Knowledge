"""
BKdV-S2 Round 2 (E2): IC change — test IC-invariance of conserved quantities.

Identical solver stack as round1.  Only the IC changes:
  - v0 = 0.6 * cos(2*pi*x/L) + 0.3 * sin(4*pi*x/L)
  - u0 = 0.4 * sin(2*pi*x/L) + 0.2 * cos(6*pi*x/L)

This is a smooth, periodic, small-amplitude random-looking IC with:
  - int u dx != 0 baseline? Actually pure cos/sin on [-L/2,L/2] integrate to 0.
    So I add a constant offset:
        u0 += 0.15
        v0 += 0.10
    That gives nontrivial means for both u and v, exposing whether C1, C2
    really are structurally conserved (not just zero-preserving).

T = 10 (shorter; we just need to see drift patterns).
"""
import os, sys, time
import numpy as np

# -----------------------------------------------------------
# Grid & spectral operators (same as round1)
# -----------------------------------------------------------
L  = 30.0
Nx = 256
dx = L / Nx
x  = -15.0 + dx * np.arange(Nx)

k   = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik  = 1j * k
k3  = k ** 3

kmax    = np.max(np.abs(k))
mask_23 = (np.abs(k) <= (2.0/3.0) * kmax).astype(float)

def fft(a):  return np.fft.fft(a)
def ifft(A): return np.real(np.fft.ifft(A))

def dx_real(a):
    return ifft(ik * fft(a))

def dxx_real(a):
    return ifft(-(k**2) * fft(a))

def dealias_product(a, b):
    P = fft(a * b)
    return ifft(P * mask_23)

def N_u(u, v):
    u2     = dealias_product(u, u)
    v2     = dealias_product(v, v)
    v_xx   = dxx_real(v)
    d_u2   = ifft(ik * fft(u2))
    d_v2   = ifft(ik * fft(v2))
    d_vxx  = ifft(ik * fft(v_xx))
    return -1.5 * d_u2 - 3.0 * d_v2 - d_vxx

def N_v(u, v):
    v2     = dealias_product(v, v)
    uv     = dealias_product(u, v)
    d_v2   = ifft(ik * fft(v2))
    d_uv   = ifft(ik * fft(uv))
    return -3.0 * d_v2 - d_uv

L_op  = 1j * (k ** 3)

def step(u, v, dt):
    denom = 1.0 - 0.5 * dt * L_op
    num   = 1.0 + 0.5 * dt * L_op
    denom_h = 1.0 - 0.25 * dt * L_op
    num_h   = 1.0 + 0.25 * dt * L_op

    Nu0 = N_u(u, v)
    Nv0 = N_v(u, v)
    u_h = u + 0.5 * dt * Nu0
    v_hat = np.fft.fft(v)
    v_hat_h = (num_h * v_hat + 0.5 * dt * np.fft.fft(Nv0)) / denom_h
    v_h = ifft(v_hat_h)

    Nu1 = N_u(u_h, v_h)
    Nv1 = N_v(u_h, v_h)
    u_new = u + dt * Nu1
    v_hat_new = (num * v_hat + dt * np.fft.fft(Nv1)) / denom
    v_new = ifft(v_hat_new)
    return u_new, v_new

def diagnostics(u, v):
    v_x = dx_real(v)
    m   = u - 0.5 * v * v
    C1  = np.sum(u) * dx
    C2  = np.sum(v) * dx
    C3  = np.sum(u * v) * dx
    C4  = 0.5 * np.sum(u * u + v * v + v_x * v_x) * dx
    C5  = np.sum(m * m) * dx
    sup = max(np.max(np.abs(u)), np.max(np.abs(v)))
    finite = bool(np.all(np.isfinite(u)) and np.all(np.isfinite(v)))
    return dict(C1=C1, C2=C2, C3=C3, C4=C4, C5=C5, sup=sup, finite=finite)

# -----------------------------------------------------------
# IC: E2 — smooth periodic small-amplitude IC with nonzero means.
# -----------------------------------------------------------
np.random.seed(7)
v0 = 0.6 * np.cos(2*np.pi*x/L) + 0.3 * np.sin(4*np.pi*x/L) + 0.10
u0 = 0.4 * np.sin(2*np.pi*x/L) + 0.2 * np.cos(6*np.pi*x/L) + 0.15
u, v = u0.copy(), v0.copy()

# -----------------------------------------------------------
# Run
# -----------------------------------------------------------
T = 10.0
dt = 2.5e-4
nsteps = int(round(T / dt))
sample_every = max(1, nsteps // 200)

init = diagnostics(u, v)
print(f"[init] dx={dx:.4e} dt={dt:.4e} nsteps={nsteps} T={T}", flush=True)
print(f"[init] mean_u={np.mean(u0):.4e} mean_v={np.mean(v0):.4e}", flush=True)
print(f"[init] C1={init['C1']:.6e} C2={init['C2']:.6e} C3={init['C3']:.6e} C4={init['C4']:.6e} C5={init['C5']:.6e}", flush=True)

history = [(0.0, init['C1'], init['C2'], init['C3'], init['C4'], init['C5'], init['sup'], init['finite'])]

t0 = time.time()
blowup_t = None
for n in range(nsteps):
    u, v = step(u, v, dt)
    if (n + 1) % sample_every == 0 or n == nsteps - 1:
        d = diagnostics(u, v)
        t_curr = (n + 1) * dt
        history.append((t_curr, d['C1'], d['C2'], d['C3'], d['C4'], d['C5'], d['sup'], d['finite']))
        if (n + 1) % (sample_every * 10) == 0 or n == nsteps - 1:
            print(f"[t={t_curr:7.4f}] C1={d['C1']:+.4e} C2={d['C2']:+.4e} C3={d['C3']:+.4e} C4={d['C4']:+.4e} C5={d['C5']:+.4e} sup={d['sup']:.4e}", flush=True)
        if not d['finite'] or d['sup'] > 1e6:
            blowup_t = t_curr
            print(f"[BLOWUP] at t={t_curr:.4f}", flush=True)
            break

elapsed = time.time() - t0
final = diagnostics(u, v)
print(f"[final] t_final={(n+1)*dt:.4f} elapsed={elapsed:.2f}s finite={final['finite']}", flush=True)

hist = np.array(history, dtype=object)
times = np.array([h[0] for h in history], dtype=float)
Cs    = np.array([[h[1], h[2], h[3], h[4], h[5]] for h in history], dtype=float)
sups  = np.array([h[6] for h in history], dtype=float)

C0 = Cs[0]
names = ["C1=int u dx", "C2=int v dx", "C3=int uv dx", "C4=energy", "C5=int m^2 dx"]
for i, nm in enumerate(names):
    init_val = C0[i]
    final_val = Cs[-1, i]
    abs_drift = final_val - init_val
    scale = max(abs(init_val), 1e-12)
    rel_drift = abs_drift / scale
    abs_excursion = float(np.max(np.abs(Cs[:, i] - init_val)))
    print(f"[drift] {nm:18s} init={init_val:+.6e} final={final_val:+.6e} abs_drift={abs_drift:+.3e} rel_drift={rel_drift:+.3e} max_excursion={abs_excursion:.3e}", flush=True)

out_npz = os.path.join(os.path.dirname(__file__), "history.npz")
np.savez(out_npz, times=times, C1=Cs[:,0], C2=Cs[:,1], C3=Cs[:,2], C4=Cs[:,3], C5=Cs[:,4], sup=sups)
print(f"[save] history -> {out_npz}", flush=True)
print(f"[summary] blowup_t={blowup_t} reached_T={(blowup_t is None and (n+1)*dt >= T - 1e-9)}", flush=True)
