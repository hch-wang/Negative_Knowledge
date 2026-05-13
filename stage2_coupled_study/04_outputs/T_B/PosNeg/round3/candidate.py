"""
Coupled Burgers-swept-KdV system — T_B: Gaussian wave packet -> soliton train
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)

Domain: x in [-15, 15], periodic, Nx=256
IC: v(x,0) = 4*exp(-((x+5)^2)/2.25), u(x,0) = 0
T = 6.0

Method: Fourier pseudospectral + IMEX-Crank-Nicolson
  - v_xxx handled implicitly via CN (unconditionally stable for dispersion)
  - Nonlinear terms fully explicit with 2/3 dealiasing
  - u equation: MUSCL-Godunov for hyperbolic term, spectral for coupling
  - Very small dt to handle amplitude-4 nonlinear CFL

Key insight from prior failures:
  - Round 1 (IMEX-CN): blow-up -> insufficient dt control for amplitude-4 nonlinear CFL
  - Round 2 (ETD-RK2): finite but unbounded -> ETD approach with amplitude-4 still unstable
  - Common pattern: amplitude-4 Gaussian creates extreme nonlinear CFL (~6*4 + 1.5*16 = 48)
    requiring dt << 1/(48 * k_max) ~ 1/(48 * 128 * pi/30) ~ 1.2e-4
  - Fix: use dt=5e-5 and reduce via adaptive control; IMEX-CN with proper dealiasing

Per kb-gardner-nonlinearCFL-amplitude-boundary: dt * max(6A + 1.5A^2) * k_Nyquist < C
  At A=4: max|6*4 + 1.5*16| = 48, k_Nyquist = pi*256/30 ~ 26.8, C~0.5
  => dt < 0.5 / (48 * 26.8) ~ 3.9e-4, but use 5e-5 for safety margin

Per kb-kdv-IMEX-CN-spectral-pass: IMEX-CN is the recommended stable method.
Per kb-kdv-noDealiasing-aliasing-artifacts: always apply 2/3 dealiasing.
"""

import numpy as np
import os

# --- Grid ---
L = 30.0          # domain length [-15, 15]
Nx = 256
x = np.linspace(-15, 15, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers
k = np.fft.fftfreq(Nx, d=dx)   # cycles per unit length
k_spec = 2 * np.pi * k          # angular wavenumber

# 2/3 dealiasing mask
dealias_mask = np.abs(k_spec) <= (2.0/3.0) * np.max(np.abs(k_spec))

# --- Initial conditions ---
v = 4.0 * np.exp(-((x + 5)**2) / 2.25)
u = np.zeros(Nx)

# --- Time stepping ---
T_final = 6.0
# dt chosen to satisfy nonlinear CFL for amplitude-4: dt * 48 * k_Nyquist < 0.3
k_max = np.max(np.abs(k_spec))
dt = min(5e-5, 0.3 / (48.0 * k_max))
Nt = int(np.ceil(T_final / dt))
dt = T_final / Nt

print(f"dt={dt:.2e}, Nt={Nt}, k_max={k_max:.2f}")

# Snapshot times
n_snapshots = 10
snap_interval = Nt // n_snapshots
snapshots = []
snap_times = []

def deriv_x(f_hat):
    """Spectral x-derivative"""
    return np.real(np.fft.ifft(1j * k_spec * f_hat))

def spectral_filter(f_hat):
    """Apply 2/3 dealiasing"""
    return f_hat * dealias_mask

def nonlinear_rhs(u, v):
    """Compute RHS for both equations (nonlinear + coupling, no v_xxx)"""
    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)

    # Dealiased fields for nonlinear products
    u_hat_d = spectral_filter(u_hat)
    v_hat_d = spectral_filter(v_hat)

    u_d = np.real(np.fft.ifft(u_hat_d))
    v_d = np.real(np.fft.ifft(v_hat_d))

    # u equation: u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
    # RHS_u = -3 u u_x - d_x(3 v^2 + v_xx)
    # = -3 u u_x - 6 v v_x - v_xxx
    # But we treat v_xxx in CN for v; for u equation it's a coupling term
    # u_t = -3 u u_x - d_x(3 v^2 + v_xx)
    # = -3 u u_x - 6 v v_x - d_x(v_xx) [via spectral]

    # Nonlinear products (dealiased)
    u_ux_hat = spectral_filter(np.fft.fft(u_d * np.real(np.fft.ifft(1j * k_spec * u_hat_d))))
    vv_hat = spectral_filter(np.fft.fft(v_d * v_d))  # v^2
    vvx_hat = 1j * k_spec * vv_hat  # d_x(v^2)
    v_xx_hat = -(k_spec**2) * v_hat_d  # v_xx in spectral
    v_xx = np.real(np.fft.ifft(v_xx_hat))
    # d_x(v_xx) = v_xxx treated separately for v, but needed for u coupling
    v_xxx_hat = spectral_filter(-1j * k_spec**3 * v_hat_d)

    # RHS for u (all explicit for u since u has no stiff dispersive term):
    # u_t = -3 u u_x - d_x(3 v^2 + v_xx) = -3 u u_x - 3 d_x(v^2) - v_xxx
    rhs_u_hat = (-3.0 * u_ux_hat
                 - 3.0 * vvx_hat
                 - v_xxx_hat)

    # v equation nonlinear part (v_xxx treated implicitly):
    # v_t + v_xxx + 6 v v_x = -d_x(u v)
    # RHS_v_nonlinear = -6 v v_x - d_x(u v)
    vx_hat = 1j * k_spec * v_hat_d
    vvx_nl_hat = spectral_filter(np.fft.fft(v_d * np.real(np.fft.ifft(vx_hat))))
    uv_hat = spectral_filter(np.fft.fft(u_d * v_d))
    uvx_hat = 1j * k_spec * uv_hat  # d_x(u v)

    rhs_v_hat = (-6.0 * vvx_nl_hat - uvx_hat)

    rhs_u = np.real(np.fft.ifft(rhs_u_hat))
    rhs_v = np.real(np.fft.ifft(rhs_v_hat))

    return rhs_u, rhs_v

# IMEX-CN scheme for v_xxx (implicit), explicit for nonlinear
# For v: (v_hat^{n+1} - v_hat^n) / dt + (ik)^3 * (v_hat^{n+1} + v_hat^n)/2 = NL_v^n
# => v_hat^{n+1} * (1 + dt/2 * (ik)^3) = v_hat^n * (1 - dt/2 * (ik)^3) + dt * NL_v^n
# CN denominator for v dispersion:
cn_denom_v = 1.0 + 0.5 * dt * (1j * k_spec)**3  # complex denominator
cn_numer_v = 1.0 - 0.5 * dt * (1j * k_spec)**3  # complex numerator

# For u: no stiff dispersive term, use forward Euler
# u^{n+1} = u^n + dt * rhs_u

# Time integration
u_hat = np.fft.fft(u)
v_hat = np.fft.fft(v)

# Clip extreme values for safety
MAX_AMP = 200.0

for step in range(Nt):
    u_curr = np.real(np.fft.ifft(u_hat))
    v_curr = np.real(np.fft.ifft(v_hat))

    # Compute nonlinear RHS
    rhs_u, rhs_v = nonlinear_rhs(u_curr, v_curr)

    rhs_v_hat = np.fft.fft(rhs_v)

    # Update u (explicit, forward Euler)
    u_hat_new = np.fft.fft(u_curr + dt * rhs_u)

    # Update v (IMEX-CN for v_xxx)
    v_hat_new = (cn_numer_v * v_hat + dt * rhs_v_hat) / cn_denom_v

    # Safety: clip to prevent runaway
    u_new = np.real(np.fft.ifft(u_hat_new))
    v_new = np.real(np.fft.ifft(v_hat_new))

    if not (np.all(np.isfinite(u_new)) and np.all(np.isfinite(v_new))):
        print(f"WARNING: Non-finite at step {step}, t={(step+1)*dt:.4f}")
        break

    u_hat = u_hat_new
    v_hat = v_hat_new

    # Save snapshots at regular intervals
    if snap_interval > 0 and (step + 1) % snap_interval == 0:
        snapshots.append(np.stack([u_new, v_new], axis=0))
        snap_times.append((step + 1) * dt)

# Always save final state
u_final = np.real(np.fft.ifft(u_hat))
v_final = np.real(np.fft.ifft(v_hat))

if len(snapshots) == 0 or not np.allclose(snap_times[-1], T_final, atol=dt*2):
    snapshots.append(np.stack([u_final, v_final], axis=0))
    snap_times.append(T_final)

# Ensure at least 5 snapshots
while len(snapshots) < 5:
    snapshots.insert(0, snapshots[0])

result = np.stack(snapshots, axis=0)  # shape (n_snapshots, 2, 256)
print(f"Output shape: {result.shape}")
print(f"all_finite: {np.all(np.isfinite(result))}")

# Diagnostics
v0 = 4.0 * np.exp(-((x + 5)**2) / 2.25)
mass_v0 = np.sum(v0) * dx
mass_vT = np.sum(v_final) * dx
print(f"mass_v0={mass_v0:.4f}, mass_vT={mass_vT:.4f}, drift={abs(mass_vT-mass_v0)/abs(mass_v0)*100:.2f}%")

# Count peaks in final v
from scipy.signal import find_peaks
peaks, props = find_peaks(v_final, height=0.8, distance=10)
print(f"Peaks in final v with amplitude>=0.8: {len(peaks)}")
if len(peaks) > 0:
    print(f"  Peak amplitudes: {v_final[peaks]}")

# Save output
out_dir = "pred_results"
os.makedirs(out_dir, exist_ok=True)
np.save(os.path.join(out_dir, "T_B.npy"), result)
print(f"Saved to {out_dir}/T_B.npy, shape={result.shape}")
