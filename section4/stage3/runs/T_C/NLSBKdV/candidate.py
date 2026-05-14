"""
T_C / NLSBKdV — E2
Single component upgrade over E1: SPECTRAL on u -> MUSCL-Godunov SSP-RK3 on u.
Still NO dealiasing on |Psi|^2.

Sign convention: STANDARD NLS -(1/2)*Psi_xx (HYPOTHESIS per kb-nls-sign-convention).
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

# ---------- MUSCL-Godunov SSP-RK3 on u for f(u) = u^2/2 (Burgers) ----------
# Periodic BCs. Cell-centered values at x_i. Use van-Leer limited reconstruction
# at cell faces, Godunov exact Riemann for f(u)=u^2/2.

def van_leer(a, b):
    # van Leer limiter on slopes a (left) and b (right): 2ab/(a+b) when same sign, else 0
    out = np.zeros_like(a)
    same = (a*b > 0.0)
    out[same] = 2.0*a[same]*b[same] / (a[same] + b[same] + 1e-300)
    return out

def godunov_burgers_flux(uL, uR):
    # exact Riemann for f(u)=u^2/2 (Burgers)
    fL = 0.5*uL*uL
    fR = 0.5*uR*uR
    flux = np.where(uL > uR,
                    # shock: pick the upwind face value via Rankine-Hugoniot
                    np.where(0.5*(uL+uR) >= 0.0, fL, fR),
                    # rarefaction: sonic point u=0 if it lies between uL, uR
                    np.where(uL >= 0.0, fL,
                             np.where(uR <= 0.0, fR, 0.0)))
    return flux

def burgers_rhs_muscl(u):
    # slopes on cell-centered u with periodic BCs
    um = np.roll(u, +1)   # u_{i-1}
    up = np.roll(u, -1)   # u_{i+1}
    a = u - um  # backward
    b = up - u  # forward
    slope = van_leer(a, b)
    # Reconstruct face values:
    #   uR_{i+1/2} = u_i + 0.5*slope_i        (right state at face i+1/2)
    #   uL_{i+1/2} = u_{i-? } ... actually:
    # Left state at face i+1/2 comes from cell i: u_i + 0.5*slope_i
    # Right state at face i+1/2 comes from cell i+1: u_{i+1} - 0.5*slope_{i+1}
    uL_face = u + 0.5*slope               # at face i+1/2, left state (from cell i)
    uR_face = np.roll(u - 0.5*slope, -1)  # at face i+1/2, right state (from cell i+1)
    F = godunov_burgers_flux(uL_face, uR_face)  # flux at face i+1/2
    # divergence: (F_{i+1/2} - F_{i-1/2}) / dx
    F_im = np.roll(F, +1)
    return -(F - F_im)/dx

def step_u_muscl_ssprk3(u, dt_u):
    k1 = burgers_rhs_muscl(u)
    u1 = u + dt_u*k1
    k2 = burgers_rhs_muscl(u1)
    u2 = 0.75*u + 0.25*(u1 + dt_u*k2)
    k3 = burgers_rhs_muscl(u2)
    return (1.0/3.0)*u + (2.0/3.0)*(u2 + dt_u*k3)

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
    # Strang Madelung-Psi
    rho = (np.abs(Psi_tilde))**2
    Psi_tilde = Psi_tilde * np.exp(1j * kappa * rho * (dt/2))
    Psi_hat = np.fft.fft(Psi_tilde)
    Psi_hat = Psi_hat * lin_phase_full
    Psi_tilde = np.fft.ifft(Psi_hat)
    rho = (np.abs(Psi_tilde))**2
    Psi_tilde = Psi_tilde * np.exp(1j * kappa * rho * (dt/2))

    # u sector: MUSCL-Godunov SSP-RK3
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
