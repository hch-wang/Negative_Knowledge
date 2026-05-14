"""S5 candidate solver: B-NLS on Mcs (bright soliton, matched u = N*phi_x).

Three method variants are exercised to characterize how time-splitting choices
affect preservation of the manifold Mcs := {m := u - N*phi_x = 0}.

System (periodic, x in [-15, 15]):
    m_t + (u*m)_x + m*u_x = 0,         m := u - N*phi_x
    N_t + d_x((u + phi_x) * N) = 0
    phi_t + u*phi_x + (1/2)*phi_x^2 + Q(N) - 2*kappa*N = 0,  Q = sqrt(N)_xx/(2 sqrt(N))

Method A ("on-manifold Madelung-Psi"): Reformulate the (N, phi) sector with the
Burgers boost as a single complex Psi = sqrt(N) exp(i phi) equation
    i Psi_t = -(1/2) Psi_xx - kappa |Psi|^2 Psi + i*[u Psi_x + (u_x/2) Psi]
with u := N phi_x = Im(conj(Psi) Psi_x) reconstructed every step. By construction
m = u - N phi_x = 0 to machine precision. This is the natural Strang split of
the (kinetic + nonlinear + boost-transport) sub-flows.

Method B ("decoupled Strang"): treat u as an independent field. Strang split
[ half u-Burgers (m frozen at m_n) | full NLS (kinetic + nonlinear, no boost) |
half u-Burgers ]. u is advanced as inviscid Burgers (u_t + u u_x = 0) by RK4 in
spectral space (with a small hyperviscosity for stability). This ignores the
coupling between u and (N, phi) and lets ||m|| drift.

Method C ("decoupled Lie"): Lie splitting of the same as B (full u-Burgers then
full NLS), with the boost fully omitted — to show even worse drift than Strang.

Outputs (pred_results/S5.npz):
    method_<A|B|C>_t, method_<A|B|C>_u, method_<A|B|C>_N, method_<A|B|C>_phi,
    method_<A|B|C>_m_norm, method_<A|B|C>_mass, method_<A|B|C>_energy,
    method_<A|B|C>_peak_x
"""
from __future__ import annotations

import os
import numpy as np

# ---------------------------------------------------------------------------
# Domain / parameters
# ---------------------------------------------------------------------------
L = 30.0          # full domain length
X_LEFT = -15.0
X_RIGHT = 15.0
NX = 256
KAPPA = 1.0
T_FINAL = 6.0

x = np.linspace(X_LEFT, X_RIGHT, NX, endpoint=False)
dx = x[1] - x[0]
k = 2.0 * np.pi * np.fft.fftfreq(NX, d=dx)
ik = 1j * k
k2 = k ** 2
# 2/3 dealiasing filter for the nonlinear products in Burgers-style steps.
kmax = np.max(np.abs(k))
dealias = (np.abs(k) <= (2.0 / 3.0) * kmax).astype(float)

# Soliton initial condition.
N0 = 2.0 * (1.0 / np.cosh(np.sqrt(2.0) * (x + 5.0))) ** 2
phi0 = 0.25 * x
phix0 = 0.25 * np.ones_like(x)
u0 = 0.25 * N0  # = N0 * phi_x  -> m0 = 0


def dx_spec(f):
    return np.real(np.fft.ifft(ik * np.fft.fft(f)))


def reconstruct_u_from_psi(psi):
    """u = N*phi_x = Im(conj(psi) * d_x psi)."""
    psi_x = np.fft.ifft(ik * np.fft.fft(psi))
    return np.imag(np.conj(psi) * psi_x)


def phix_from_psi(psi, eps=1e-14):
    """phi_x = Im(conj(psi) * psi_x) / |psi|^2, well-defined even if phi unwraps."""
    psi_x = np.fft.ifft(ik * np.fft.fft(psi))
    return np.imag(np.conj(psi) * psi_x) / np.maximum(np.abs(psi) ** 2, eps)


def m_from_fields_psi(u, psi):
    """Compute m = u - N phi_x using Psi (avoids phase unwrap artifacts)."""
    return u - reconstruct_u_from_psi(psi)


def m_from_fields(u, N, phi_x):
    """phi_x is already the gradient (NOT phi itself)."""
    return u - N * phi_x


def mass(N):
    return np.sum(N) * dx


def total_energy(u, N, phi):
    """Heuristic conserved-quantity proxy for diagnostics only."""
    phix = dx_spec(phi)
    return _energy_with_phix(u, N, phix)


def _energy_with_phix(u, N, phix):
    sqrtN = np.sqrt(np.maximum(N, 1e-30))
    sqrtNx = dx_spec(sqrtN)
    kinetic = 0.5 * np.sum(N * (u ** 2)) * dx
    quantum = 0.5 * np.sum(sqrtNx ** 2) * dx
    interaction = -0.5 * KAPPA * np.sum(N ** 2) * dx
    return kinetic + quantum + interaction


def peak_x(N):
    i = int(np.argmax(N))
    return float(x[i])


# ---------------------------------------------------------------------------
# Method A: on-manifold Madelung-Psi with Strang(kinetic-nonlinear-boost)
# ---------------------------------------------------------------------------
def step_psi_kinetic(psi, dt):
    """exact propagator for i psi_t = -(1/2) psi_xx, in Fourier space."""
    return np.fft.ifft(np.exp(-0.5j * k2 * dt) * np.fft.fft(psi))


def step_psi_nonlinear(psi, dt):
    """exact propagator for i psi_t = -kappa |psi|^2 psi."""
    return np.exp(1j * KAPPA * np.abs(psi) ** 2 * dt) * psi


def step_psi_boost(psi, dt):
    """advection sub-step: psi_t = -u psi_x - (u_x/2) psi  (norm-preserving).

    We use a Strang-style update that recomputes u := Im(conj(psi) psi_x) at the
    midpoint of the sub-step, then applies an RK4 advection. Conservative form
    of the advection is psi_t = -(1/2)[(u psi)_x + u psi_x].
    """
    def rhs(z):
        u_local = np.imag(np.conj(z) * np.fft.ifft(ik * np.fft.fft(z)))
        zx = np.fft.ifft(ik * np.fft.fft(z))
        uz_x = np.fft.ifft(ik * np.fft.fft(u_local * z))
        return -0.5 * (uz_x + u_local * zx)

    k1 = rhs(psi)
    k2_ = rhs(psi + 0.5 * dt * k1)
    k3 = rhs(psi + 0.5 * dt * k2_)
    k4 = rhs(psi + dt * k3)
    return psi + (dt / 6.0) * (k1 + 2 * k2_ + 2 * k3 + k4)


def method_A(dt=0.001, n_save=121):
    """Strang split: boost(dt/2) -> kinetic(dt/2) -> nonlinear(dt) -> kinetic(dt/2) -> boost(dt/2)."""
    psi = np.sqrt(N0) * np.exp(1j * phi0)
    steps = int(round(T_FINAL / dt))
    save_every = max(1, steps // (n_save - 1))
    snaps = {"t": [], "u": [], "N": [], "phi": [], "m_norm": [], "mass": [], "energy": [], "peak_x": []}

    def record(tt, psi):
        N = np.abs(psi) ** 2
        phi_eff = np.angle(psi)  # wrapped, kept only for snapshot reference
        phix = phix_from_psi(psi)
        u = reconstruct_u_from_psi(psi)  # = N * phi_x exactly
        snaps["t"].append(tt)
        snaps["u"].append(u.copy())
        snaps["N"].append(N.copy())
        snaps["phi"].append(phi_eff.copy())
        # m = u - N*phi_x, computed without phase unwrap: should be zero by construction.
        m_local = u - N * phix
        snaps["m_norm"].append(float(np.sqrt(np.sum(m_local ** 2) * dx)))
        snaps["mass"].append(float(mass(N)))
        # energy uses phix not phi.
        snaps["energy"].append(float(_energy_with_phix(u, N, phix)))
        snaps["peak_x"].append(peak_x(N))

    record(0.0, psi)
    for n in range(1, steps + 1):
        psi = step_psi_boost(psi, 0.5 * dt)
        psi = step_psi_kinetic(psi, 0.5 * dt)
        psi = step_psi_nonlinear(psi, dt)
        psi = step_psi_kinetic(psi, 0.5 * dt)
        psi = step_psi_boost(psi, 0.5 * dt)
        if n % save_every == 0 or n == steps:
            record(n * dt, psi)
    return {kk: np.array(vv) for kk, vv in snaps.items()}


# ---------------------------------------------------------------------------
# Method B: decoupled Strang.  u is treated independently as inviscid Burgers,
# integrated with a 1st-order upwind finite-difference (shock-stable, no need
# for viscosity).  NLS sub-step uses pure Madelung-Psi (no boost).  Final u
# is NOT reconciled with N, phi.
# ---------------------------------------------------------------------------
def step_u_upwind(u, dt):
    """Single forward-Euler upwind step of u_t + u u_x = 0 (conservative form).

    Conservative form: u_t + (u^2/2)_x = 0, use Engquist-Osher / upwind flux:
       F_{i+1/2} = 0.5 * (max(u_i,0)^2 + min(u_{i+1},0)^2)
    This is shock-stable and dissipates entropy.
    """
    uL = u
    uR = np.roll(u, -1)
    F = 0.5 * (np.maximum(uL, 0.0) ** 2 + np.minimum(uR, 0.0) ** 2)
    F_left = np.roll(F, 1)
    return u - (dt / dx) * (F - F_left)


def step_u_burgers(u, dt, n_substeps=4):
    """Sub-step the upwind scheme to respect CFL."""
    h = dt / n_substeps
    for _ in range(n_substeps):
        u = step_u_upwind(u, h)
    return u


def step_psi_pure_nls(psi, dt):
    """Strang within NLS sub: kinetic(dt/2) -> nonlinear(dt) -> kinetic(dt/2)."""
    psi = step_psi_kinetic(psi, 0.5 * dt)
    psi = step_psi_nonlinear(psi, dt)
    psi = step_psi_kinetic(psi, 0.5 * dt)
    return psi


def method_B(dt=0.001, n_save=121):
    u = u0.copy()
    psi = np.sqrt(N0) * np.exp(1j * phi0)
    steps = int(round(T_FINAL / dt))
    save_every = max(1, steps // (n_save - 1))
    snaps = {"t": [], "u": [], "N": [], "phi": [], "m_norm": [], "mass": [], "energy": [], "peak_x": []}

    def record(tt, u, psi):
        N = np.abs(psi) ** 2
        phi_eff = np.angle(psi)
        phix = phix_from_psi(psi)
        snaps["t"].append(tt)
        snaps["u"].append(u.copy())
        snaps["N"].append(N.copy())
        snaps["phi"].append(phi_eff.copy())
        m_local = u - N * phix
        snaps["m_norm"].append(float(np.sqrt(np.sum(m_local ** 2) * dx)))
        snaps["mass"].append(float(mass(N)))
        snaps["energy"].append(float(_energy_with_phix(u, N, phix)))
        snaps["peak_x"].append(peak_x(N))

    record(0.0, u, psi)
    for n in range(1, steps + 1):
        u = step_u_burgers(u, 0.5 * dt)
        psi = step_psi_pure_nls(psi, dt)
        u = step_u_burgers(u, 0.5 * dt)
        if n % save_every == 0 or n == steps:
            record(n * dt, u, psi)
    return {kk: np.array(vv) for kk, vv in snaps.items()}


# ---------------------------------------------------------------------------
# Method A-Lie: same operators as A but Lie ordering [boost(dt) kinetic(dt) nonlinear(dt)].
# Tests ordering sensitivity inside the on-manifold method.
# ---------------------------------------------------------------------------
def method_A_lie(dt=0.001, n_save=121):
    psi = np.sqrt(N0) * np.exp(1j * phi0)
    steps = int(round(T_FINAL / dt))
    save_every = max(1, steps // (n_save - 1))
    snaps = {"t": [], "u": [], "N": [], "phi": [], "m_norm": [], "mass": [], "energy": [], "peak_x": []}

    def record(tt, psi):
        N = np.abs(psi) ** 2
        phi_eff = np.angle(psi)
        phix = phix_from_psi(psi)
        u = reconstruct_u_from_psi(psi)
        snaps["t"].append(tt)
        snaps["u"].append(u.copy())
        snaps["N"].append(N.copy())
        snaps["phi"].append(phi_eff.copy())
        snaps["m_norm"].append(float(np.sqrt(np.sum((u - N * phix) ** 2) * dx)))
        snaps["mass"].append(float(mass(N)))
        snaps["energy"].append(float(_energy_with_phix(u, N, phix)))
        snaps["peak_x"].append(peak_x(N))

    record(0.0, psi)
    for n in range(1, steps + 1):
        psi = step_psi_boost(psi, dt)
        psi = step_psi_kinetic(psi, dt)
        psi = step_psi_nonlinear(psi, dt)
        if n % save_every == 0 or n == steps:
            record(n * dt, psi)
    return {kk: np.array(vv) for kk, vv in snaps.items()}


# ---------------------------------------------------------------------------
# Method D: fully coupled RK4 on (u, N, phi) directly, with QP regularization.
# Treats the 3-variable system simultaneously — no operator split.
# ---------------------------------------------------------------------------
def _rhs_uNphi(state, qp_eps=1e-8):
    """Right-hand sides of the original B-NLS in (u, N, phi)."""
    u, N, phi = state
    phix = dx_spec(phi)
    # N continuity: N_t = -((u + phix) * N)_x
    flux_N = (u + phix) * N
    N_t = -dx_spec(flux_N)
    # phi HJ: phi_t = -u phix - 0.5*phix^2 - Q(N) + 2*kappa*N
    sqrtN = np.sqrt(np.maximum(N, qp_eps))
    sqrtN_xx = np.real(np.fft.ifft(-k2 * np.fft.fft(sqrtN)))
    Q = sqrtN_xx / (2.0 * sqrtN)
    phi_t = -u * phix - 0.5 * phix * phix - Q + 2.0 * KAPPA * N
    # u from m equation: m_t = -(u m)_x - m u_x.
    # Use the identity m = u - N phix and solve for u_t via implicit consistency.
    # Easier: u_t = m_t + (N phix)_t. We get (N phix)_t from N_t and phi_xt.
    # phi_xt = d_x(phi_t) -> use spectral derivative of phi_t.
    phi_xt = dx_spec(phi_t)
    m = u - N * phix
    m_uflux = dx_spec(u * m)
    ux = dx_spec(u)
    m_t = -m_uflux - m * ux
    Nphix_t = N_t * phix + N * phi_xt
    u_t = m_t + Nphix_t
    return np.array([u_t, N_t, phi_t])


def method_D(dt=0.0005, n_save=121, qp_eps=1e-8):
    """Coupled RK4 on (u, N, phi) — no operator splitting."""
    u = u0.copy()
    N = N0.copy()
    phi = phi0.copy()
    state = np.array([u, N, phi])
    steps = int(round(T_FINAL / dt))
    save_every = max(1, steps // (n_save - 1))
    snaps = {"t": [], "u": [], "N": [], "phi": [], "m_norm": [], "mass": [], "energy": [], "peak_x": []}

    def record(tt, state):
        u, N, phi = state
        phix = dx_spec(phi)
        snaps["t"].append(tt)
        snaps["u"].append(u.copy())
        snaps["N"].append(N.copy())
        snaps["phi"].append(phi.copy())
        snaps["m_norm"].append(float(np.sqrt(np.sum((u - N * phix) ** 2) * dx)))
        snaps["mass"].append(float(mass(N)))
        snaps["energy"].append(float(_energy_with_phix(u, N, phix)))
        snaps["peak_x"].append(peak_x(N))

    record(0.0, state)
    for n in range(1, steps + 1):
        k1 = _rhs_uNphi(state, qp_eps)
        k2_ = _rhs_uNphi(state + 0.5 * dt * k1, qp_eps)
        k3 = _rhs_uNphi(state + 0.5 * dt * k2_, qp_eps)
        k4 = _rhs_uNphi(state + dt * k3, qp_eps)
        state = state + (dt / 6.0) * (k1 + 2 * k2_ + 2 * k3 + k4)
        if not np.all(np.isfinite(state)):
            print("Method D diverged at step", n)
            break
        if n % save_every == 0 or n == steps:
            record(n * dt, state)
    return {kk: np.array(vv) for kk, vv in snaps.items()}


# ---------------------------------------------------------------------------
# Method C: decoupled Lie split (worst case baseline).
# ---------------------------------------------------------------------------
def method_C(dt=0.001, n_save=121):
    u = u0.copy()
    psi = np.sqrt(N0) * np.exp(1j * phi0)
    steps = int(round(T_FINAL / dt))
    save_every = max(1, steps // (n_save - 1))
    snaps = {"t": [], "u": [], "N": [], "phi": [], "m_norm": [], "mass": [], "energy": [], "peak_x": []}

    def record(tt, u, psi):
        N = np.abs(psi) ** 2
        phi_eff = np.angle(psi)
        phix = phix_from_psi(psi)
        snaps["t"].append(tt)
        snaps["u"].append(u.copy())
        snaps["N"].append(N.copy())
        snaps["phi"].append(phi_eff.copy())
        m_local = u - N * phix
        snaps["m_norm"].append(float(np.sqrt(np.sum(m_local ** 2) * dx)))
        snaps["mass"].append(float(mass(N)))
        snaps["energy"].append(float(_energy_with_phix(u, N, phix)))
        snaps["peak_x"].append(peak_x(N))

    record(0.0, u, psi)
    for n in range(1, steps + 1):
        u = step_u_burgers(u, dt)
        psi = step_psi_pure_nls(psi, dt)
        if n % save_every == 0 or n == steps:
            record(n * dt, u, psi)
    return {kk: np.array(vv) for kk, vv in snaps.items()}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def _diag_summary(label, R):
    m_norm = R["m_norm"]
    mass_arr = R["mass"]
    energy = R["energy"]
    peak = R["peak_x"]
    drift = np.abs(mass_arr - mass_arr[0]).max()
    e_drift = np.abs(energy - energy[0]).max()
    peak_drift = peak[-1] - peak[0]
    print(
        f"[{label}] T={R['t'][-1]:.3f}  ||m||_2 max={m_norm.max():.3e}  end={m_norm[-1]:.3e}  "
        f"mass_drift={drift:.3e}  energy_drift={e_drift:.3e}  peak_drift={peak_drift:.3f}"
    )
    nan_flag = bool(np.any(np.isnan(R["u"])) or np.any(np.isnan(R["N"])))
    print(f"        nan={nan_flag}  min_N={float(np.min(R['N'])):.3e}")


if __name__ == "__main__":
    os.makedirs("pred_results", exist_ok=True)

    print("Running Method A (Strang on-manifold) dt=0.001 ...")
    RA = method_A(dt=0.001)
    _diag_summary("A_dt001", RA)

    print("Running Method A (Strang on-manifold) dt=0.0005 ...")
    RA2 = method_A(dt=0.0005)
    _diag_summary("A_dt0005", RA2)

    print("Running Method A (Strang on-manifold) dt=0.005 (coarse) ...")
    RA3 = method_A(dt=0.005)
    _diag_summary("A_dt005", RA3)

    print("Running Method A-Lie (Lie on-manifold) dt=0.001 ...")
    RAL = method_A_lie(dt=0.001)
    _diag_summary("A_lie_dt001", RAL)

    print("Running Method B (decoupled Strang upwind-Burgers) dt=0.001 ...")
    RB = method_B(dt=0.001)
    _diag_summary("B_dt001", RB)

    print("Running Method C (decoupled Lie upwind-Burgers) dt=0.001 ...")
    RC = method_C(dt=0.001)
    _diag_summary("C_dt001", RC)

    print("Running Method D (fully coupled RK4 on (u,N,phi)) dt=0.0005 ...")
    RD = method_D(dt=0.0005)
    _diag_summary("D_dt0005", RD)

    out = {}
    for tag, R in (
        ("A_dt001", RA),
        ("A_dt0005", RA2),
        ("A_dt005", RA3),
        ("A_lie_dt001", RAL),
        ("B_dt001", RB),
        ("C_dt001", RC),
        ("D_dt0005", RD),
    ):
        out[f"{tag}_t"] = R["t"]
        out[f"{tag}_u"] = R["u"]
        out[f"{tag}_N"] = R["N"]
        out[f"{tag}_phi"] = R["phi"]
        out[f"{tag}_m_norm"] = R["m_norm"]
        out[f"{tag}_mass"] = R["mass"]
        out[f"{tag}_energy"] = R["energy"]
        out[f"{tag}_peak_x"] = R["peak_x"]
    out["x"] = x
    np.savez("pred_results/S5.npz", **out)
    print("Saved pred_results/S5.npz")
