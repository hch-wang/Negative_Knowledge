"""
T_B: Gaussian wave packet -> soliton train decomposition
Coupled Burgers-swept-KdV system:
  u_t + 3 u u_x = -d_x(3v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

Method (E3 - final revision):
In spectral space linear parts: d/dt u_hat = ik^3*v_hat + NL_u
                                 d/dt v_hat = ik^3*v_hat + NL_v

Change of variables: w_hat = u_hat - v_hat
  d/dt v_hat = ik^3*v_hat + NL_v  (stiff, use exact exp propagation)
  d/dt w_hat = NL_u - NL_v        (no stiff term, use RK4)

Strang splitting: exp(ik^3 dt/2) for v, RK4 for nonlinear, exp(ik^3 dt/2) for v.

ADDED: exponential spectral filter applied after each step to prevent aliasing
blow-up during high-amplitude soliton collisions on the periodic domain.
Filter: sigma(k) = exp(-alpha*(|k|/k_max)^p) with alpha=50, p=8 (damps k > ~0.9*k_max)
This is equivalent to a mild Gaussian/Butterworth spectral filter.

dt=2e-5, 2/3 dealiasing for nonlinear products, Strang+RK4+filter.
"""

import numpy as np
import os
from scipy.signal import find_peaks

# Parameters
L = 30.0
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx
T = 6.0
dt = 2e-5
n_steps = int(round(T / dt))
n_snapshots = 61

k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi
k_idx = np.fft.fftfreq(Nx) * Nx
dealias_mask = np.abs(k_idx) <= Nx // 3

def dealias(fh):
    out = fh.copy()
    out[~dealias_mask] = 0.0
    return out

def ifft_r(fh):
    return np.real(np.fft.ifft(fh))

def fft_r(f):
    return np.fft.fft(np.real(f))

# Spectral filter for stability
k_max = np.max(np.abs(k))
alpha_filt = 50.0
p_filt = 8
spec_filter = np.exp(-alpha_filt * (np.abs(k) / k_max)**p_filt)

def apply_filter(fh):
    return spec_filter * fh

# Linear operator for v: lv = ik^3
lv = 1j * k**3
# Strang half-step exact propagator
E_half = np.exp(lv * dt / 2.0)  # Note: lv is purely imaginary, so |E_half|=1, safe

def NL_v_fn(u_hat, v_hat):
    """NL_v = -6vv_x - (uv)_x, dealiased"""
    v = ifft_r(v_hat)
    u = ifft_r(u_hat)
    v_x = ifft_r(1j * k * v_hat)
    t1 = dealias(fft_r(-6.0 * v * v_x))
    uv_hat = dealias(fft_r(u * v))
    t2 = -1j * k * uv_hat
    return t1 + t2

def NL_u_fn(u_hat, v_hat):
    """NL_u = -3uu_x - (3v^2)_x = -3uu_x - 6vv_x, dealiased"""
    u = ifft_r(u_hat)
    v = ifft_r(v_hat)
    u_x = ifft_r(1j * k * u_hat)
    v_x = ifft_r(1j * k * v_hat)
    t1 = dealias(fft_r(-3.0 * u * u_x))
    t2 = dealias(fft_r(-6.0 * v * v_x))
    return t1 + t2

def NL_w_fn(w_hat, v_hat):
    """d/dt w_hat = NL_u - NL_v"""
    u_hat = w_hat + v_hat
    return NL_u_fn(u_hat, v_hat) - NL_v_fn(u_hat, v_hat)

def step_one(w_hat, v_hat):
    """One step: Strang splitting (linear half) + RK4 (nonlinear) + (linear half) + filter"""
    # Linear half-step for v
    v1 = E_half * v_hat

    # RK4 for nonlinear part (both w and v_nonlinear)
    def F(wh, vh):
        u_hat = wh + vh
        nlv = NL_v_fn(u_hat, vh)
        nlu = NL_u_fn(u_hat, vh)
        return nlu - nlv, nlv  # (d/dt w, d/dt v_nonlinear)

    k1w, k1v = F(w_hat, v1)

    w2 = w_hat + (dt/2)*k1w
    v2 = v1 + (dt/2)*k1v
    k2w, k2v = F(w2, v2)

    w3 = w_hat + (dt/2)*k2w
    v3 = v1 + (dt/2)*k2v
    k3w, k3v = F(w3, v3)

    w4 = w_hat + dt*k3w
    v4 = v1 + dt*k3v
    k4w, k4v = F(w4, v4)

    w_new = w_hat + (dt/6)*(k1w + 2*k2w + 2*k3w + k4w)
    v_mid = v1 + (dt/6)*(k1v + 2*k2v + 2*k3v + k4v)

    # Linear half-step for v
    v_new = E_half * v_mid

    # Apply spectral filter to both
    w_new = apply_filter(w_new)
    v_new = apply_filter(v_new)

    return w_new, v_new

# Initial condition
v0 = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
u0 = np.zeros(Nx)
v_hat = fft_r(v0)
u_hat = fft_r(u0)
w_hat = u_hat - v_hat

save_times = np.linspace(0, T, n_snapshots)
save_steps_set = set(np.round(save_times / dt).astype(int))
save_steps_set.add(0)
save_steps_set.add(n_steps)

results = []
t = 0.0
results.append((t, ifft_r(u_hat).copy(), ifft_r(v_hat).copy()))

nl_cfl = dt * 48 * k_max
print(f"Nx={Nx}, dt={dt}, n_steps={n_steps}, T={T}")
print(f"NL-CFL(A=4): {nl_cfl:.4f}")
print(f"Filter: alpha={alpha_filt}, p={p_filt}")
print(f"Starting Strang+RK4+filter integration...")

report_interval = max(1, n_steps // 20)

for step in range(n_steps):
    w_hat, v_hat = step_one(w_hat, v_hat)
    t += dt

    if step % report_interval == 0:
        u_hat_c = w_hat + v_hat
        vm = np.max(np.abs(ifft_r(v_hat)))
        um = np.max(np.abs(ifft_r(u_hat_c)))
        if not (np.isfinite(vm) and np.isfinite(um)):
            print(f"NaN at step={step}, t={t:.4f}")
            break
        print(f"step={step}/{n_steps}, t={t:.3f}, v_max={vm:.4f}, u_max={um:.4f}")

    if step + 1 in save_steps_set:
        u_hat_c = w_hat + v_hat
        results.append((t, ifft_r(u_hat_c).copy(), ifft_r(v_hat).copy()))

print(f"\nDone. {len(results)} snapshots.")

n_out = len(results)
out = np.zeros((n_out, 2, Nx))
for i, (ti, ui, vi) in enumerate(results):
    out[i, 0, :] = ui
    out[i, 1, :] = vi

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", out)
print(f"Saved pred_results/T_B.npy, shape={out.shape}")

v_final = out[-1, 1, :]
u_final = out[-1, 0, :]
print(f"\n=== Final diagnostics ===")
print(f"all_finite: {np.all(np.isfinite(out))}")
print(f"v_max={np.max(v_final):.4f}, v_min={np.min(v_final):.4f}")
print(f"u_max={np.max(u_final):.4f}")
peaks_v, _ = find_peaks(v_final, height=0.8, distance=5)
print(f"v peaks >= 0.8: {len(peaks_v)}")
if len(peaks_v):
    print(f"  x: {x[peaks_v]}")
    print(f"  amp: {v_final[peaks_v]}")
dx_val = L / Nx
m_i = np.sum(out[0, 1, :]) * dx_val
m_f = np.sum(v_final) * dx_val
drift = abs(m_f - m_i) / abs(m_i) * 100
print(f"Mass drift: {drift:.3f}%")
print(f"n_snapshots: {n_out}")
