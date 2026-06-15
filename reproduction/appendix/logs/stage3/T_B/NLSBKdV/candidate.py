"""
T_B: Gaussian density packet on M_cs — focusing B-NLS modulational instability.

E2 method (current): same Madelung-Psi Strang split-step on Psi as E1, but with
single grid-refinement upgrade Nx=256 -> Nx=512 and dt 1e-3 -> 5e-4 (the
CFL-tied dt change), per kb-nls-resolution-soliton-counting and
kb-nls-strang-splitstep-bright-soliton recommendations for A>=2 Gaussian.
After integration on the Nx=512 grid we downsample to 256 for the output
shape required by the task spec.

Sign convention: STANDARD NLS sign (i Psi_t = -1/2 Psi_xx - kappa |Psi|^2 Psi)
adopted per kb-nls-sign-convention's hypothesis-transfer warning.

Bank ids consulted:
  NLS: kb-nls-recommended-default-bnls, kb-nls-strang-splitstep-bright-soliton,
       kb-nls-resolution-soliton-counting, kb-nls-cfl-split-step,
       kb-nls-madelung-psi-handles-zero-density, kb-nls-split-linear-phase,
       kb-nls-23-dealiasing-cubic, kb-nls-direct-n-phi-structural-failure.
"""

import os
import numpy as np

# ---------- output target ----------
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "pred_results")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, "T_B.npy")

# ---------- problem parameters ----------
kappa = 1.0
Lx = 30.0
Nx_int = 512               # internal grid (refined)
Nx_out = 256               # output grid (task spec)
dx_int = Lx / Nx_int
x_int = -Lx / 2.0 + dx_int * np.arange(Nx_int)
x_out = -Lx / 2.0 + (Lx / Nx_out) * np.arange(Nx_out)
downsample_step = Nx_int // Nx_out                              # = 2

# wavenumbers for internal grid
k = 2.0 * np.pi * np.fft.fftfreq(Nx_int, d=dx_int)
k2 = k * k

# 2/3 dealias mask
kmax = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * kmax).astype(np.float64)

# ---------- initial condition ----------
sigma = 1.5
A0 = 2.0
N0 = A0 * np.exp(-(x_int + 5.0) ** 2 / (2.0 * sigma ** 2))
c_phase = 0.3
phi_tilde0 = np.zeros_like(x_int)
eps_mad = 1.0e-12
U = np.sqrt(N0 + eps_mad) * np.exp(1j * phi_tilde0)

# linear full-step propagator with Galilean boost
def make_lin_full(dt):
    return np.exp(-0.5j * dt * (k + c_phase) ** 2)


# ---------- time integration ----------
T = 6.0
dt = 5.0e-4
nsteps = int(round(T / dt))
n_snapshots = 25
snap_every = max(1, nsteps // (n_snapshots - 1))

snaps_u = []
snaps_N = []
snaps_phi = []
snap_times = []


def reconstruct(U_arr, t):
    """Reconstruct (u, N, phi) on the OUTPUT (Nx_out) grid by downsampling.

    Psi(x,t) = exp(i*c*x) * U(x,t)
    N = |U|^2
    phi_total = c*x + arg(U)
    u = c*|U|^2 + Im(conj(U) U_x)
    """
    Uk = np.fft.fft(U_arr)
    Ux = np.fft.ifft(1j * k * Uk)
    N_lab = (np.abs(U_arr) ** 2).real
    j = (c_phase * N_lab + np.imag(np.conj(U_arr) * Ux)).real
    u_lab = j
    phi_lab = c_phase * x_int + np.angle(U_arr)
    # downsample
    u_out = u_lab[::downsample_step].astype(np.float32)
    N_out = N_lab[::downsample_step].astype(np.float32)
    phi_out = phi_lab[::downsample_step].astype(np.float32)
    return u_out, N_out, phi_out


def save_snapshot(U_arr, t):
    u_out, N_out, phi_out = reconstruct(U_arr, t)
    snaps_u.append(u_out)
    snaps_N.append(N_out)
    snaps_phi.append(phi_out)
    snap_times.append(t)


save_snapshot(U, 0.0)

lin_full = make_lin_full(dt)

mass0 = np.sum(np.abs(U) ** 2) * dx_int
max_abs_U = 0.0

print(f"E2 setup: Nx_int={Nx_int}, Nx_out={Nx_out}, dt={dt}, nsteps={nsteps}, T={T}")
print(f"  initial mass = {mass0:.6e}")
print(f"  c_phase={c_phase}, eps_mad={eps_mad}")
print(f"  snap_every={snap_every} steps")
print(f"  linear-step phase budget pi^2 Nx^2 dt / (2 L^2) = {np.pi**2 * Nx_int**2 * dt / (2 * Lx**2):.3f}")

for step in range(1, nsteps + 1):
    # NL half-step
    rho = np.abs(U) ** 2
    rho_k = np.fft.fft(rho)
    rho_k *= dealias
    rho = np.fft.ifft(rho_k).real
    U = U * np.exp(0.5j * dt * kappa * rho)

    # Linear full step
    Uk = np.fft.fft(U)
    Uk = lin_full * Uk
    Uk *= dealias
    U = np.fft.ifft(Uk)

    # NL half-step
    rho = np.abs(U) ** 2
    rho_k = np.fft.fft(rho)
    rho_k *= dealias
    rho = np.fft.ifft(rho_k).real
    U = U * np.exp(0.5j * dt * kappa * rho)

    if not np.all(np.isfinite(U)):
        print(f"BLOWUP at step={step}, t={step*dt}")
        break
    max_abs_U = max(max_abs_U, float(np.max(np.abs(U))))

    if (step % snap_every == 0) or step == nsteps:
        save_snapshot(U, step * dt)

print(f"\nFinal stats: {len(snap_times)} snapshots; t_last={snap_times[-1]:.4f}")
mass_final = np.sum(np.abs(U) ** 2) * dx_int
print(f"  mass0 = {mass0:.6e}, mass_final = {mass_final:.6e}, drift = {(mass_final-mass0)/mass0:.3e}")
print(f"  max|U|_t = {max_abs_U:.4f}, |U|_max_final = {float(np.max(np.abs(U))):.4f}")

# Output array
out = np.stack(
    [np.stack([snaps_u[i], snaps_N[i], snaps_phi[i]], axis=0) for i in range(len(snap_times))],
    axis=0,
)
print(f"  output shape = {out.shape}")

# Final-snap diagnostics on the Nx_out grid
N_final = snaps_N[-1].astype(np.float64)
phi_final = snaps_phi[-1].astype(np.float64)
u_final = snaps_u[-1].astype(np.float64)
k_out = 2.0 * np.pi * np.fft.fftfreq(Nx_out, d=Lx / Nx_out)
phi_k_out = np.fft.fft(phi_final)
phi_x_final = np.fft.ifft(1j * k_out * phi_k_out).real
m_final = u_final - N_final * phi_x_final
print(f"  ||m||_inf on final snap (output grid) = {np.max(np.abs(m_final)):.3e}")
print(f"  ||m||_2   on final snap (output grid) = {np.sqrt(np.sum(m_final**2)*(Lx/Nx_out)):.3e}")

maxima_idx = []
for i in range(Nx_out):
    im = (i - 1) % Nx_out
    ip = (i + 1) % Nx_out
    if N_final[i] > N_final[im] and N_final[i] > N_final[ip]:
        maxima_idx.append(i)
peaks_sig = [(x_out[i], float(N_final[i])) for i in maxima_idx if N_final[i] >= 1.0]
print(f"  local maxima count (any height): {len(maxima_idx)}")
print(f"  peaks with N>=1.0: {len(peaks_sig)}")
for p in peaks_sig:
    print(f"     x={p[0]:.3f}  N={p[1]:.4f}")

# Spectral tail on internal grid
Uk_int = np.fft.fft(U)
total = np.sum(np.abs(Uk_int) ** 2)
tail_int = float(np.sum(np.abs(Uk_int[int(0.9*Nx_int):int(0.95*Nx_int)])**2) / total)
upper_third_int = float(np.sum(np.abs(Uk_int[int(2/3*Nx_int):])**2) / total)
print(f"  spectral tail (90-95% of Nx_int={Nx_int}) = {tail_int:.3e}")
print(f"  upper-third energy (Nx_int) = {upper_third_int:.3e}")

np.save(OUT_PATH, out.astype(np.float32))
print(f"\nSaved to {OUT_PATH}")
