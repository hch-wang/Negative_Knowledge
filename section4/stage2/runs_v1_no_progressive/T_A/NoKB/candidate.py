"""
Experiment E3: Coupled Burgers-swept-KdV soliton stability
Method: Fourier pseudospectral + scipy RK45 adaptive + small hyperviscosity

PDE:
  u_t = -3 u u_x - 6 v v_x - v_xxx - eps*k^4*u  (hyperviscosity for u)
  v_t = -6 v v_x - v_xxx - (uv)_x - eps*k^4*v    (hyperviscosity for v)

The hyperviscosity term -eps*k^4 in spectral space damps high-k modes.
With eps=1e-4 and k_max~27, dissipation rate at k_max = eps*k_max^4 ~ 0.02,
which is small relative to the KdV dynamics but prevents aliasing instability.

scipy.integrate.solve_ivp with RK45 handles the v_xxx stiffness via adaptive dt.
"""
import numpy as np
from scipy.integrate import solve_ivp
import os

# --- Grid setup ---
Nx = 256
xL, xR = -15.0, 15.0
L = xR - xL
x = np.linspace(xL, xR, Nx, endpoint=False)
dx = L / Nx

# Fourier wavenumbers
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi
k_int = np.fft.fftfreq(Nx, d=1.0/Nx)  # integer wavenumbers
ik = 1j * k
ik3 = (1j * k)**3

# 2/3 dealiasing mask
dealias = (np.abs(k_int) <= Nx // 3).astype(float)

# Hyperviscosity parameter (small enough not to affect soliton dynamics)
# At k_max_eff~18 rad/m: dissipation rate = eps*k^4 ~ eps*18^4 ~ 1e-5 * 105000 = 1.05
# Use eps=1e-7: rate ~ 0.011 at k_max, negligible for soliton
eps_hv = 1e-7
hv = -eps_hv * k**4  # linear dissipation in spectral space (always negative/zero)

def rhs_flat(t, y):
    """
    RHS for scipy.integrate.solve_ivp.
    y = [U_hat_real, U_hat_imag, V_hat_real, V_hat_imag] flattened as real array
    """
    # Unpack
    U_hat = y[:Nx] + 1j * y[Nx:2*Nx]
    V_hat = y[2*Nx:3*Nx] + 1j * y[3*Nx:4*Nx]

    # Apply dealiasing
    U_hat_d = U_hat * dealias
    V_hat_d = V_hat * dealias

    # Physical space values
    u = np.real(np.fft.ifft(U_hat_d))
    v = np.real(np.fft.ifft(V_hat_d))

    # Spatial derivatives
    u_x = np.real(np.fft.ifft(ik * U_hat_d))
    v_x = np.real(np.fft.ifft(ik * V_hat_d))
    v_xxx = np.real(np.fft.ifft(ik3 * V_hat_d))

    # PDE 1: u_t = -3 u u_x - 6 v v_x - v_xxx + hv*U_hat
    dudt_phys = -3.0 * u * u_x - 6.0 * v * v_x - v_xxx
    dU_hat = np.fft.fft(dudt_phys) * dealias + hv * U_hat

    # PDE 2: v_t = -6 v v_x - v_xxx - (uv)_x + hv*V_hat
    uv_x = np.real(np.fft.ifft(ik * np.fft.fft(u * v) * dealias))
    dvdt_phys = -6.0 * v * v_x - v_xxx - uv_x
    dV_hat = np.fft.fft(dvdt_phys) * dealias + hv * V_hat

    # Pack back to real array
    dy = np.concatenate([
        np.real(dU_hat), np.imag(dU_hat),
        np.real(dV_hat), np.imag(dV_hat)
    ])
    return dy


# --- Initial conditions ---
v0 = 2.0 / np.cosh(x + 5.0)**2
u0 = 0.5 * v0**2 + 0.2 * v0

U_hat0 = np.fft.fft(u0)
V_hat0 = np.fft.fft(v0)

y0 = np.concatenate([
    np.real(U_hat0), np.imag(U_hat0),
    np.real(V_hat0), np.imag(V_hat0)
])

# Snapshot times
T_final = 8.0
n_snapshots = 9
t_eval = np.linspace(0, T_final, n_snapshots)

print("Starting integration with scipy RK45...")
print(f"T_final={T_final}, n_snapshots={n_snapshots}")

sol = solve_ivp(
    rhs_flat,
    [0, T_final],
    y0,
    method='RK45',
    t_eval=t_eval,
    rtol=1e-6,
    atol=1e-8,
    max_step=0.05,   # limit max step to ensure we don't overshoot
    dense_output=False
)

print(f"Solver status: {sol.status}, message: {sol.message}")
print(f"Number of function evaluations: {sol.nfev}")
print(f"t_eval achieved: {sol.t}")

# Reconstruct snapshots
snapshots = []
for i in range(len(sol.t)):
    y = sol.y[:, i]
    U_hat = y[:Nx] + 1j * y[Nx:2*Nx]
    V_hat = y[2*Nx:3*Nx] + 1j * y[3*Nx:4*Nx]
    u_snap = np.real(np.fft.ifft(U_hat))
    v_snap = np.real(np.fft.ifft(V_hat))
    snapshots.append(np.array([u_snap, v_snap]))

snapshots = np.array(snapshots)
print(f"Snapshots shape: {snapshots.shape}")

# Diagnostics
if len(snapshots) >= 2:
    v_init = snapshots[0, 1]
    v_final = snapshots[-1, 1]
    u_final = snapshots[-1, 0]

    v_init_peak = np.max(v_init)
    v_final_peak = np.max(v_final)
    v_init_mass = np.sum(v_init) * dx
    v_final_mass = np.sum(v_final) * dx
    mass_drift_pct = abs(v_final_mass - v_init_mass) / (abs(v_init_mass) + 1e-12) * 100

    print(f"\nDiagnostics at T={sol.t[-1]:.3f}:")
    print(f"  Initial v peak: {v_init_peak:.4f}")
    print(f"  Final v peak:   {v_final_peak:.4f}")
    print(f"  Amplitude retention: {v_final_peak/v_init_peak:.4f} ({v_final_peak/v_init_peak*100:.1f}%)")
    print(f"  Initial v mass: {v_init_mass:.4f}")
    print(f"  Final v mass:   {v_final_mass:.4f}")
    print(f"  Mass drift: {mass_drift_pct:.2f}%")
    print(f"  Max |u| final: {np.max(np.abs(u_final)):.4f}")
    print(f"  Max |v| final: {np.max(np.abs(v_final)):.4f}")

    # Check all snapshots
    print("\nTime-series diagnostics:")
    for i, ti in enumerate(sol.t):
        v_s = snapshots[i, 1]
        u_s = snapshots[i, 0]
        print(f"  t={ti:.2f}: v_peak={np.max(v_s):.4f}, max|u|={np.max(np.abs(u_s)):.4f}, max|v|={np.max(np.abs(v_s)):.4f}")

    # NaN check
    has_nan = not np.isfinite(snapshots).all()
    print(f"\nHas NaN/Inf: {has_nan}")
    print(f"Phenomenon check:")
    print(f"  v_final_peak >= 1.0 (50% of 2.0): {v_final_peak >= 1.0}")
    print(f"  mass_drift < 8%: {mass_drift_pct < 8.0}")
    print(f"  max|u| < 15: {np.max(np.abs(u_final)) < 15.0}")
    print(f"  max|v| < 15: {np.max(np.abs(v_final)) < 15.0}")

# Save output
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "T_A.npy")
np.save(out_path, snapshots)
print(f"\nSaved to {out_path}")
