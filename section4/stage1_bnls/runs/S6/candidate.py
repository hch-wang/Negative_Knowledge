"""S6: B-NLS off Mcs -- relaxation from u perturbation.

The Madelung-Psi formulation: we evolve state (Psi, m) where
  Psi = sqrt(N) * exp(i*phi)     (complex, well-defined including vacuum)
  m   = u - N*phi_x = u - j      (j := Im(conj(Psi)*Psi_x) = N*phi_x)
We never divide by N, since u is reconstructed as u = m + j.

We adopt the standard-NLS sign convention for Psi:
  i*Psi_t = -(1/2)*Psi_xx - 2*kappa*|Psi|^2*Psi - i*u*Psi_x - (i/2)*u_x*Psi

With kappa=+1 this is focusing NLS with advection, for which the sech^2 soliton
N = 2*sech^2(sqrt(2)*(x+5)) is the bright soliton ground state (in the unbosted
frame). NOTE: This Madelung corresponds to the quantum-pressure sign convention
that makes Psi a wave function on which a 1/sqrt(N) singularity does not arise
(as is standard).

Equations:
  Psi_t = (i/2)*Psi_xx + 2i*kappa*|Psi|^2*Psi - u*Psi_x - (1/2)*u_x*Psi
  m_t   = -u*m_x - 2*m*u_x   (the EPDiff momentum equation, unchanged)
  u     = m + j              (algebraic reconstruction; no division by N)

Implementation:
  Two substantively different methods, both on the (Psi, m) state.

  M1 = "Strang"  -- Strang-split Madelung-Psi (the recommended S5 method):
      kinetic(dt/2) -- nonlinear(dt/2) -- advection-and-m(dt) -- nonlinear(dt/2) -- kinetic(dt/2).
      Kinetic and nonlinear pieces are integrated exactly (FFT and pointwise
      exponential), so the only time-stepping error comes from the advection
      step which uses RK4 sub-steps. This is highly stable for the NLS
      sector (no kinetic CFL restriction).

  M2 = "RK4"     -- direct explicit RK4 on (Psi, m) without splitting.

Three experiments:
  E1: Strang, eps=0.05, dt=0.01
  E2: Strang, eps=0.20, dt=0.01  (epsilon scan)
  E3: RK4,    eps=0.05, dt=0.001 (cross-validation with smaller dt)
"""

import numpy as np
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "pred_results"
OUT.mkdir(parents=True, exist_ok=True)

L = 30.0
xL, xR = -15.0, 15.0
Nx_default = 256
T_final_default = 12.0
kappa = 1.0


def make_grid(Nx):
    x = np.linspace(xL, xR, Nx, endpoint=False)
    dx = L / Nx
    k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
    return x, dx, k


def initial_condition(x, epsilon):
    """Returns (Psi, m) with Psi=sqrt(N)*exp(i*phi), m = u - N*phi_x."""
    N0 = 2.0 * (1.0 / np.cosh(np.sqrt(2.0) * (x + 5.0))) ** 2
    phi0 = 0.25 * x  # boost: phi_x = 0.25 everywhere
    u0 = 0.25 * N0 + epsilon * np.cos(2.0 * np.pi * x / 30.0)
    m0 = u0 - 0.25 * N0  # = epsilon*cos(2*pi*x/30)
    Psi0 = np.sqrt(N0) * np.exp(1j * phi0)
    return Psi0.astype(complex), m0.astype(float)


def make_dealias_mask(k, frac=2.0 / 3.0):
    kmax = np.max(np.abs(k))
    return (np.abs(k) < frac * kmax).astype(float)


def dxc(f, k):
    return np.fft.ifft(1j * k * np.fft.fft(f))


def dxr(f, k):
    return np.real(np.fft.ifft(1j * k * np.fft.fft(f)))


def dxxc(f, k):
    return np.fft.ifft(-(k**2) * np.fft.fft(f))


def dealias_field(f, mask):
    if np.iscomplexobj(f):
        return np.fft.ifft(np.fft.fft(f) * mask)
    return np.real(np.fft.ifft(np.fft.fft(f) * mask))


def compute_u(Psi, m, k):
    Psi_x = dxc(Psi, k)
    j = np.imag(np.conj(Psi) * Psi_x)
    u = m + j
    return u, j, Psi_x


# -----------------------------------------------------------------------------
# Method M1: Strang split (S5 method)
# -----------------------------------------------------------------------------
def kinetic_half(Psi, dt, k):
    """Solve i*Psi_t = -(1/2)*Psi_xx exactly. Solution: Psi_hat *= exp(-(i/2)*k^2*dt)."""
    return np.fft.ifft(np.exp(-0.5j * (k**2) * dt) * np.fft.fft(Psi))


def nonlinear_half(Psi, dt, kappa):
    """Solve i*Psi_t = -2*kappa*|Psi|^2*Psi -> Psi *= exp(2i*kappa*|Psi|^2*dt). |Psi|^2 conserved."""
    return Psi * np.exp(2j * kappa * (np.abs(Psi) ** 2) * dt)


def advection_step_rk4(Psi, m, dt, k, dealias_mask, n_sub=4):
    """Advection of Psi by u and evolution of m, both via RK4 sub-steps.
       Psi_t-advect = -u*Psi_x - (1/2)*u_x*Psi
       m_t          = -u*m_x - 2*m*u_x
    """
    sub_dt = dt / n_sub

    def adv_rhs(Psi_, m_):
        u, j, Psi_x = compute_u(Psi_, m_, k)
        u_x = dxr(u, k)
        m_x = dxr(m_, k)
        adv = u * Psi_x + 0.5 * u_x * Psi_
        adv = dealias_field(adv, dealias_mask)
        dPsi = -adv
        prod1 = dealias_field(u * m_x, dealias_mask)
        prod2 = dealias_field(m_ * u_x, dealias_mask)
        dm = -prod1 - 2.0 * prod2
        return dPsi, dm

    for _ in range(n_sub):
        k1p, k1m = adv_rhs(Psi, m)
        k2p, k2m = adv_rhs(Psi + 0.5 * sub_dt * k1p, m + 0.5 * sub_dt * k1m)
        k3p, k3m = adv_rhs(Psi + 0.5 * sub_dt * k2p, m + 0.5 * sub_dt * k2m)
        k4p, k4m = adv_rhs(Psi + sub_dt * k3p, m + sub_dt * k3m)
        Psi = Psi + (sub_dt / 6.0) * (k1p + 2 * k2p + 2 * k3p + k4p)
        m = m + (sub_dt / 6.0) * (k1m + 2 * k2m + 2 * k3m + k4m)
        Psi = dealias_field(Psi, dealias_mask)
        m = dealias_field(m, dealias_mask)
    return Psi, m


def strang_step(Psi, m, dt, k, kappa, dealias_mask):
    Psi = kinetic_half(Psi, dt / 2.0, k)
    Psi = nonlinear_half(Psi, dt / 2.0, kappa)
    Psi, m = advection_step_rk4(Psi, m, dt, k, dealias_mask)
    Psi = nonlinear_half(Psi, dt / 2.0, kappa)
    Psi = kinetic_half(Psi, dt / 2.0, k)
    return Psi, m


# -----------------------------------------------------------------------------
# Method M2: Direct RK4 on (Psi, m)
# -----------------------------------------------------------------------------
def rhs_direct(Psi, m, k, kappa, dealias_mask):
    u, j, Psi_x = compute_u(Psi, m, k)
    Psi_xx = dxxc(Psi, k)
    u_x = dxr(u, k)
    m_x = dxr(m, k)

    nlin = 2j * kappa * (np.abs(Psi) ** 2) * Psi
    nlin = dealias_field(nlin, dealias_mask)
    adv = u * Psi_x + 0.5 * u_x * Psi
    adv = dealias_field(adv, dealias_mask)
    Psi_t = 0.5j * Psi_xx + nlin - adv  # note: +i/2*Psi_xx since i*Psi_t = -(1/2)*Psi_xx -> Psi_t = +(i/2)*Psi_xx

    prod1 = dealias_field(u * m_x, dealias_mask)
    prod2 = dealias_field(m * u_x, dealias_mask)
    m_t = -prod1 - 2.0 * prod2

    return Psi_t, m_t


def rk4_step(Psi, m, dt, k, kappa, dealias_mask):
    k1p, k1m = rhs_direct(Psi, m, k, kappa, dealias_mask)
    k2p, k2m = rhs_direct(Psi + 0.5 * dt * k1p, m + 0.5 * dt * k1m, k, kappa, dealias_mask)
    k3p, k3m = rhs_direct(Psi + 0.5 * dt * k2p, m + 0.5 * dt * k2m, k, kappa, dealias_mask)
    k4p, k4m = rhs_direct(Psi + dt * k3p, m + dt * k3m, k, kappa, dealias_mask)
    Psi_new = Psi + (dt / 6.0) * (k1p + 2 * k2p + 2 * k3p + k4p)
    m_new = m + (dt / 6.0) * (k1m + 2 * k2m + 2 * k3m + k4m)
    Psi_new = dealias_field(Psi_new, dealias_mask)
    m_new = dealias_field(m_new, dealias_mask)
    return Psi_new, m_new


# -----------------------------------------------------------------------------
# Diagnostics
# -----------------------------------------------------------------------------
def diagnostics(Psi, m, k, dx):
    u, j, Psi_x = compute_u(Psi, m, k)
    N = np.abs(Psi) ** 2
    mass = float(np.sum(N) * dx)
    p_nls = float(np.sum(j) * dx)
    p_u = float(np.sum(u) * dx)
    m_norm = float(np.sqrt(np.sum(m**2) * dx))
    # Standard NLS energy: H = (1/2)*∫|Psi_x|^2 - kappa*∫|Psi|^4 dx
    e_kin = float(0.5 * np.sum(np.abs(Psi_x) ** 2) * dx)
    e_nl = float(-kappa * np.sum(N**2) * dx)
    energy_nls = e_kin + e_nl
    return dict(
        mass=mass,
        p_nls=p_nls,
        p_u=p_u,
        m_norm=m_norm,
        energy=float(energy_nls),
        e_kin=e_kin,
        e_nl=e_nl,
        min_N=float(N.min()),
        max_absu=float(np.abs(u).max()),
        max_absPsi=float(np.abs(Psi).max()),
        max_absm=float(np.abs(m).max()),
    )


# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
def run_simulation(method, epsilon, dt, T_final, Nx, save_every=100, verbose=True):
    x, dx, k = make_grid(Nx)
    dealias_mask = make_dealias_mask(k)
    Psi, m = initial_condition(x, epsilon)
    Psi = dealias_field(Psi, dealias_mask)
    m = dealias_field(m, dealias_mask)

    n_steps = int(np.round(T_final / dt))
    times = []
    diag_list = []
    m_norm_traj = []

    d0 = diagnostics(Psi, m, k, dx)
    times.append(0.0)
    diag_list.append(d0)
    m_norm_traj.append(d0["m_norm"])
    if verbose:
        print(f"[{method} eps={epsilon} dt={dt}] t=0.000  ||m||={d0['m_norm']:.6e}  mass={d0['mass']:.6e}  energy={d0['energy']:.6e}  max|u|={d0['max_absu']:.3e}  max|Psi|={d0['max_absPsi']:.3e}")
    print_every = max(1, n_steps // 24)

    for step in range(1, n_steps + 1):
        if method == "Strang":
            Psi, m = strang_step(Psi, m, dt, k, kappa, dealias_mask)
        elif method == "RK4":
            Psi, m = rk4_step(Psi, m, dt, k, kappa, dealias_mask)
        else:
            raise ValueError(method)

        t = step * dt
        if step % save_every == 0 or step == n_steps:
            d = diagnostics(Psi, m, k, dx)
            times.append(t)
            diag_list.append(d)
            m_norm_traj.append(d["m_norm"])
            if not np.isfinite(d["m_norm"]) or d["max_absu"] > 100:
                print(f"!!! Instability at t={t}: m_norm={d['m_norm']} max_u={d['max_absu']}")
                return None
            if verbose and step % print_every == 0:
                print(f"[{method} eps={epsilon} dt={dt}] t={t:.3f}  ||m||={d['m_norm']:.6e}  mass={d['mass']:.6e}  energy={d['energy']:.6e}  max|u|={d['max_absu']:.3e}  max|Psi|={d['max_absPsi']:.3e}")

    u_final, j_final, _ = compute_u(Psi, m, k)
    N_final = np.abs(Psi) ** 2

    times_arr = np.array(times)
    m_norm_arr = np.array(m_norm_traj)
    mass_arr = np.array([d["mass"] for d in diag_list])
    energy_arr = np.array([d["energy"] for d in diag_list])
    minN_arr = np.array([d["min_N"] for d in diag_list])
    p_nls_arr = np.array([d["p_nls"] for d in diag_list])
    p_u_arr = np.array([d["p_u"] for d in diag_list])
    max_u_arr = np.array([d["max_absu"] for d in diag_list])

    return dict(
        x=x,
        times=times_arr,
        m_norm=m_norm_arr,
        mass=mass_arr,
        energy=energy_arr,
        min_N=minN_arr,
        p_nls=p_nls_arr,
        p_u=p_u_arr,
        max_u=max_u_arr,
        Psi_final=Psi,
        u_final=u_final,
        N_final=N_final,
        m_final=m,
        epsilon=epsilon,
        method=method,
        dt=dt,
    )


# -----------------------------------------------------------------------------
# Fits
# -----------------------------------------------------------------------------
def fit_exponential(t, y, t_start=None, t_end=None):
    if t_start is None:
        t_start = 0.1 * t[-1]
    if t_end is None:
        t_end = t[-1]
    mask = (t >= t_start) & (t <= t_end) & (y > 0) & np.isfinite(y)
    if mask.sum() < 5:
        return None
    p = np.polyfit(t[mask], np.log(y[mask]), 1)
    slope, intercept = p
    tau = -1.0 / slope if slope < 0 else np.inf
    A = float(np.exp(intercept))
    log_y = np.log(y[mask])
    log_yhat = intercept + slope * t[mask]
    ss_res = np.sum((log_y - log_yhat) ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return dict(tau=float(tau), A=float(A), r2_log=float(r2), slope=float(slope), t_start=float(t_start), t_end=float(t_end))


def fit_power_law(t, y, t_start=0.5, t_end=None):
    if t_end is None:
        t_end = t[-1]
    mask = (t >= t_start) & (t <= t_end) & (y > 0) & np.isfinite(t) & np.isfinite(y)
    if mask.sum() < 5:
        return None
    p = np.polyfit(np.log(t[mask]), np.log(y[mask]), 1)
    slope, intercept = p
    alpha = -slope
    A = float(np.exp(intercept))
    log_yhat = intercept + slope * np.log(t[mask])
    ss_res = np.sum((np.log(y[mask]) - log_yhat) ** 2)
    ss_tot = np.sum((np.log(y[mask]) - np.mean(np.log(y[mask]))) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return dict(alpha=float(alpha), A=float(A), r2_log=float(r2), t_start=float(t_start), t_end=float(t_end))


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    runs = {}

    print("\n=== E1: Strang-split Madelung-Psi, eps=0.05, dt=0.005, T=12 ===")
    r1 = run_simulation("Strang", epsilon=0.05, dt=0.005, T_final=T_final_default, Nx=Nx_default, save_every=20)
    if r1 is not None:
        r1["fit_exponential"] = fit_exponential(r1["times"], r1["m_norm"])
        r1["fit_power_law"] = fit_power_law(r1["times"], r1["m_norm"])
        runs["E1_Strang_eps0p05"] = r1
        print(f"E1 fit_exp: {r1['fit_exponential']}")
        print(f"E1 fit_pow: {r1['fit_power_law']}")

    print("\n=== E2: Strang-split Madelung-Psi, eps=0.20, dt=0.005, T=12 ===")
    r2 = run_simulation("Strang", epsilon=0.20, dt=0.005, T_final=T_final_default, Nx=Nx_default, save_every=20)
    if r2 is not None:
        r2["fit_exponential"] = fit_exponential(r2["times"], r2["m_norm"])
        r2["fit_power_law"] = fit_power_law(r2["times"], r2["m_norm"])
        runs["E2_Strang_eps0p20"] = r2
        print(f"E2 fit_exp: {r2['fit_exponential']}")
        print(f"E2 fit_pow: {r2['fit_power_law']}")

    print("\n=== E3: Strang-split Madelung-Psi, eps=0.05, dt=0.0025, T=12 (timestep refinement) ===")
    r3 = run_simulation("Strang", epsilon=0.05, dt=0.0025, T_final=T_final_default, Nx=Nx_default, save_every=40)
    if r3 is not None:
        r3["fit_exponential"] = fit_exponential(r3["times"], r3["m_norm"])
        r3["fit_power_law"] = fit_power_law(r3["times"], r3["m_norm"])
        runs["E3_Strang_eps0p05_fine"] = r3
        print(f"E3 fit_exp: {r3['fit_exponential']}")
        print(f"E3 fit_pow: {r3['fit_power_law']}")

    save_dict = {}
    for tag, r in runs.items():
        if r is None:
            continue
        save_dict[f"{tag}_times"] = r["times"]
        save_dict[f"{tag}_m_norm"] = r["m_norm"]
        save_dict[f"{tag}_mass"] = r["mass"]
        save_dict[f"{tag}_energy"] = r["energy"]
        save_dict[f"{tag}_min_N"] = r["min_N"]
        save_dict[f"{tag}_p_nls"] = r["p_nls"]
        save_dict[f"{tag}_p_u"] = r["p_u"]
        save_dict[f"{tag}_max_u"] = r["max_u"]
        save_dict[f"{tag}_x"] = r["x"]
        save_dict[f"{tag}_Psi_final_re"] = np.real(r["Psi_final"])
        save_dict[f"{tag}_Psi_final_im"] = np.imag(r["Psi_final"])
        save_dict[f"{tag}_u_final"] = r["u_final"]
        save_dict[f"{tag}_N_final"] = r["N_final"]
        save_dict[f"{tag}_m_final"] = r["m_final"]
        save_dict[f"{tag}_epsilon"] = np.array(r["epsilon"])
        save_dict[f"{tag}_dt"] = np.array(r["dt"])

    np.savez(OUT / "S6.npz", **save_dict)
    print(f"\nSaved {OUT / 'S6.npz'}")

    print("\n=== Fit summary ===")
    for tag, r in runs.items():
        if r is None:
            continue
        fe = r["fit_exponential"]
        fp = r["fit_power_law"]
        if fe is None or fp is None:
            print(f"{tag}: fit failed")
            continue
        print(f"{tag}: tau={fe['tau']:.3f} r2_exp={fe['r2_log']:.3f}; alpha={fp['alpha']:.3f} r2_pow={fp['r2_log']:.3f}")

    fits_summary = {
        tag: {
            "fit_exponential": r["fit_exponential"],
            "fit_power_law": r["fit_power_law"],
            "epsilon": r["epsilon"],
            "method": r["method"],
            "dt": r["dt"],
            "mass_initial": float(r["mass"][0]),
            "mass_final": float(r["mass"][-1]),
            "mass_drift_relative": float((r["mass"][-1] - r["mass"][0]) / r["mass"][0]),
            "energy_initial": float(r["energy"][0]),
            "energy_final": float(r["energy"][-1]),
            "energy_drift_relative": float((r["energy"][-1] - r["energy"][0]) / abs(r["energy"][0])),
            "m_norm_initial": float(r["m_norm"][0]),
            "m_norm_final": float(r["m_norm"][-1]),
            "m_norm_decay_ratio": float(r["m_norm"][-1] / r["m_norm"][0]),
            "max_u_max": float(r["max_u"].max()),
        }
        for tag, r in runs.items() if r is not None
    }
    with open(OUT / "S6_fits.json", "w") as f:
        json.dump(fits_summary, f, indent=2)
    print(f"Saved {OUT / 'S6_fits.json'}")
