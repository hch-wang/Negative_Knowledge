"""
T_B: Gaussian wave packet -> soliton train decomposition
Coupled Burgers-swept-KdV system (Holm et al. 2025):
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

Round-2 method: Integrating Factor RK4 (IFRK4) with strong dealiasing and
a much smaller time step to prevent overflow blow-up from round 1.

Round-1 blew up due to IMEX-CN at dt=0.0005 being insufficiently stable for
the strongly coupled nonlinear terms when v has amplitude 4.  We switch to
IFRK4 which exactly integrates the linear dispersive stiffness via the
integrating factor exp(ik^3 * t), and use dt=0.0001 for the nonlinear stage.
The 2/3 dealiasing removes aliasing energy that drove round-1 to blow up.
"""

import numpy as np
import os

# Domain
L = 30.0
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = x[1] - x[0]

# Wavenumbers
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi

# Initial conditions
v = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u = np.zeros(Nx)

# Time stepping — much smaller dt than round 1 to tame nonlinear coupling
T_final = 6.0
dt = 0.0001
Nt = int(round(T_final / dt))
dt = T_final / Nt

# Dealiasing mask (2/3 rule)
k_max_abs = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * k_max_abs).astype(float)

# Precompute ik^3 for the dispersive term of v
ik3 = (1j * k) ** 3  # = -i k^3

# Snapshot setup: 7 evenly spaced including t=0 and t=T
n_snapshots = 7
snap_times = np.linspace(0, T_final, n_snapshots)
snap_steps = set(int(round(t / dt)) for t in snap_times)
snap_steps.add(Nt)

snapshots = []


def rhs_uv(u_hat, v_hat):
    """
    Returns (du_hat/dt, dv_hat/dt) from the nonlinear + coupling terms only.
    The linear dispersive part ik^3 * v_hat is handled by the integrating factor.

    u_t = -3 d_x(u^2/2) - d_x(3v^2 + v_xx)
    v_t + v_xxx = -6 d_x(v^2/2) - d_x(u v)

    In IF frame: du_hat/dt and dv_hat_IF/dt where v_hat_IF = exp(-ik^3 t) v_hat.
    Here we just compute the pure nonlinear RHS (the factor is applied outside).
    """
    # Apply dealiasing
    u_hat_d = u_hat * dealias
    v_hat_d = v_hat * dealias

    u_r = np.fft.ifft(u_hat_d).real
    v_r = np.fft.ifft(v_hat_d).real

    # v_xx for the forcing on u
    vxx_hat = (1j * k) ** 2 * v_hat_d
    vxx_r = np.fft.ifft(vxx_hat).real

    # RHS for u: -d_x(3 u^2/2 * 2 ... let's be precise)
    # u_t + 3 u u_x = -d_x(3v^2 + v_xx)
    # u_t = -3 u u_x - d_x(3v^2 + v_xx)
    # = -3/2 d_x(u^2) - d_x(3v^2 + v_xx)   [since 3 u u_x = 3/2 d_x(u^2)]
    uu_hat = np.fft.fft(u_r ** 2) * dealias
    v2_hat = np.fft.fft(v_r ** 2) * dealias
    expr_u_hat = np.fft.fft(3.0 * v_r ** 2 + vxx_r) * dealias

    rhs_u_hat = -1j * k * (1.5 * uu_hat + expr_u_hat)

    # RHS for v (nonlinear part only, dispersive -ik^3 v handled by IF):
    # v_t = -6 v v_x - d_x(u v) = -3 d_x(v^2) - d_x(u v)
    uv_hat = np.fft.fft(u_r * v_r) * dealias
    rhs_v_hat = -1j * k * (3.0 * v2_hat + uv_hat)

    return rhs_u_hat, rhs_v_hat


# Integrating Factor RK4
# For v: let w_hat = exp(-ik^3 * t) * v_hat
# dw_hat/dt = exp(-ik^3*t) * rhs_v_hat(u_hat, v_hat)
# At each sub-step we must convert w_hat back: v_hat = exp(ik^3*t) * w_hat

u_hat = np.fft.fft(u)
v_hat = np.fft.fft(v)

t = 0.0
# Initial w_hat (at t=0, factor=1)
w_hat = v_hat.copy()  # exp(-ik^3 * 0) * v_hat = v_hat

for step in range(Nt):
    if step in snap_steps:
        u_r = np.fft.ifft(u_hat).real
        v_r = np.fft.ifft(np.exp(1j * ik3 * t) * w_hat).real
        snapshots.append(np.stack([u_r, v_r], axis=0))

    # Current v_hat from integrating factor
    ef = np.exp(1j * ik3 * t)
    v_hat = ef * w_hat

    # k1
    k1u, k1v = rhs_uv(u_hat, v_hat)
    # For w: k1w = exp(-ik^3*t) * k1v
    k1w = np.exp(-1j * ik3 * t) * k1v

    # k2 at t + dt/2
    t2 = t + 0.5 * dt
    ef2 = np.exp(1j * ik3 * t2)
    w2 = w_hat + 0.5 * dt * k1w
    v2 = ef2 * w2
    u2 = u_hat + 0.5 * dt * k1u
    k2u, k2v = rhs_uv(u2, v2)
    k2w = np.exp(-1j * ik3 * t2) * k2v

    # k3 at t + dt/2
    w3 = w_hat + 0.5 * dt * k2w
    v3 = ef2 * w3
    u3 = u_hat + 0.5 * dt * k2u
    k3u, k3v = rhs_uv(u3, v3)
    k3w = np.exp(-1j * ik3 * t2) * k3v

    # k4 at t + dt
    t4 = t + dt
    ef4 = np.exp(1j * ik3 * t4)
    w4 = w_hat + dt * k3w
    v4 = ef4 * w4
    u4 = u_hat + dt * k3u
    k4u, k4v = rhs_uv(u4, v4)
    k4w = np.exp(-1j * ik3 * t4) * k4v

    # Update
    w_hat = w_hat + (dt / 6.0) * (k1w + 2.0 * k2w + 2.0 * k3w + k4w)
    u_hat = u_hat + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    t = t + dt

# Final snapshot
u_r = np.fft.ifft(u_hat).real
v_r = np.fft.ifft(np.exp(1j * ik3 * t) * w_hat).real
snapshots.append(np.stack([u_r, v_r], axis=0))

# Ensure we have at least 5 and at most n_snapshots+1
if len(snapshots) > 8:
    # subsample to keep manageable
    idx = np.round(np.linspace(0, len(snapshots) - 1, 8)).astype(int)
    snapshots = [snapshots[i] for i in idx]

result = np.array(snapshots)  # shape (n_snap, 2, 256)

# Save
out_dir = os.path.join(
    "${PROJECT_ROOT}/stage2/runs/T_B/PosOnly/round2",
    "pred_results"
)
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "T_B.npy"), result)

print(f"Saved shape: {result.shape}")
print(f"v final: min={result[-1, 1].min():.4f}, max={result[-1, 1].max():.4f}")
print(f"all finite: {np.all(np.isfinite(result))}")
