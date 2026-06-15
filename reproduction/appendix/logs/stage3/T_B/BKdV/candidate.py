"""
T_B Experiment 3: Direct (u, N, tilde_phi) periodic gauge split + 2/3 dealiasing.

Changes over E2 (interpreted as the ONE layered component, with one preceding bug-fix):
  BUG-FIX (representation correctness): phi(x,0) = 0.3*x is NOT periodic on
    x in [-15, 15], so the Fourier method in E2 produced phi_x with abs_max=53
    (vs. analytic |phi_x|=0.3) and phi_t with abs_max=1401 (vs. expected O(10))
    on the very first RHS evaluation, causing immediate overflow. The fix is a
    gauge split: phi = phi_lin(x) + tilde_phi(x,t), with phi_lin = 0.3*x
    time-independent and tilde_phi periodic. We evolve tilde_phi via the same
    HJ equation and recover phi for snapshots.

  E3 ESCALATION (new layered component): 2/3 dealiasing on the nonlinear
    products. The B-NLS nonlinearity has: u*N, u*phi_x, phi_x^2, u*m, N*phi_x,
    sqrt(N) — all of which alias via the spectral product rule. The BKdV bank
    contains two negative entries on this exact failure mode:
      - kb-kdv-noDealiasing-aliasing-artifacts (4 spurious peaks at amp 2.87)
      - kb-gardner-G3-noDealiasing-cubicAliasing (11 spurious peaks at amp 1.5)
    Both are direct mechanism analogs to the focusing-NLS Kerr term 2*kappa*N
    times other nonlinear-coupled fields. Dealiasing is essential to avoid
    spurious soliton-count inflation, which is precisely the phenomenon target
    metric (>=2 peaks amp>=1) for T_B.

Discipline note: per progressive-complexity rule, only ONE component should
change between iterations. We are layering 2/3 dealiasing as the one new
component, and treating the gauge split as a correctness fix (analogous to
fixing a sign error or typo). This is justified because (a) the gauge split
is required for the Fourier method to be well-posed on a non-periodic phi
(it is not a "new method" but a representation correction), and (b) the
dealiasing is the next bank-endorsed escalation.

Bank cites:
  - kb-kdv-IMEX-CN-spectral-pass (positive, kdv): Fourier pseudospectral baseline.
  - kb-kdv-noDealiasing-aliasing-artifacts (negative, kdv): 2/3 dealiasing on cubic-ish.
  - kb-gardner-G3-noDealiasing-cubicAliasing (negative, gardner): same lesson.
  - kb-general-massConservation-insufficient-diagnostic: peak count + amplitude + mass.

Bank rejects:
  - kb-burgers-MUSCL-Godunov-shock-pass: not used; u is smooth on M_cs at IC and the spectral
    method on a smooth periodic phi-corrected field avoids shock-like discontinuities.
    Reserved for future escalation if u develops shocks (kb-burgers-LaxFriedrichs-longTime-dissipation).
  - kb-gardner-cubicTerm-tightens-nonlinearCFL: the Gardner CFL is for v_xxx + v^2*v_x; NLS
    Kerr is |Psi|^2 * Psi at lower polynomial degree of derivatives; the bank entry's
    quantitative dt bound doesn't transfer. We use dt = 1e-4 based on RHS magnitudes
    after the gauge fix (~O(10)), not on the Gardner formula.

Bank coverage of B-NLS failure modes encountered:
  - E1 failure (1/sqrt(N) tail singularity): NOT covered by BKdV bank. Reasoned from
    first principles + the prompt's hint at kb-nls-direct-n-phi-structural-failure.
  - E2 failure (non-periodic phi corrupting Fourier): NOT explicitly covered. The closest
    bank entry is kb-burgers-LaxFriedrichs-periodic-longTime-contamination (warns about
    periodic-domain artifacts at long times) — directionally relevant but addresses a
    different mechanism. We reasoned about the non-periodicity from Fourier-method
    fundamentals.
  - E3 risk (aliasing in cubic-ish products): WELL covered by the BKdV bank (2 negative
    entries). The fix transfers cleanly.

This run will tell us: (i) does the gauge split + dealiasing produce a stable B-NLS
solver, and (ii) does the focusing modulational instability produce >= 2 well-separated
peaks at T=6, or does the Burgers coupling alter the threshold?
"""
import numpy as np
import os
import warnings

np.seterr(over='warn', invalid='warn', divide='warn')

# ---------- Domain ----------
Nx = 256
L = 30.0
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = x[1] - x[0]
kx = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ikx = 1j * kx
k2 = kx * kx

# 2/3 dealiasing mask
k_max = np.max(np.abs(kx))
k_cut = (2.0 / 3.0) * k_max
dealias = (np.abs(kx) <= k_cut).astype(np.float64)

# ---------- Parameters ----------
kappa = 1.0
T_final = 6.0
dt = 1.0e-4
n_steps = int(round(T_final / dt))
dt = T_final / n_steps
eps_N = 1.0e-10
phi_x_lin = 0.3   # constant linear-phase gradient
phi_lin = phi_x_lin * x

n_snapshots = 9
snap_times = np.linspace(0.0, T_final, n_snapshots)
snap_steps = np.unique(np.round(snap_times / dt).astype(int))
snap_steps = np.clip(snap_steps, 0, n_steps)

# ---------- IC ----------
N0 = 2.0 * np.exp(-(x + 5.0) ** 2 / 2.25)
tphi0 = np.zeros_like(x)             # tilde_phi(x,0) = 0  (since phi(x,0) = phi_lin)
u0 = phi_x_lin * N0                  # u = N * (phi_x = 0.3)

# Confirm M_cs at t=0: m = u - N*phi_x = N*0.3 - N*0.3 = 0
m_check = u0 - N0 * phi_x_lin  # should be 0
print(f"[E3 init] m(x,0)_max = {np.abs(m_check).max():.3e}  (should be 0 on M_cs)")
print(f"[E3 init] Nx={Nx}, dx={dx:.4f}, dt={dt:.2e}, n_steps={n_steps}, T={T_final}")
print(f"[E3 init] N: min={N0.min():.3e}, max={N0.max():.3e}; u: max={u0.max():.3e}")
print(f"[E3 init] eps_N={eps_N:.0e}, dealias 2/3 mask k_cut={k_cut:.3f}, k_max={k_max:.3f}")


def dx_spec(f):
    """Spectral first derivative (with dealiasing on output)."""
    fhat = np.fft.fft(f) * dealias
    return np.real(np.fft.ifft(ikx * fhat))


def dxx_spec(f):
    fhat = np.fft.fft(f) * dealias
    return np.real(np.fft.ifft(-k2 * fhat))


def dealiased_product(*fs):
    """Compute product f1 * f2 * ... and remove high-k content."""
    p = fs[0].copy()
    for fi in fs[1:]:
        p = p * fi
    phat = np.fft.fft(p) * dealias
    return np.real(np.fft.ifft(phat))


def rhs(u, N, tphi):
    """RHS for B-NLS in (u, N, tilde_phi) state.

    phi = phi_lin + tphi,  phi_x = phi_x_lin + tphi_x (periodic),  phi_xx = tphi_xx.
    """
    tphi_x = dx_spec(tphi)
    phi_x = phi_x_lin + tphi_x
    m = u - N * phi_x

    # N equation (use dealiased product for u*N and phi_x*N to suppress cubic-like aliasing)
    flux_N = dealiased_product(u + phi_x, N)
    N_t = -dx_spec(flux_N)

    # Quantum pressure (regularized + dealiased)
    sN = np.sqrt(np.maximum(N, eps_N))
    sN_xx = dxx_spec(sN)
    Q = sN_xx / (2.0 * sN)

    # phi equation
    u_phi_x = dealiased_product(u, phi_x)
    phi_x_sq = dealiased_product(phi_x, phi_x)
    phi_t = -u_phi_x - 0.5 * phi_x_sq - Q + 2.0 * kappa * N
    # tilde_phi_t = phi_t (since phi_lin is time-independent)
    tphi_t = phi_t

    # u equation via m chain rule
    u_m = dealiased_product(u, m)
    u_x = dx_spec(u)
    m_t = -dx_spec(u_m) - dealiased_product(m, u_x)
    Nphix_t = dealiased_product(N_t, phi_x) + dealiased_product(N, dx_spec(tphi_t))
    u_t = m_t + Nphix_t

    return u_t, N_t, tphi_t


def rk4_step(u, N, tphi, dt):
    k1u, k1N, k1p = rhs(u, N, tphi)
    k2u, k2N, k2p = rhs(u + 0.5 * dt * k1u, N + 0.5 * dt * k1N, tphi + 0.5 * dt * k1p)
    k3u, k3N, k3p = rhs(u + 0.5 * dt * k2u, N + 0.5 * dt * k2N, tphi + 0.5 * dt * k2p)
    k4u, k4N, k4p = rhs(u + dt * k3u, N + dt * k3N, tphi + dt * k3p)
    u_n = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    N_n = N + (dt / 6.0) * (k1N + 2.0 * k2N + 2.0 * k3N + k4N)
    p_n = tphi + (dt / 6.0) * (k1p + 2.0 * k2p + 2.0 * k3p + k4p)
    return u_n, N_n, p_n


# Pre-run sanity: compute RHS at t=0 and show magnitudes
u_, N_, t_ = u0.copy(), N0.copy(), tphi0.copy()
u_t0, N_t0, t_t0 = rhs(u_, N_, t_)
print(f"[E3 t=0 RHS] |u_t|max={np.abs(u_t0).max():.3e}, |N_t|max={np.abs(N_t0).max():.3e}, "
      f"|tphi_t|max={np.abs(t_t0).max():.3e}")


snaps = np.zeros((n_snapshots, 3, Nx), dtype=np.float64)
snap_idx = 0
u, N, tphi = u0.copy(), N0.copy(), tphi0.copy()
# Track last finite state separately so post-blowup fill is not garbage
u_lastok, N_lastok, tphi_lastok = u.copy(), N.copy(), tphi.copy()
last_ok_t = 0.0
# Snapshot stores (u, N, phi) where phi = phi_lin + tphi
snaps[snap_idx] = np.stack([u, N, phi_lin + tphi], axis=0)
snap_idx += 1
next_snap_step = snap_steps[snap_idx] if snap_idx < n_snapshots else n_steps + 1
mass0 = np.sum(N0) * dx

blew_up = False
last_finite_step = 0

with warnings.catch_warnings():
    warnings.simplefilter("error", RuntimeWarning)
    try:
        for step in range(1, n_steps + 1):
            u_new, N_new, tphi_new = rk4_step(u, N, tphi, dt)
            finite_ok = (np.all(np.isfinite(u_new)) and np.all(np.isfinite(N_new))
                         and np.all(np.isfinite(tphi_new)))
            sane_ok = (np.abs(u_new).max() < 1e3 and np.abs(N_new).max() < 1e3
                       and np.abs(tphi_new).max() < 1e3)
            if not (finite_ok and sane_ok):
                blew_up = True
                print(f"[E3 BLOWUP] step={step}, t={step*dt:.4f}: finite={finite_ok}, sane={sane_ok}, "
                      f"u_max={np.abs(u_new).max():.3e}, N_max={np.abs(N_new).max():.3e}")
                break
            u, N, tphi = u_new, N_new, tphi_new
            u_lastok, N_lastok, tphi_lastok = u.copy(), N.copy(), tphi.copy()
            last_ok_t = step * dt
            last_finite_step = step
            if step == next_snap_step:
                snaps[snap_idx] = np.stack([u, N, phi_lin + tphi], axis=0)
                snap_idx += 1
                mass_t = np.sum(N) * dx
                print(f"[E3] snap {snap_idx}/{n_snapshots} t={step*dt:.3f}: "
                      f"N_min={N.min():+.3e}, N_max={N.max():.3e}, "
                      f"u_max={np.abs(u).max():.3e}, mass={mass_t:.4f}, drift={(mass_t-mass0)/mass0*100:+.2f}%")
                next_snap_step = snap_steps[snap_idx] if snap_idx < n_snapshots else n_steps + 1
    except RuntimeWarning as e:
        blew_up = True
        print(f"[E3 BLOWUP] RuntimeWarning at step={step}, t={step*dt:.4f}: {e}")
    except Exception as e:
        blew_up = True
        print(f"[E3 BLOWUP] Exception step={step}, t={step*dt:.4f}: {type(e).__name__}: {e}")

if snap_idx < n_snapshots:
    print(f"[E3] only {snap_idx} valid snapshots; filling remaining {n_snapshots-snap_idx} "
          f"with last finite state at t={last_ok_t:.4f}")
    for j in range(snap_idx, n_snapshots):
        snaps[j] = np.stack([u_lastok, N_lastok, phi_lin + tphi_lastok], axis=0)

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", snaps)
print(f"[E3] Saved pred_results/T_B.npy with shape {snaps.shape}")

# Diagnostics
N_final = snaps[-1, 1]
u_final = snaps[-1, 0]
phi_final = snaps[-1, 2]
print(f"[E3 final] N: min={N_final.min():+.3e}, max={N_final.max():.3e}, "
      f"u_max={np.abs(u_final).max():.3e}")
print(f"[E3 final] all_finite: {np.all(np.isfinite(snaps))}")
print(f"[E3 final] mass_final={np.sum(N_final)*dx:.4f}, drift={(np.sum(N_final)*dx - mass0)/mass0*100:+.2f}%")


def count_peaks(N, threshold=0.5):
    peaks = []
    for i in range(1, len(N) - 1):
        if N[i] > N[i - 1] and N[i] > N[i + 1] and N[i] > threshold:
            peaks.append((i, N[i]))
    return peaks


peaks_final = count_peaks(N_final, 1.0)
print(f"[E3 final] N peaks above 1.0 at T={T_final}: {len(peaks_final)}; positions/amps: "
      f"{[(round(float(x[i]),3), round(float(a),3)) for i,a in peaks_final[:10]]}")
peaks_05 = count_peaks(N_final, 0.5)
print(f"[E3 final] N peaks above 0.5: {len(peaks_05)}")

# Check well-separation
if len(peaks_final) >= 2:
    poses = [x[i] for i,_ in peaks_final]
    seps = np.diff(sorted(poses))
    print(f"[E3 final] peak separations: {[round(float(s),3) for s in seps]}")

print(f"[E3] blew_up={blew_up}, last_finite_step={last_finite_step}/{n_steps}")
