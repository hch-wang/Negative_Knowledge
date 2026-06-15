"""
BKdV-S7 Round 3 (E3): mechanism — predict which modes of m amplify first,
using the BKdV-S5 algebraic identity:

    m_t|_{m=0} = (v - 1) * (6 v v_x + v_xxx)

evaluated on our IC v_0(x) = 1.5 sech^2(x + 5).

Plan:
1. Compute the spatial structure of m_t at t = 0 from the algebraic identity
   above, using the same Fourier pseudospectral derivative stack.
2. Compute its L2 norm and spectral content |m_t_hat(k)|.
3. Load the actual BKdV m(x, t) trajectory from round2/snapshots.npz,
   compute |m_hat(k, t)| at several early times, and check which modes
   are predicted vs observed.
4. Independent linearized prediction:  d/dt |m_hat(k, t)| at t = 0 is exactly
   |m_t_hat(k, 0)|.  We can integrate this linear prediction to get
   m_predicted(k, t) ≈ t * m_t_hat(k, 0) for small t, then compare to actual
   m(x, t) computed from the BKdV snapshot file.
5. We also probe amplitude sensitivity: recompute the source for A = 1.0 and
   A = 0.5 and verify the source scales (roughly) like A^3 (cubic in v for
   small v) or A * (v_xxx)-piece (linear in v for the dispersive piece).

Outputs:
- round3/source_diag.npz  (x, m_t_source, spectral coefs, A-sweep numbers)
- round3/exec.log
"""

import os
import sys
import time
import numpy as np

ROUND_DIR = os.path.dirname(os.path.abspath(__file__))
ROUND2_DIR = os.path.join(os.path.dirname(ROUND_DIR), "round2")
ROUND1_DIR = os.path.join(os.path.dirname(ROUND_DIR), "round1")

# ------------------------------------------------------------
# Grid & spectral operators (identical to E1/E2)
# ------------------------------------------------------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
ik = 1j * k
k2 = k ** 2
ik3 = 1j * k ** 3

k_max = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)


def fft_dealias(a):
    return np.fft.fft(a) * dealias


def dx_spec(f):
    return np.real(np.fft.ifft(ik * fft_dealias(f)))


def dxxx_spec(f):
    return np.real(np.fft.ifft(-ik3 * fft_dealias(f)))


# ------------------------------------------------------------
# 1. Algebraic source for m_t|_{m=0} at t=0
# ------------------------------------------------------------
A = 1.5
v0 = A * (1.0 / np.cosh(x + 5.0)) ** 2

v_x = dx_spec(v0)
v_xxx = dxxx_spec(v0)

# inner bracket: 6 v v_x + v_xxx
inner = 6.0 * v0 * v_x + v_xxx

# full source: m_t source = (v - 1) * inner
source = (v0 - 1.0) * inner

source_L2 = float(np.sqrt(np.sum(source ** 2) * dx))
source_Linf = float(np.max(np.abs(source)))
integ = float(np.sum(source) * dx)
integ_abs = float(np.sum(np.abs(source)) * dx)

print(f"[source] m_t|_(m=0)(t=0) at A={A}", flush=True)
print(f"  ||m_t_source||_L2 = {source_L2:.4e}", flush=True)
print(f"  ||m_t_source||_Linf = {source_Linf:.4e}", flush=True)
print(f"  integrated source (signed) = {integ:.4e}", flush=True)
print(f"  integrated |source|        = {integ_abs:.4e}", flush=True)

# Note: source is concentrated where v_0 is large (x ≈ -5).
# Find the spatial support: top 5% mask
mask = np.abs(source) > 0.05 * source_Linf
support_xs = x[mask]
if len(support_xs) > 0:
    print(f"  spatial support (5% threshold): x in [{support_xs.min():+.2f}, {support_xs.max():+.2f}]",
          flush=True)

# Spectral content of the source
src_hat = np.fft.fft(source)
src_amp = np.abs(src_hat)
# Top modes by |hat|. Use only positive k (k>0 half) for reporting.
pos = np.where(k > 0)[0]
order = pos[np.argsort(-src_amp[pos])][:10]
print(f"\n[source spectral content] top 10 positive-k modes (k_index, k, |hat|)",
      flush=True)
for idx in order:
    kval = float(k[idx])
    amp = float(src_amp[idx])
    # convert k_index back to integer mode number n: k = 2 pi n / L
    n_mode = int(round(kval * L / (2 * np.pi)))
    print(f"  n={n_mode:3d}  k={kval:+.3f}  |src_hat|={amp:.3e}", flush=True)

# Predicted L2 growth rate of m at t=0: d/dt ||m||_L2|_(t=0)^+ = ||m_t||_L2
# (since m(0) = 0, ||m+dt m_t||_L2 = dt * ||m_t||_L2 for small dt)
predicted_growth_per_unit_t = source_L2
print(f"\n[prediction] d/dt ||m||_L2|_(t->0+) = ||source||_L2 = {source_L2:.4e}",
      flush=True)
print(f"  Hence m_norm(t=0.1) ≈ {0.1*source_L2:.4e},  m_norm(t=0.5) ≈ {0.5*source_L2:.4e}  (linear extrapolation)",
      flush=True)

# Decompose the source: |(v-1)| * |6 v v_x|  vs  |(v-1)| * |v_xxx|
src_quad = (v0 - 1.0) * (6.0 * v0 * v_x)
src_disp = (v0 - 1.0) * v_xxx
quad_L2 = float(np.sqrt(np.sum(src_quad ** 2) * dx))
disp_L2 = float(np.sqrt(np.sum(src_disp ** 2) * dx))
print(f"\n[source decomposition]", flush=True)
print(f"  ||(v-1) * 6 v v_x||_L2  (quadratic-flux piece) = {quad_L2:.4e}", flush=True)
print(f"  ||(v-1) * v_xxx||_L2    (dispersive piece)     = {disp_L2:.4e}", flush=True)
print(f"  ratio quad/disp = {quad_L2/disp_L2:+.4f}", flush=True)

# ------------------------------------------------------------
# 2. Verify by loading actual BKdV snapshots and checking the early
# m-trajectory + spectral signature.
# ------------------------------------------------------------
snap = np.load(os.path.join(ROUND2_DIR, "snapshots.npz"))
t_arr = snap["times"]
v_traj = snap["v"]
u_traj = snap["u"]
print(f"\n[load] round2 snapshots: {len(t_arr)} times, t in [{t_arr[0]:.3f}, {t_arr[-1]:.3f}]",
      flush=True)

# Linear prediction:  m_pred(x, t) = t * source(x)  (valid only for very small t)
# Compare predicted ||m||_L2 to observed at the earliest snapshots
print(f"\n[early-time m_norm verification]", flush=True)
print(f"  t       observed ||m||_L2   linear-extrap t*||source||_L2", flush=True)
for ti in range(min(5, len(t_arr))):
    t = float(t_arr[ti])
    m_obs = u_traj[ti] - 0.5 * v_traj[ti] ** 2
    m_obs_L2 = float(np.sqrt(np.sum(m_obs ** 2) * dx))
    m_pred = t * source_L2
    print(f"  {t:5.3f}   {m_obs_L2:.4e}        {m_pred:.4e}    "
          f"(ratio obs/pred = {m_obs_L2/(m_pred+1e-30):.3f})", flush=True)

# ------------------------------------------------------------
# 3. Spectral verification — which modes carry the observed m at t = 0.5?
# Compare |m_hat(k, t=0.5)| / t  vs.  |source_hat(k)|.
# (For small t and m(0)=0, |m_hat(k,t)| ≈ t * |source_hat(k)| + O(t^2).)
# ------------------------------------------------------------
t_check = float(t_arr[1])  # t = 0.5
m05 = u_traj[1] - 0.5 * v_traj[1] ** 2
m05_hat = np.fft.fft(m05)
m05_amp = np.abs(m05_hat)
m05_per_t = m05_amp / t_check  # rate per unit time

print(f"\n[spectral verification at t = {t_check}]", flush=True)
print(f"  top 10 positive-k modes in observed |m_hat|/t  vs  |source_hat|:",
      flush=True)
order_obs = pos[np.argsort(-m05_amp[pos])][:10]
for idx in order_obs:
    kval = float(k[idx])
    n_mode = int(round(kval * L / (2 * np.pi)))
    print(f"  n={n_mode:3d}  k={kval:+.3f}  |m_hat|(t=0.5)/0.5={m05_per_t[idx]:.3e}  "
          f"|source_hat|={src_amp[idx]:.3e}  ratio={m05_per_t[idx]/(src_amp[idx]+1e-30):+.3f}",
          flush=True)

# Overall spectral correlation between |m_hat|(t=0.5)/0.5 and |source_hat|
ix = pos  # positive-k modes
num = np.sum(m05_per_t[ix] * src_amp[ix])
den = np.sqrt(np.sum(m05_per_t[ix] ** 2) * np.sum(src_amp[ix] ** 2))
corr = float(num / (den + 1e-30))
print(f"\n[spectral correlation] cos-sim(|m_hat|(t=0.5)/t, |source_hat|) = {corr:.4f}",
      flush=True)

# ------------------------------------------------------------
# 4. Amplitude sweep — how does ||source||_L2 scale with A?
# Source = (A sech^2 - 1) * [ 6 A sech^2 (A sech^2)_x + (A sech^2)_xxx ]
#       =  6 A^3 sech^4 (sech^2)_x - 6 A^2 sech^2 (sech^2)_x
#         + A^2 sech^2 (sech^2)_xxx - A (sech^2)_xxx   (after grouping)
# So the source has 4 polynomial pieces in A. Compute numerically.
# ------------------------------------------------------------
print(f"\n[A-sweep] ||source||_L2 vs A", flush=True)
A_list = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
src_norms = []
for A_test in A_list:
    v_test = A_test * (1.0 / np.cosh(x + 5.0)) ** 2
    v_x_t = dx_spec(v_test)
    v_xxx_t = dxxx_spec(v_test)
    inner_t = 6.0 * v_test * v_x_t + v_xxx_t
    src_t = (v_test - 1.0) * inner_t
    norm_t = float(np.sqrt(np.sum(src_t ** 2) * dx))
    src_norms.append(norm_t)
    # decompose:  (v-1) * (6 v v_x):  cubic-A part of leading term
    # at v=1 (A sech^2 = 1) the source vanishes pointwise; that's the (v-1) cancellation
    print(f"  A={A_test:.2f}  ||source||_L2 = {norm_t:.4e}", flush=True)

# Estimate scaling: ||source||(A) for A in [0.5, 1.5] — fit log-log
A_arr = np.array(A_list)
s_arr = np.array(src_norms)
# only use A in [0.5, 1.5] to avoid v->1 cancellation at A near 1/peak
mask_fit = (A_arr >= 0.25) & (A_arr <= 0.75)
if np.sum(mask_fit) >= 2:
    p = np.polyfit(np.log(A_arr[mask_fit]), np.log(s_arr[mask_fit]), 1)
    print(f"  loglog slope on A in [0.25, 0.75]: {p[0]:.3f}   "
          f"(expected ~3 if cubic dominates, ~1 if linear-dispersive dominates)",
          flush=True)
mask_fit2 = (A_arr >= 1.0) & (A_arr <= 2.5)
if np.sum(mask_fit2) >= 2:
    p2 = np.polyfit(np.log(A_arr[mask_fit2]), np.log(s_arr[mask_fit2]), 1)
    print(f"  loglog slope on A in [1.0, 2.5]: {p2[0]:.3f}",
          flush=True)

# ------------------------------------------------------------
# 5. Save everything
# ------------------------------------------------------------
np.savez(os.path.join(ROUND_DIR, "source_diag.npz"),
         x=x, v0=v0, source=source,
         src_quad=src_quad, src_disp=src_disp,
         src_hat=src_hat, m05_hat=m05_hat,
         A_list=np.array(A_list), src_norms=np.array(src_norms),
         source_L2=source_L2, predicted_growth=predicted_growth_per_unit_t,
         spectral_corr_t05=corr)

print(f"\n[saved] {os.path.join(ROUND_DIR, 'source_diag.npz')}", flush=True)
print("[done] E3 mechanism complete.", flush=True)
