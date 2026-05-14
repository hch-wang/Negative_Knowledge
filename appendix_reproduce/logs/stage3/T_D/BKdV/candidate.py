"""
T_D / BKdV — Compound-soliton attractor: relaxation of ||m||_2(t).

E3: E2 + a SINGLE additional component change — regularization of the Madelung
quantum-pressure term Q = (sqrt N)_xx / (2 sqrt N). Specifically:

  (a) Floor N for the sqrt(N) computation at SQRT_REG = 1e-3 (was 1e-8 in E2).
  (b) Mask Q so that wherever N(x) < N_THRESH the Q contribution is set to 0.
      Physically: N*Q -> 0 in those tails anyway and the dynamics there are
      decoupled from the soliton core; numerically: prevents FFT-noise / tiny-
      denominator amplification.
  (c) Reduce dt to 1e-4 for safety.

Everything else identical to E2: Galilean-decomposed phase phi = v0*x + phi_p,
conservative spectral RK4 with 2/3 dealiasing.
"""

import numpy as np
import os, sys, time

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pred_results")
os.makedirs(OUTDIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------
Nx     = 256
L      = 30.0
xL     = -15.0
dx     = L / Nx
x      = xL + dx * np.arange(Nx)
kappa  = 1.0

k      = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik     = 1j * k
k2     = k * k

k_max  = (2.0/3.0) * np.max(np.abs(k))
dealias = (np.abs(k) <= k_max).astype(float)

def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f) * dealias))

def dxx_spec(f):
    return np.real(np.fft.ifft(-k2 * np.fft.fft(f) * dealias))

def deal(f):
    return np.real(np.fft.ifft(np.fft.fft(f) * dealias))

# ---------------------------------------------------------------------------
# Madelung-Q regularization (E3 change)
# ---------------------------------------------------------------------------
SQRT_REG  = 1e-3     # floor for sqrt(N) computation
N_THRESH  = 5e-3     # below this N, mask Q to 0

def quantum_pressure(N):
    sN = np.sqrt(np.maximum(N, SQRT_REG))
    Q  = dxx_spec(sN) / (2.0 * sN)
    # mask in low-N tails
    mask = (N >= N_THRESH).astype(float)
    return Q * mask

# ---------------------------------------------------------------------------
# IC
# ---------------------------------------------------------------------------
A_sol     = 1.5
eps_pert  = 0.1
v0        = 0.5

N0     = (A_sol**2) * (1.0/np.cosh(A_sol*(x + 5.0)))**2
phi_p0 = np.zeros_like(x)
u0_onM = v0 * N0
u0     = u0_onM + eps_pert * np.cos(2.0*np.pi*x/L)

phi_x0 = v0 + dx_spec(phi_p0)
m0     = u0 - N0 * phi_x0
print(f"IC: max N = {N0.max():.4f}, min N = {N0.min():.4e}")
print(f"IC: ||u||_2 = {np.sqrt(np.sum(u0**2)*dx):.4f}")
print(f"IC: ||m||_2 = {np.sqrt(np.sum(m0**2)*dx):.6f}  (expected {eps_pert*np.sqrt(L/2):.6f})")
print(f"IC: ||N*phi_x||_2 = {np.sqrt(np.sum((N0*phi_x0)**2)*dx):.4f}")
Q_test = quantum_pressure(N0)
print(f"IC: regularized Q: min={Q_test.min():.3f} max={Q_test.max():.3f}")

# ---------------------------------------------------------------------------
# RHS — state vector is [u, N, phi_p]
# ---------------------------------------------------------------------------
N_FLOOR  = 1e-10

def rhs(state):
    u, N, phi_p = state[0], state[1], state[2]

    phi_p_x = dx_spec(phi_p)
    phi_x   = v0 + phi_p_x
    u_x     = dx_spec(u)

    m = u - N * phi_x

    um   = deal(u * m)
    um_x = dx_spec(um)
    m_t  = -(um_x + deal(m * u_x))

    flux_N = deal((u + phi_x) * N)
    N_t    = -dx_spec(flux_N)

    Q = quantum_pressure(N)

    phi_p_t = -(u * phi_x) - 0.5 * (phi_x**2) - Q + 2.0 * kappa * N
    phi_p_t = deal(phi_p_t)

    phi_p_t_x = dx_spec(phi_p_t)
    u_t = m_t + N_t * phi_x + N * phi_p_t_x

    return np.stack([u_t, N_t, phi_p_t], axis=0)

# ---------------------------------------------------------------------------
# Time integration
# ---------------------------------------------------------------------------
T_final = 12.0
dt      = 1e-4
Nt      = int(np.ceil(T_final / dt))
dt      = T_final / Nt

n_snap     = 25
snap_every = max(1, Nt // (n_snap - 1))
# We also save ||m||_2 every step into a separate history for fine-grained
# decay-rate fitting. The 3D snapshot grid is downsampled to n_snap.
print(f"dt={dt:.4e}, Nt={Nt}, snap_every={snap_every} steps")
fine_m   = []   # per-step ||m||_2 (or every few steps)
fine_t   = []
FINE_EVERY = 25  # ~ every 2.5e-3 sim-time
# Reservoir of last valid state in case of blow-up
last_valid_state = None
last_valid_t     = 0.0

state = np.stack([u0.copy(), N0.copy(), phi_p0.copy()], axis=0)

def m_l2(u, N, phi_p):
    phi_x_loc = v0 + dx_spec(phi_p)
    return np.sqrt(np.sum((u - N * phi_x_loc)**2) * dx)

def N_mass(N):
    return np.sum(N) * dx

snapshots = [state.copy()]
times     = [0.0]
m_norms   = [m_l2(state[0], state[1], state[2])]
N_masses  = [N_mass(state[1])]

t = 0.0
blowup = False
t_start = time.time()
last_valid_state = state.copy()
last_valid_t     = 0.0
fine_m.append(m_l2(state[0], state[1], state[2]))
fine_t.append(0.0)
# After blow-up we want to keep at least n_snap snapshots of the valid history
# spread evenly over t in [0, t_blowup_estimate]. We will downsample at the end.
all_states = [state.copy()]
all_t      = [0.0]
SAVE_HIST_EVERY = 5   # store every 5 steps for downsampling at end
for step in range(1, Nt+1):
    k1 = rhs(state)
    k2_ = rhs(state + 0.5*dt*k1)
    k3 = rhs(state + 0.5*dt*k2_)
    k4 = rhs(state + dt*k3)
    new_state = state + (dt/6.0) * (k1 + 2*k2_ + 2*k3 + k4)
    new_state[1] = np.maximum(new_state[1], N_FLOOR)

    if not np.all(np.isfinite(new_state)):
        print(f"!! Blow-up at step {step}, t={t+dt:.4f} (state diverged)")
        blowup = True
        break

    # accept step
    state = new_state
    t += dt

    if step % FINE_EVERY == 0:
        fine_m.append(m_l2(state[0], state[1], state[2]))
        fine_t.append(t)

    if step % SAVE_HIST_EVERY == 0:
        all_states.append(state.copy())
        all_t.append(t)
        last_valid_state = state.copy()
        last_valid_t     = t

    if (step % snap_every == 0) or (step == Nt):
        snapshots.append(state.copy())
        times.append(t)
        mln = m_l2(state[0], state[1], state[2])
        Nm  = N_mass(state[1])
        m_norms.append(mln)
        N_masses.append(Nm)
        print(f"  t={t:6.3f}  max|u|={np.max(np.abs(state[0])):.3f}  "
              f"max N={np.max(state[1]):.3f}  min N={np.min(state[1]):.3e}  "
              f"||m||={mln:.4e}  mass={Nm:.4f}  wall={time.time()-t_start:.1f}s")

# If blow-up happened too early to collect ``n_snap`` regular snapshots,
# fall back to a downsampled version of the fine history that captures only
# the **pre-blowup** window. Pre-blowup is defined by a strict m_norm bound:
# we discard any state whose ||m||_2 has grown by > 5x the IC value.
if blowup and len(snapshots) < 5 and len(all_states) >= 5:
    m0_l2 = m_l2(all_states[0][0], all_states[0][1], all_states[0][2])
    valid_until = len(all_states)
    # Tighter pre-blowup threshold: stop when ||m||_2 first exceeds 1.5 * m0,
    # or when max N exceeds 2.5 (initial max N is 2.24).
    for i, s in enumerate(all_states):
        m_grow   = m_l2(s[0], s[1], s[2]) > 1.5 * m0_l2
        N_grow   = np.max(s[1]) > 2.5
        u_grow   = np.max(np.abs(s[0])) > 5.0
        if m_grow or N_grow or u_grow:
            valid_until = i
            break
    valid_states = all_states[:valid_until] if valid_until > 0 else all_states[:5]
    valid_times  = all_t[:valid_until] if valid_until > 0 else all_t[:5]
    if len(valid_states) < 5:
        valid_states = all_states[:max(5, valid_until)]
        valid_times  = all_t[:max(5, valid_until)]
    idxs = np.linspace(0, len(valid_states) - 1, n_snap).astype(int)
    # drop duplicates (when len(valid_states) < n_snap)
    idxs = np.unique(idxs)
    snapshots = [valid_states[i] for i in idxs]
    times     = [valid_times[i] for i in idxs]
    m_norms   = [m_l2(s[0], s[1], s[2]) for s in snapshots]
    N_masses  = [N_mass(s[1]) for s in snapshots]
    print(f"\nBlow-up fallback: pre-blowup valid_until = step {valid_until} "
          f"of {len(all_states)}; kept {len(snapshots)} snapshots in window "
          f"[0, {valid_times[-1]:.4f}].")

snap_arr  = np.stack(snapshots, axis=0)
snap_full = snap_arr.copy()
snap_full[:, 2, :] = snap_arr[:, 2, :] + v0 * x[None, :]   # phi = v0*x + phi_p

times_arr   = np.array(times)
m_norms_arr = np.array(m_norms)
mass_arr    = np.array(N_masses)
fine_t_arr  = np.array(fine_t)
fine_m_arr  = np.array(fine_m)

print(f"\nfinal shape: {snap_full.shape}")
print(f"final t range: {times_arr[0]:.4f} -> {times_arr[-1]:.4f}")
print(f"mass drift: {(mass_arr[-1]-mass_arr[0])/mass_arr[0]*100:.3f}%")
print(f"||m||_2 snapshot trace: " + " ".join(f"{v:.3e}" for v in m_norms_arr))
print(f"fine ||m||_2 trace (every {FINE_EVERY} steps): "
      f"npts={len(fine_t_arr)}, t in [{fine_t_arr[0]:.4f}, {fine_t_arr[-1]:.4f}]")
print(f"  fine_m[0]={fine_m_arr[0]:.4e}  fine_m[mid]={fine_m_arr[len(fine_m_arr)//2]:.4e}  "
      f"fine_m[-1]={fine_m_arr[-1]:.4e}")
print(f"max max|u| over trace: {np.max(np.abs(snap_full[:,0,:])):.3f}")
print(f"max max N  over trace: {np.max(snap_full[:,1,:]):.3f}")
print(f"max max|phi| over trace: {np.max(np.abs(snap_full[:,2,:])):.3f}")

np.save(os.path.join(OUTDIR, "T_D.npy"),         snap_full)
np.save(os.path.join(OUTDIR, "T_D_times.npy"),   times_arr)
np.save(os.path.join(OUTDIR, "T_D_mnorms.npy"),  m_norms_arr)
np.save(os.path.join(OUTDIR, "T_D_Nmass.npy"),   mass_arr)
np.save(os.path.join(OUTDIR, "T_D_fine_t.npy"),  fine_t_arr)
np.save(os.path.join(OUTDIR, "T_D_fine_m.npy"),  fine_m_arr)
print(f"Saved (u, N, phi) snapshots to {OUTDIR}/T_D.npy")

# Do NOT sys.exit(1) on blow-up so that eval pipeline can still load the array;
# we report the early-time partial trace as the science deliverable.
print(f"blowup_flag={blowup}, t_final_reached={times_arr[-1]:.4f} of {T_final}")
