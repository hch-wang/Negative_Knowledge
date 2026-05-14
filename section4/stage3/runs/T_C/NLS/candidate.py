"""
T_C / NLS — Experiment E3 (final)
Single-component upgrade over E2: add 2/3-rule dealiasing.

Method (full validated S7 stack from kb-nls-muscl-madelung-bore-soliton):
  - Spatial:
      u: finite-volume cell averages, van-Leer-limited MUSCL reconstruction at
         each cell face, Godunov flux for Burgers f(u)=u^2/2, periodic.
      Psi = exp(i c x) * Psi_tilde, Psi_tilde periodic spectral grid (Nx=256, L=30,
         c=phi_x=0.6). Standard NLS sign (-(1/2) Psi_xx) per kb-nls-sign-convention.
  - Time:
      Outer Strang split per dt: [u-Burgers SSP-RK3 dt/2] - [Psi NLS-Strang dt] -
      [u-Burgers SSP-RK3 dt/2].
      NLS-Strang on Psi_tilde: N(dt/2) - L(dt) - N(dt/2).
  - 2/3 dealiasing on:
      (a) linear half-step output Psi_tilde (zero upper third of Fourier modes), and
      (b) |Psi_tilde|^2 before the cubic exponential.
  - dt = 5e-4.

Diagnostics: mass, ||m||_2, peak amplitude / position, |u| bounds, TV(u),
spectral tails on u and N.
"""
import numpy as np
import os, json, time

# ---------- domain & params ----------
L = 30.0
Nx = 256
dx = L / Nx
x = -L/2 + dx * (np.arange(Nx) + 0.5)
kappa = 1.0
T_final = 8.0
dt = 5.0e-4
n_steps = int(round(T_final / dt))
n_snapshots = 17
snap_every = n_steps // (n_snapshots - 1)

k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)

# 2/3 dealiasing mask: keep |k_index| <= Nx/3, zero out the middle high-frequency block
kx = np.arange(Nx)
# np.fft.fftfreq layout: 0..Nx/2 then -Nx/2..-1
# We keep only modes with |index| < Nx/3 in the symmetric sense.
# Compute via the absolute integer wavenumber:
kabs = np.minimum(kx, Nx - kx)
dealias_mask = (kabs < (Nx // 3)).astype(np.float64)
# = mask with the upper 1/3 of magnitudes zeroed.

c_boost = 0.6

# ---------- initial conditions ----------
u0 = 1.0 * (1.0 - np.tanh(x / 0.5)) / 2.0
N0 = 1.0 * (1.0 / np.cosh(x + 8.0))**2
phi_tilde0 = np.zeros_like(x)
Psi_tilde = np.sqrt(N0).astype(complex) * np.exp(1j * phi_tilde0)
u = u0.copy()

# ---------- MUSCL-Godunov on Burgers u ----------
def vanleer(a, b):
    out = np.zeros_like(a)
    s = a * b
    mask = s > 0
    denom = a + b
    out[mask] = 2.0 * a[mask] * b[mask] / denom[mask]
    return out

def burgers_godunov_flux(uL, uR):
    s = 0.5 * (uL + uR)
    out = np.where(uL <= uR,
                   np.where(uL > 0, 0.5*uL*uL,
                            np.where(uR < 0, 0.5*uR*uR, 0.0)),
                   np.where(s > 0, 0.5*uL*uL, 0.5*uR*uR))
    return out

def burgers_rhs(u_field):
    um1 = np.roll(u_field, 1)
    up1 = np.roll(u_field, -1)
    up2 = np.roll(u_field, -2)
    sigma = vanleer(u_field - um1, up1 - u_field)
    sigma_p1 = vanleer(up1 - u_field, up2 - up1)
    uL = u_field + 0.5 * sigma
    uR = up1 - 0.5 * sigma_p1
    F_iph = burgers_godunov_flux(uL, uR)
    F_imh = np.roll(F_iph, 1)
    return -(F_iph - F_imh) / dx

def step_u_SSPRK3(u_field, dt):
    k1 = burgers_rhs(u_field)
    u1 = u_field + dt * k1
    k2 = burgers_rhs(u1)
    u2 = 0.75 * u_field + 0.25 * (u1 + dt * k2)
    k3 = burgers_rhs(u2)
    u_new = (1.0/3.0) * u_field + (2.0/3.0) * (u2 + dt * k3)
    return u_new

# ---------- NLS Strang split-step on Psi_tilde with 2/3 dealias ----------
def linear_step_Psi_tilde(Psi_t, h):
    Pk = np.fft.fft(Psi_t)
    Pk *= np.exp(-1j * 0.5 * (k + c_boost)**2 * h)
    Pk *= dealias_mask                         # 2/3 dealias on linear step output
    return np.fft.ifft(Pk)

def nonlinear_step_Psi_tilde(Psi_t, h):
    rho = np.abs(Psi_t)**2
    # 2/3 dealias on the cubic source |Psi|^2 (zeros upper third before exponentiation)
    rho_k = np.fft.fft(rho) * dealias_mask
    rho_dealiased = np.real(np.fft.ifft(rho_k))
    return np.exp(1j * kappa * rho_dealiased * h) * Psi_t

def strang_step_Psi_tilde(Psi_t, h):
    Psi_t = nonlinear_step_Psi_tilde(Psi_t, 0.5 * h)
    Psi_t = linear_step_Psi_tilde(Psi_t, h)
    Psi_t = nonlinear_step_Psi_tilde(Psi_t, 0.5 * h)
    return Psi_t

def reconstruct_N_phi_x(Psi_t):
    N_field = np.abs(Psi_t)**2
    Psi_t_x = np.fft.ifft(1j * k * np.fft.fft(Psi_t))
    j_tilde = np.imag(np.conj(Psi_t) * Psi_t_x)
    eps_safe = 1e-30
    phi_x = c_boost + j_tilde / (N_field + eps_safe)
    return N_field, phi_x

# ---------- diagnostics ----------
snapshots, times = [], []
mass_t, mnorm_t, peak_amp, peak_pos, u_max, u_min, u_tv = [], [], [], [], [], [], []
energy_t = []

def record_snapshot(t_now, u_field, Psi_t):
    N_field, phi_x = reconstruct_N_phi_x(Psi_t)
    full_phase = c_boost * x + np.angle(Psi_t)
    snapshots.append(np.stack([u_field.copy(), N_field.copy(), full_phase.copy()], axis=0))
    times.append(t_now)
    mass_t.append(np.sum(N_field) * dx)
    m_field = u_field - N_field * phi_x
    mnorm_t.append(np.sqrt(np.sum(m_field**2) * dx))
    peak_amp.append(N_field.max())
    peak_pos.append(x[np.argmax(N_field)])
    u_max.append(u_field.max())
    u_min.append(u_field.min())
    u_tv.append(np.sum(np.abs(np.diff(u_field))) + np.abs(u_field[0] - u_field[-1]))
    # NLS energy on Psi_tilde:
    # E_NLS = 1/2 |Psi_x|^2 - kappa/2 |Psi|^4
    Psi_x = np.fft.ifft(1j * (k + c_boost) * np.fft.fft(Psi_t))
    E = 0.5 * np.sum(np.abs(Psi_x)**2) * dx - 0.5 * kappa * np.sum(np.abs(Psi_t)**4) * dx
    energy_t.append(E)

record_snapshot(0.0, u, Psi_tilde)

# ---------- main loop ----------
t0 = time.time()
blew_up = False
for step in range(1, n_steps + 1):
    u = step_u_SSPRK3(u, 0.5 * dt)
    Psi_tilde = strang_step_Psi_tilde(Psi_tilde, dt)
    u = step_u_SSPRK3(u, 0.5 * dt)

    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(Psi_tilde))):
        print(f"BLOW UP at step {step}, t={step*dt:.6f}")
        blew_up = True
        break

    if step % 100 == 0:
        umx = np.abs(u).max()
        rhomx = (np.abs(Psi_tilde)**2).max()
        if umx > 1e3 or rhomx > 1e3:
            print(f"DIVERGENCE at step {step}, t={step*dt:.6f}, |u|max={umx:.3e}, N_max={rhomx:.3e}")
            blew_up = True
            break

    if step % snap_every == 0 or step == n_steps:
        record_snapshot(step * dt, u, Psi_tilde)

wall = time.time() - t0
print(f"wall = {wall:.1f}s, n_snapshots = {len(snapshots)}, blew_up = {blew_up}")
print("times:", [f"{t:.2f}" for t in times])
print("mass:", [f"{m:.6f}" for m in mass_t])
print("||m||_2:", [f"{mm:.4f}" for mm in mnorm_t])
print("peak_amp:", [f"{p:.3f}" for p in peak_amp])
print("peak_pos:", [f"{p:.2f}" for p in peak_pos])
print("u_min..u_max:", [f"{a:.3f}..{b:.3f}" for a,b in zip(u_min, u_max)])
print("u_TV:", [f"{tv:.3f}" for tv in u_tv])
print("E_NLS:", [f"{e:.4f}" for e in energy_t])

# spectral tail (last snapshot)
N_last = snapshots[-1][1, :]
u_last = snapshots[-1][0, :]
uk = np.fft.fft(u_last)
Nk = np.fft.fft(N_last)
hi_ratio_u = np.sum(np.abs(uk[Nx//3:2*Nx//3])**2) / max(np.sum(np.abs(uk)**2), 1e-30)
hi_ratio_N = np.sum(np.abs(Nk[Nx//3:2*Nx//3])**2) / max(np.sum(np.abs(Nk)**2), 1e-30)
print(f"u high-1/3 energy ratio: {hi_ratio_u:.2e}")
print(f"N high-1/3 energy ratio: {hi_ratio_N:.2e}")

arr = np.stack(snapshots, axis=0).astype(np.float64)
print("output shape:", arr.shape)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", arr)
print("saved pred_results/T_C.npy")

diag = {
    "method": "E3: MUSCL-Godunov SSP-RK3 on u + Madelung-Psi Strang + 2/3 dealias (full S7 stack)",
    "Nx": Nx, "L": L, "dt": dt, "T": T_final, "kappa": kappa, "phi_x_boost": c_boost,
    "n_snapshots": len(snapshots), "blew_up": blew_up,
    "wall_seconds": wall,
    "times": times, "mass": mass_t, "mnorm": mnorm_t, "energy_NLS": energy_t,
    "peak_amp": peak_amp, "peak_pos": peak_pos,
    "u_min": u_min, "u_max": u_max, "u_TV": u_tv,
    "u_high1_3_ratio_T": hi_ratio_u,
    "N_high1_3_ratio_T": hi_ratio_N,
}
with open("E3_diag.json", "w") as f:
    json.dump(diag, f, indent=2)
print("saved E3_diag.json")
