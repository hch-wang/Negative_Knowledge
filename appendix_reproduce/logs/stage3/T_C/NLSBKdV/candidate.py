"""
T_C / NLSBKdV — E3 (final method)
Single component upgrade over E2: add 2/3 dealiasing on |Psi|^2 (before pointwise
nonlinear exponential) and on the linear FFT step.

Final method = MUSCL-Godunov SSP-RK3 on u + Strang Madelung-Psi on Psi + 2/3 dealias.
This matches kb-nls-muscl-madelung-bore-soliton's full stacked recipe.

Sign convention: STANDARD NLS -(1/2)*Psi_xx (HYPOTHESIS per kb-nls-sign-convention).
The user's literal +Q sign in the phi equation does not admit a stable explicit
Madelung-Psi propagator; we adopt the standard sign as the working hypothesis per
the bank entry's recommended_action (iii).
"""
import numpy as np
import os, time

# ---------- Grid ----------
L  = 30.0
xL, xR = -15.0, 15.0
Nx = 256
dx = L / Nx
x  = xL + dx*np.arange(Nx)
k  = 2.0*np.pi*np.fft.fftfreq(Nx, d=dx)

kappa = 1.0
c_phi = 0.6

# 2/3 dealias mask
k_cut = Nx//3
dealias = np.ones(Nx)
# zero out top 1/3 of |k| modes
abs_k = np.abs(k)
dealias[abs_k > (2.0/3.0) * np.max(abs_k)] = 0.0

# ---------- IC ----------
u0   = 1.0 * (1.0 - np.tanh(x/0.5))/2.0
N0   = 1.0 * (1.0/np.cosh(x + 8.0))**2
Psi0_tilde = np.sqrt(N0).astype(np.complex128)

# ---------- Time ----------
T_final = 8.0
dt      = 5.0e-4
n_steps = int(round(T_final/dt))
dt      = T_final/n_steps

n_snapshots = 9
snap_times  = np.linspace(0.0, T_final, n_snapshots)
snap_steps  = set(int(round(t/dt)) for t in snap_times)

k_shift = k + c_phi
lin_phase_full = np.exp(-1j * 0.5 * k_shift**2 * dt)

# ---------- MUSCL-Godunov SSP-RK3 on u (Burgers, f=u^2/2) ----------
def van_leer(a, b):
    out = np.zeros_like(a)
    same = (a*b > 0.0)
    out[same] = 2.0*a[same]*b[same] / (a[same] + b[same] + 1e-300)
    return out

def godunov_burgers_flux(uL, uR):
    fL = 0.5*uL*uL
    fR = 0.5*uR*uR
    flux = np.where(uL > uR,
                    np.where(0.5*(uL+uR) >= 0.0, fL, fR),
                    np.where(uL >= 0.0, fL,
                             np.where(uR <= 0.0, fR, 0.0)))
    return flux

def burgers_rhs_muscl(u):
    um = np.roll(u, +1)
    up = np.roll(u, -1)
    a = u - um
    b = up - u
    slope = van_leer(a, b)
    uL_face = u + 0.5*slope
    uR_face = np.roll(u - 0.5*slope, -1)
    F = godunov_burgers_flux(uL_face, uR_face)
    F_im = np.roll(F, +1)
    return -(F - F_im)/dx

def step_u_muscl_ssprk3(u, dt_u):
    k1 = burgers_rhs_muscl(u)
    u1 = u + dt_u*k1
    k2 = burgers_rhs_muscl(u1)
    u2 = 0.75*u + 0.25*(u1 + dt_u*k2)
    k3 = burgers_rhs_muscl(u2)
    return (1.0/3.0)*u + (2.0/3.0)*(u2 + dt_u*k3)

# ---------- Strang Madelung-Psi with 2/3 dealiasing ----------
def strang_step(Psi_tilde):
    # half-step nonlinear with dealiased |Psi|^2
    rho = (np.abs(Psi_tilde))**2
    rho_hat = np.fft.fft(rho)
    rho_hat *= dealias
    rho_d = np.real(np.fft.ifft(rho_hat))
    Psi_tilde = Psi_tilde * np.exp(1j * kappa * rho_d * (dt/2))
    # linear full-step with dealiasing
    Psi_hat = np.fft.fft(Psi_tilde)
    Psi_hat *= lin_phase_full * dealias
    Psi_tilde = np.fft.ifft(Psi_hat)
    # half-step nonlinear
    rho = (np.abs(Psi_tilde))**2
    rho_hat = np.fft.fft(rho)
    rho_hat *= dealias
    rho_d = np.real(np.fft.ifft(rho_hat))
    Psi_tilde = Psi_tilde * np.exp(1j * kappa * rho_d * (dt/2))
    return Psi_tilde

# ---------- Diagnostics ----------
def reconstruct_full(Psi_tilde_now):
    Psi = np.exp(1j*c_phi*x) * Psi_tilde_now
    N   = (np.abs(Psi))**2
    phi = np.angle(Psi)
    return N, phi

def m_norm(u_now, N_now, phi_now):
    Psi = np.sqrt(np.maximum(N_now, 0.0)) * np.exp(1j*phi_now)
    Psi_x = np.fft.ifft(1j*k*np.fft.fft(Psi))
    eps = 1e-30
    phi_x_est = np.imag(Psi_x / (Psi + eps))
    m_vec = u_now - N_now*phi_x_est
    return float(np.sqrt(np.sum(m_vec*m_vec)*dx))

snapshots = []
diag = []
def save_snap(t_now, u_now, Psi_tilde_now):
    N_now, phi_now = reconstruct_full(Psi_tilde_now)
    snapshots.append(np.stack([u_now.copy(), N_now.copy(), phi_now.copy()], axis=0))
    mass = float(np.sum(N_now)*dx)
    mnrm = m_norm(u_now, N_now, phi_now)
    Nmax = float(np.max(N_now))
    umax = float(np.max(np.abs(u_now)))
    tv_u = float(np.sum(np.abs(np.diff(u_now))))
    diag.append(dict(t=t_now, mass=mass, m_norm=mnrm, Nmax=Nmax, umax=umax, tv_u=tv_u))

# ---------- Main loop ----------
Psi_tilde = Psi0_tilde.copy()
u = u0.copy()
save_snap(0.0, u, Psi_tilde)

t0 = time.time()
diverged = False
for step in range(1, n_steps+1):
    Psi_tilde = strang_step(Psi_tilde)
    u = step_u_muscl_ssprk3(u, dt)
    t = step*dt

    if (step % 200) == 0 or step in snap_steps:
        u_lo = float(np.max(np.abs(u)))
        N_lo = float(np.max((np.abs(Psi_tilde))**2))
        if (not np.isfinite(u_lo)) or (not np.isfinite(N_lo)) or u_lo>50 or N_lo>1e4:
            print(f"DIVERGE at step={step} t={t:.4f} umax={u_lo:.3e} Nmax={N_lo:.3e}")
            diverged = True
            break

    if step in snap_steps:
        save_snap(t, u, Psi_tilde)
        d = diag[-1]
        print(f"snap t={d['t']:.3f}: mass={d['mass']:.4e} ||m||={d['m_norm']:.3e} Nmax={d['Nmax']:.3e} umax={d['umax']:.3e} TV(u)={d['tv_u']:.3e}")

elapsed = time.time() - t0
while len(snapshots) < n_snapshots:
    snapshots.append(snapshots[-1].copy())
    diag.append(diag[-1].copy())

arr = np.stack(snapshots, axis=0)
print("output shape:", arr.shape)

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", arr)
print(f"Saved pred_results/T_C.npy. Walltime: {elapsed:.1f}s. Diverged={diverged}")

print("--- diagnostics ---")
for d in diag:
    print(f"  t={d['t']:.3f}  mass={d['mass']:.4e}  ||m||={d['m_norm']:.3e}  Nmax={d['Nmax']:.3e}  umax={d['umax']:.3e}  TV(u)={d['tv_u']:.3e}")
