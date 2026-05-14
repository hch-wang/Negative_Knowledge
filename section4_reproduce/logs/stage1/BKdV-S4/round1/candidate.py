"""
BKdV-S4 / Round 1 / E1 — Baseline numerical-resolution probe

Research question (program-level): How sensitive is BKdV long-time behavior to
(dt, Nx, hyperviscosity ν_h)? Is there a regime where doubling resolution flips
the qualitative answer?

Round 1: lay down a BASELINE at the PROMPT-SPECIFIED parameters, with the
PRE-VALIDATED Fourier pseudospectral + 2/3-dealias + RK4 stack. No method
iteration. Record a full diagnostic time series so later rounds can be
compared against this baseline (5% shift threshold for "robust").

Params: dt=5e-4, Nx=256, ν_h=1e-22.
IC: v0 = 1.5 sech^2(x+5), u0 = v0^2/2 (so m0 = u0 - v0^2/2 ≡ 0 — Gardner-manifold IC).
Domain: x ∈ [-15,15], periodic. T_final = 10.

Diagnostics:
  - ||m||_L2(t), ||m||_inf(t)          (Gardner-manifold deviation)
  - ||u||_L2(t), ||v||_L2(t)           (energy proxy)
  - mass_u, mass_v                     (1st conservation laws)
  - lock_corr(u, v^2/2)                (compound-state alignment)
  - low/high spectral partition (k<2 vs k>=2) for u and for v
  - snapshots of u(x), v(x) at 11 times
"""

import numpy as np
import os, json, time, sys

# -----------------------------------------------------------------------------
# Resolution parameters (THIS IS WHAT THE PROGRAM PROBES)
# -----------------------------------------------------------------------------
DT       = 5.0e-4
NX       = 256
HYPER    = 1.0e-22       # ν_h baseline
T_FINAL  = 10.0

TAG = "E1_baseline"
OUTDIR = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------------------------------------
# Spatial grid
# -----------------------------------------------------------------------------
L  = 30.0
x  = np.linspace(-15.0, 15.0, NX, endpoint=False)
dx = x[1] - x[0]
k  = 2.0 * np.pi * np.fft.fftfreq(NX, d=L / NX)
kmax = np.max(np.abs(k))
ik   = 1j * k
ik3  = 1j * (k ** 3)
kcut = (2.0 / 3.0) * kmax
dealias = (np.abs(k) < kcut).astype(np.float64)

# Hyperviscosity operator: -ν_h * k^16  on u-hat (8th-order hyperviscous)
HYPER_P = 8
hyper_op = -HYPER * (k ** (2 * HYPER_P))

def fft(a):  return np.fft.fft(a)
def ifft(A): return np.real(np.fft.ifft(A))
def nl_hat(a, b): return dealias * fft(a * b)

# -----------------------------------------------------------------------------
# RHS for the integrating-factor form on v
#   v_hat = exp(i k^3 t) * w_hat,  so v_xxx term is absorbed into the IF.
#   u-equation: u_t + 3 u u_x = -∂_x(3 v^2 + v_xx)  (plus hyperviscous tail)
#   v-equation: v_t + 6 v v_x + v_xxx = -∂_x(u v)  → w_t = e^{-ik^3 t} * [v RHS w/o v_xxx]
# -----------------------------------------------------------------------------
def rhs(u_hat, w_hat, t):
    phase = np.exp(ik3 * t)
    v_hat = phase * w_hat
    u = ifft(u_hat); v = ifft(v_hat)
    u2_h = nl_hat(u, u)
    v2_h = nl_hat(v, v)
    uv_h = nl_hat(u, v)
    v_xx_h = (ik ** 2) * v_hat
    u_hat_t = -ik * (1.5 * u2_h + 3.0 * v2_h + v_xx_h) + hyper_op * u_hat
    v_hat_t_nl = -ik * (3.0 * v2_h + uv_h)
    w_hat_t = np.exp(-ik3 * t) * v_hat_t_nl
    return u_hat_t, w_hat_t

def rk4_step(u_hat, w_hat, t, dt):
    k1a, k1b = rhs(u_hat, w_hat, t)
    k2a, k2b = rhs(u_hat + 0.5 * dt * k1a, w_hat + 0.5 * dt * k1b, t + 0.5 * dt)
    k3a, k3b = rhs(u_hat + 0.5 * dt * k2a, w_hat + 0.5 * dt * k2b, t + 0.5 * dt)
    k4a, k4b = rhs(u_hat + dt * k3a,       w_hat + dt * k3b,       t + dt)
    return (u_hat + dt / 6.0 * (k1a + 2.0 * k2a + 2.0 * k3a + k4a),
            w_hat + dt / 6.0 * (k1b + 2.0 * k2b + 2.0 * k3b + k4b))

# -----------------------------------------------------------------------------
# Diagnostics
# -----------------------------------------------------------------------------
def m_field(u, v): return u - 0.5 * v * v

def spectrum_partition(field, k_split=2.0):
    F = np.fft.fft(field) / NX
    P = np.abs(F) ** 2
    mask_low = np.abs(k) <= k_split
    return float(np.sum(P[mask_low])), float(np.sum(P[~mask_low]))

def lock_corr(u, v):
    a = u - np.mean(u); b = 0.5 * v * v - np.mean(0.5 * v * v)
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    return float('nan') if (na < 1e-12 or nb < 1e-12) else float(np.dot(a, b) / (na * nb))

def cons_estim(u, v):
    return (float(np.sum(u) * dx),
            float(np.sum(v) * dx),
            float(np.sqrt(np.sum(u * u) * dx)),
            float(np.sqrt(np.sum(v * v) * dx)))

def energy_estim(u, v):
    # An admissible "energy-like" quadratic functional often tracked in BKdV:
    #   E = ∫ ( 1/2 u^2 + 1/2 v^2 + 1/2 v_x^2 ) dx
    v_hat = np.fft.fft(v)
    v_x = np.real(np.fft.ifft(ik * v_hat))
    return float(0.5 * np.sum(u * u) * dx
                 + 0.5 * np.sum(v * v) * dx
                 + 0.5 * np.sum(v_x * v_x) * dx)

# -----------------------------------------------------------------------------
# IC
# -----------------------------------------------------------------------------
v0 = 1.5 / np.cosh(x + 5.0) ** 2
u0 = 0.5 * v0 * v0          # Gardner-manifold: m0 = u0 - v0^2/2 = 0

print(f"== BKdV-S4 / E1 baseline ==")
print(f"   NX={NX}, dt={DT}, ν_h={HYPER:.1e}, T={T_FINAL}")
print(f"   IC: v0 = 1.5 sech^2(x+5), u0 = v0^2/2")
print(f"   ||m0||_L2 = {np.sqrt(np.sum(m_field(u0, v0)**2) * dx):.3e}  (should be ~0)")
print(f"   v-mass    = {np.sum(v0)*dx:.4f}")
print(f"   u-mass    = {np.sum(u0)*dx:.4f}")

# -----------------------------------------------------------------------------
# Integration
# -----------------------------------------------------------------------------
u_hat = fft(u0); v_hat = fft(v0); w_hat = v_hat.copy()
nsteps = int(round(T_FINAL / DT))
n_diag = 101                # 100 intervals → record every T/100 = 0.1
diag_stride = max(1, nsteps // (n_diag - 1))
n_snap = 11
snap_stride = max(1, nsteps // (n_snap - 1))

times = [0.0]
m_l2  = [float(np.sqrt(np.sum(m_field(u0, v0) ** 2) * dx))]
m_inf = [float(np.max(np.abs(m_field(u0, v0))))]
el_u, eh_u, el_v, eh_v = [], [], [], []
elu, ehu = spectrum_partition(u0); el_u.append(elu); eh_u.append(ehu)
elv, ehv = spectrum_partition(v0); el_v.append(elv); eh_v.append(ehv)
locks  = [lock_corr(u0, v0)]
masses = [cons_estim(u0, v0)]
energies = [energy_estim(u0, v0)]
snaps  = [np.stack([u0.copy(), v0.copy()], axis=0)]
snap_times = [0.0]

t  = 0.0
t0 = time.time()
blew_up = False
for step in range(1, nsteps + 1):
    u_hat, w_hat = rk4_step(u_hat, w_hat, t, DT)
    t += DT
    if not np.all(np.isfinite(u_hat)) or not np.all(np.isfinite(w_hat)):
        print(f"NaN at step {step}, t={t:.4f}")
        blew_up = True; break
    if step % diag_stride == 0:
        v_hat_now = np.exp(ik3 * t) * w_hat
        u_now = ifft(u_hat); v_now = ifft(v_hat_now)
        m_now = m_field(u_now, v_now)
        times.append(t)
        m_l2.append(float(np.sqrt(np.sum(m_now ** 2) * dx)))
        m_inf.append(float(np.max(np.abs(m_now))))
        elu, ehu = spectrum_partition(u_now); el_u.append(elu); eh_u.append(ehu)
        elv, ehv = spectrum_partition(v_now); el_v.append(elv); eh_v.append(ehv)
        locks.append(lock_corr(u_now, v_now))
        masses.append(cons_estim(u_now, v_now))
        energies.append(energy_estim(u_now, v_now))
    if step % snap_stride == 0 and len(snaps) < n_snap:
        v_hat_now = np.exp(ik3 * t) * w_hat
        u_now = ifft(u_hat); v_now = ifft(v_hat_now)
        snaps.append(np.stack([u_now.copy(), v_now.copy()], axis=0))
        snap_times.append(t)
while len(snaps) < n_snap:
    snaps.append(snaps[-1].copy()); snap_times.append(snap_times[-1])

wall = time.time() - t0
print(f"\nIntegration: nsteps={nsteps}, wall={wall:.1f}s, blew_up={blew_up}")

# -----------------------------------------------------------------------------
# Save
# -----------------------------------------------------------------------------
out_npz = os.path.join(OUTDIR, "E1_baseline.npz")
np.savez(out_npz,
         times=np.array(times), m_l2=np.array(m_l2), m_inf=np.array(m_inf),
         el_u=np.array(el_u), eh_u=np.array(eh_u),
         el_v=np.array(el_v), eh_v=np.array(eh_v),
         lock=np.array(locks), masses=np.array(masses),
         energies=np.array(energies),
         snaps=np.array(snaps), snap_times=np.array(snap_times),
         x=x, k=k,
         dt=DT, Nx=NX, hyper=HYPER, T_final=T_FINAL)
print(f"saved {out_npz}")

# JSON summary (human + curator)
mfin = masses[-1]
summary = {
    "tag": TAG,
    "params": {"dt": DT, "Nx": NX, "hyper": HYPER, "T_final": T_FINAL},
    "blew_up": blew_up, "wall_seconds": wall,
    "t_end": float(times[-1]),
    "m_l2":     {"t0": float(m_l2[0]),    "t_end": float(m_l2[-1])},
    "m_inf":    {"t0": float(m_inf[0]),   "t_end": float(m_inf[-1])},
    "lock":     {"t0": float(locks[0]),   "t_end": float(locks[-1])},
    "L2_u":     {"t0": float(masses[0][2]), "t_end": float(mfin[2])},
    "L2_v":     {"t0": float(masses[0][3]), "t_end": float(mfin[3])},
    "mass_u":   {"t0": float(masses[0][0]), "t_end": float(mfin[0])},
    "mass_v":   {"t0": float(masses[0][1]), "t_end": float(mfin[1])},
    "energy":   {"t0": float(energies[0]),  "t_end": float(energies[-1])},
    "el_u_tend": float(el_u[-1]), "eh_u_tend": float(eh_u[-1]),
    "el_v_tend": float(el_v[-1]), "eh_v_tend": float(eh_v[-1]),
    "u_peak_tend": float(np.max(np.abs(snaps[-1][0]))),
    "v_peak_tend": float(np.max(np.abs(snaps[-1][1]))),
}
print("\nE1 summary:")
print(json.dumps(summary, indent=2))
with open(os.path.join(OUTDIR, "E1_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print(f"saved {os.path.join(OUTDIR, 'E1_summary.json')}")
