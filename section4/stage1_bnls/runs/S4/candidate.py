"""S4: NLS defocusing dark soliton — stress test for N=0 singularity handling.

Compares three substantively different methods:

  M1  Madelung-Psi split-step Fourier on Psi (kappa=-1, defocusing).
      i*Psi_t = -1/2 Psi_xx + kappa*|Psi|^2 Psi.  IC: Psi(x,0) = tanh(x).
      Operates on Psi directly so N=0 at x=0 is harmless (Psi is smooth).
      Phase singularity at x=0 (true pi-jump) is encoded as Psi changing sign.

  M2  Direct (N, phi) split-step Fourier with floor-regularization
      N <- max(N, eps).  Evolves the Madelung pair via
          N_t  = -(N*v)_x,           v := phi_x
          phi_t = -1/2 v^2 - Q(N) + kappa*N - mu0   with mu0 the asymptotic
          quantum-pressure free chemical potential.
      Quantum pressure  Q(N) := -(sqrt(N))_xx / (2 sqrt(N))  blows up at N=0,
      hence the eps floor.  Tested at eps in {1e-6, 1e-4, 1e-2}.

  M3  Strang-split Crank-Nicolson on Psi (cross-check higher-order in time
      reference for M1).  Same equation as M1, second-order in time, allows
      large dt and serves as ground truth for the conserved density.

  M4  Madelung-Psi split-step using ANTI-PERIODIC Fourier basis.  The dark
      soliton Psi=tanh(x) satisfies Psi(-L)=-Psi(L), NOT Psi(-L)=Psi(L), so the
      naive periodic Fourier basis introduces a Gibbs jump of 2 at x=±L which
      corrupts the dynamics.  M4 uses the shifted wavenumbers k_n=(2n+1)*pi/(2L)
      to enforce the correct boundary condition.  This is THE periodic-vs-
      Dirichlet finding the prompt's stress question asks about.

Outputs:
  pred_results/S4.npz with arrays for each method at T=4.0.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

# -----------------------------------------------------------------------------
# Problem set-up
# -----------------------------------------------------------------------------
HERE = Path(__file__).parent
PRED = HERE / "pred_results"
PRED.mkdir(exist_ok=True)

L = 15.0           # half-domain
Nx = 256
T_final = 4.0
kappa = -1.0       # defocusing
x = np.linspace(-L, L, Nx, endpoint=False)
dx = x[1] - x[0]
k = 2 * np.pi * np.fft.fftfreq(Nx, d=dx)
k2 = k ** 2

# IC: dark soliton.  On [-15,15], tanh(±15) ≈ ±1 to ~1e-13 so periodic is fine.
Psi0 = np.tanh(x).astype(np.complex128)

# For the defocusing NLS with boundary density 1, the stationary dark soliton
# satisfies i Psi_t = -1/2 Psi_xx + kappa |Psi|^2 Psi - mu0 Psi  with mu0 = kappa.
# Here we use the equation WITHOUT the chemical-potential shift, so |Psi|^2 is
# stationary but the global phase rotates uniformly by exp(-i*kappa*t).
mu0 = kappa   # = -1.  Density profile is preserved, global phase rotates.


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def density_phase(Psi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return np.abs(Psi) ** 2, np.angle(Psi)


def mass(Psi: np.ndarray) -> float:
    # On a finite periodic domain with dark soliton, mass diverges with L; we
    # report the deviation from the IC mass as the conservation diagnostic.
    return float(np.sum(np.abs(Psi) ** 2) * dx)


def energy_psi(Psi: np.ndarray) -> float:
    # E = ∫ [ 1/2 |Psi_x|^2 + kappa/2 |Psi|^4 ] dx
    Psix = np.fft.ifft(1j * k * np.fft.fft(Psi))
    kin = 0.5 * np.sum(np.abs(Psix) ** 2) * dx
    interaction = 0.5 * kappa * np.sum(np.abs(Psi) ** 4) * dx
    return float(np.real(kin + interaction))


# -----------------------------------------------------------------------------
# M1: Madelung-Psi split-step Fourier on Psi
# -----------------------------------------------------------------------------
def run_M1(dt: float = 1e-3, T: float = T_final) -> dict:
    Psi = Psi0.copy()
    Nt = int(round(T / dt))
    dt_eff = T / Nt
    # Strang splitting: half-step in nonlinear V, full kinetic, half nonlinear.
    # We solve i Psi_t = -1/2 Psi_xx + kappa (|Psi|^2 - n_inf) Psi where
    # n_inf=1 is the asymptotic density.  This is the dark-soliton frame:
    # tanh(x) is a TRUE stationary solution -- density and phase profile
    # preserved exactly.
    n_inf = 1.0
    kin_prop = np.exp(-1j * 0.5 * k2 * dt_eff)
    min_N = np.inf
    mass_hist = [mass(Psi)]
    for n in range(Nt):
        # half-step nonlinear
        V = kappa * (np.abs(Psi) ** 2 - n_inf)
        Psi *= np.exp(-1j * V * 0.5 * dt_eff)
        # full kinetic
        Psi = np.fft.ifft(kin_prop * np.fft.fft(Psi))
        # half-step nonlinear
        V = kappa * (np.abs(Psi) ** 2 - n_inf)
        Psi *= np.exp(-1j * V * 0.5 * dt_eff)
        n_now = float(np.min(np.abs(Psi) ** 2))
        if n_now < min_N:
            min_N = n_now
        if n % max(1, Nt // 8) == 0:
            mass_hist.append(mass(Psi))
    mass_hist.append(mass(Psi))
    rho, ph = density_phase(Psi)

    # Phase jump diagnostic: across x=0 the dark soliton has a pi jump.
    # Find indices straddling x=0.
    i0 = int(np.argmin(np.abs(x)))           # closest sample
    # Use the two samples bracketing 0.
    iL = i0 - 1
    iR = i0 + 1
    phase_jump = float(np.angle(np.exp(1j * (ph[iR] - ph[iL]))))
    # Density at the centre
    rho_at_zero = float(rho[i0])

    # Compare density to exact (stationary)
    rho_exact = np.tanh(x) ** 2
    density_L2err = float(np.sqrt(np.sum((rho - rho_exact) ** 2) * dx))
    density_Linf = float(np.max(np.abs(rho - rho_exact)))

    return dict(
        Psi=Psi,
        rho=rho,
        phase=ph,
        min_N=min_N,
        mass_init=mass_hist[0],
        mass_final=mass_hist[-1],
        mass_drift=abs(mass_hist[-1] - mass_hist[0]),
        phase_jump=phase_jump,
        rho_at_zero=rho_at_zero,
        density_L2err=density_L2err,
        density_Linf=density_Linf,
        energy=energy_psi(Psi),
        dt=dt_eff,
    )


# -----------------------------------------------------------------------------
# M2: Direct (N, phi) split-step with regularization
# -----------------------------------------------------------------------------
def quantum_pressure(N: np.ndarray, eps: float) -> np.ndarray:
    """Q(N) = -(sqrt(N))_xx / (2 sqrt(N)).  Uses N -> max(N, eps) for stability."""
    Nr = np.maximum(N, eps)
    s = np.sqrt(Nr)
    sxx = np.fft.ifft(-(k2) * np.fft.fft(s)).real
    return -sxx / (2.0 * s)


def run_M2(dt: float, eps: float, T: float = T_final) -> dict:
    # IC from Psi0
    rho = np.abs(Psi0) ** 2          # tanh^2(x)
    # Phase is 0 for x>0, pi for x<0 (since Psi=tanh(x) is real, sign change).
    phi = np.where(x >= 0.0, 0.0, np.pi).astype(np.float64)
    N = rho.copy()
    # Simple first-order operator splitting for the (N, phi) system.
    # N_t  = -(N v)_x,  v = phi_x
    # phi_t = -1/2 v^2 - Q(N) + kappa N - mu0     (with mu0 = kappa)
    Nt = int(round(T / dt))
    dt_eff = T / Nt
    min_N_seen = float(np.min(N))
    max_grad_phi = 0.0
    blew_up = False
    nan_step = -1
    mass0 = float(np.sum(N) * dx)
    n_inf = 1.0  # dark-soliton frame: subtract asymptotic density
    for n in range(Nt):
        v = np.fft.ifft(1j * k * np.fft.fft(phi)).real
        # Update N: dN/dt = -(N v)_x
        flux = N * v
        dN_dx_flux = np.fft.ifft(1j * k * np.fft.fft(flux)).real
        N = N - dt_eff * dN_dx_flux
        N_reg = np.maximum(N, eps)
        # Update phi (dark-soliton frame, no mu0 needed since absorbed)
        Q = quantum_pressure(N_reg, eps)
        dphi = -0.5 * v ** 2 - Q + kappa * (N_reg - n_inf)
        phi = phi + dt_eff * dphi
        # Diagnostics
        mn = float(np.min(N))
        if mn < min_N_seen:
            min_N_seen = mn
        if not (np.all(np.isfinite(N)) and np.all(np.isfinite(phi))):
            blew_up = True
            nan_step = n
            break
        gmax = float(np.max(np.abs(v)))
        if gmax > max_grad_phi:
            max_grad_phi = gmax
        if max_grad_phi > 1e8:
            blew_up = True
            nan_step = n
            break

    mass_final = float(np.sum(N) * dx) if not blew_up else float("nan")
    # rebuild Psi for output
    Psi_out = np.sqrt(np.maximum(N, 0.0)) * np.exp(1j * phi)
    rho_exact = np.tanh(x) ** 2
    if blew_up:
        density_L2err = float("nan")
        density_Linf = float("nan")
        phase_jump = float("nan")
    else:
        density_L2err = float(np.sqrt(np.sum((N - rho_exact) ** 2) * dx))
        density_Linf = float(np.max(np.abs(N - rho_exact)))
        i0 = int(np.argmin(np.abs(x)))
        iL = i0 - 1
        iR = i0 + 1
        phase_jump = float(np.angle(np.exp(1j * (phi[iR] - phi[iL]))))
    return dict(
        N=N,
        phi=phi,
        Psi=Psi_out,
        eps=eps,
        dt=dt_eff,
        blew_up=blew_up,
        nan_step=nan_step,
        T_reached=(nan_step if blew_up else Nt) * dt_eff,
        min_N=min_N_seen,
        max_grad_phi=max_grad_phi,
        mass_init=mass0,
        mass_final=mass_final,
        mass_drift=abs(mass_final - mass0) if not blew_up else float("nan"),
        density_L2err=density_L2err,
        density_Linf=density_Linf,
        phase_jump=phase_jump,
    )


# -----------------------------------------------------------------------------
# M4: Madelung-Psi split-step with ANTI-PERIODIC Fourier basis
# -----------------------------------------------------------------------------
# The dark soliton Psi=tanh(x) satisfies Psi(-L) = -Psi(L) on [-L, L].  This is
# anti-periodic, NOT periodic.  Standard periodic Fourier introduces a jump of
# size 2 at the boundary, which corrupts the dynamics through Gibbs ringing.
# The fix: use anti-periodic Fourier basis exp(i k_n x) with k_n = (2n+1)pi/(2L).
# We implement this via the "half-shift" trick: U(x) := exp(-i pi x / (2L)) Psi(x)
# is periodic when Psi is anti-periodic; we evolve U with standard periodic FFT
# and convert back to Psi for diagnostics.
def run_M4(dt: float = 1e-3, T: float = T_final) -> dict:
    """Anti-periodic Fourier split-step on Psi.  Proper BC for dark soliton."""
    # Anti-periodic shift factor
    shift = np.exp(-1j * np.pi * x / (2.0 * L))
    # In terms of U, the operator -1/2 d^2/dx^2 has Fourier symbol
    # 1/2 (k + pi/(2L))^2 on U-modes (k = 2 pi n / (2L) = standard).
    k_shifted = k + np.pi / (2.0 * L)
    k2_shifted = k_shifted ** 2

    Psi = Psi0.copy()
    U = shift * Psi
    Nt = int(round(T / dt))
    dt_eff = T / Nt
    n_inf = 1.0
    kin_prop = np.exp(-1j * 0.5 * k2_shifted * dt_eff)
    min_N = np.inf
    mass_init = mass(Psi)
    for n in range(Nt):
        # convert U -> Psi for nonlinear (which acts pointwise; |Psi|=|U|)
        # half-step nonlinear: V = kappa (|Psi|^2 - n_inf), acts on Psi
        # |Psi|^2 = |U|^2 so we can use U here directly.
        V = kappa * (np.abs(U) ** 2 - n_inf)
        U *= np.exp(-1j * V * 0.5 * dt_eff)
        # full kinetic on U via shifted-k Fourier
        U = np.fft.ifft(kin_prop * np.fft.fft(U))
        # half-step nonlinear
        V = kappa * (np.abs(U) ** 2 - n_inf)
        U *= np.exp(-1j * V * 0.5 * dt_eff)
        n_now = float(np.min(np.abs(U) ** 2))
        if n_now < min_N:
            min_N = n_now
    # recover Psi
    Psi = U / shift
    rho, ph = density_phase(Psi)
    rho_exact = np.tanh(x) ** 2
    density_L2err = float(np.sqrt(np.sum((rho - rho_exact) ** 2) * dx))
    density_Linf = float(np.max(np.abs(rho - rho_exact)))
    mass_final = mass(Psi)
    i0 = int(np.argmin(np.abs(x)))
    phase_jump = float(np.angle(np.exp(1j * (ph[i0 + 1] - ph[i0 - 1]))))
    # Phase rotation rate at the boundary should be ~ kappa * n_inf = -1 in
    # the dark-soliton frame this is removed, so phase stays near 0/pi.
    return dict(
        Psi=Psi,
        rho=rho,
        phase=ph,
        dt=dt_eff,
        min_N=min_N,
        density_L2err=density_L2err,
        density_Linf=density_Linf,
        mass_init=mass_init,
        mass_final=mass_final,
        mass_drift=abs(mass_final - mass_init),
        phase_jump=phase_jump,
        rho_at_zero=float(rho[i0]),
        energy=energy_psi(Psi),
    )


# -----------------------------------------------------------------------------
# M3: Strang-split Crank-Nicolson on Psi (reference cross-check)
# -----------------------------------------------------------------------------
def run_M3(dt: float = 5e-3, T: float = T_final) -> dict:
    """Same equation as M1 but using a CN-style implicit linear half-step
    combined with explicit nonlinear half-step.  Provides a second numerical
    scheme on Psi to confirm M1 is right.
    """
    Psi = Psi0.copy()
    Nt = int(round(T / dt))
    dt_eff = T / Nt
    # Same dark-soliton frame as M1: kappa (|Psi|^2 - n_inf)
    n_inf = 1.0
    # CN propagator for linear part: (1 + i dt/2 (k^2/2)) Psi^{n+1} = (1 - i dt/2 (k^2/2)) Psi^n
    a = 1j * dt_eff * 0.25 * k2  # corresponds to dt/2 * (k^2/2)
    cn_num = (1.0 - a) / (1.0 + a)
    min_N = np.inf
    for n in range(Nt):
        # half nonlinear (exact rotation)
        V = kappa * (np.abs(Psi) ** 2 - n_inf)
        Psi *= np.exp(-1j * V * 0.5 * dt_eff)
        # CN linear (in Fourier space, the CN step is diagonal -> exact factor)
        Psi = np.fft.ifft(cn_num * np.fft.fft(Psi))
        # half nonlinear
        V = kappa * (np.abs(Psi) ** 2 - n_inf)
        Psi *= np.exp(-1j * V * 0.5 * dt_eff)
        n_now = float(np.min(np.abs(Psi) ** 2))
        if n_now < min_N:
            min_N = n_now
    rho, ph = density_phase(Psi)
    rho_exact = np.tanh(x) ** 2
    density_L2err = float(np.sqrt(np.sum((rho - rho_exact) ** 2) * dx))
    density_Linf = float(np.max(np.abs(rho - rho_exact)))
    mass_final = mass(Psi)
    mass_init = mass(Psi0)
    i0 = int(np.argmin(np.abs(x)))
    phase_jump = float(np.angle(np.exp(1j * (ph[i0 + 1] - ph[i0 - 1]))))
    return dict(
        Psi=Psi,
        rho=rho,
        phase=ph,
        dt=dt_eff,
        min_N=min_N,
        density_L2err=density_L2err,
        density_Linf=density_Linf,
        mass_init=mass_init,
        mass_final=mass_final,
        mass_drift=abs(mass_final - mass_init),
        phase_jump=phase_jump,
        energy=energy_psi(Psi),
    )


# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------
def main() -> None:
    t0 = time.time()
    print(f"[S4] grid Nx={Nx}, dx={dx:.4f}, x in [{-L},{L}], T={T_final}, kappa={kappa}")
    print(f"[S4] IC: Psi(x,0)=tanh(x), |Psi|^2 zero at x=0 -> dark soliton stress test")

    # ---- M1 ----
    print("\n[M1] Madelung-Psi split-step Fourier (dt=1e-3)")
    M1 = run_M1(dt=1e-3)
    print(f"  min_N        = {M1['min_N']:.3e}")
    print(f"  mass drift   = {M1['mass_drift']:.3e}")
    print(f"  density L2   = {M1['density_L2err']:.3e}, Linf = {M1['density_Linf']:.3e}")
    print(f"  rho(x=0)     = {M1['rho_at_zero']:.3e}")
    print(f"  phase jump   = {M1['phase_jump']:.6f} rad (expect ±pi = ±{np.pi:.4f})")

    # ---- M2 sweep ----
    M2_eps_results = {}
    for eps in (1e-6, 1e-4, 1e-2):
        # Use small dt so the failure mode is genuinely the regularization, not
        # CFL.  Time-step chosen heuristically.
        dt = 5e-4
        print(f"\n[M2] Direct (N,phi) split, eps={eps:.0e}, dt={dt}")
        res = run_M2(dt=dt, eps=eps)
        M2_eps_results[f"eps_{eps:.0e}"] = res
        if res["blew_up"]:
            print(f"  BLEW UP at step {res['nan_step']} (T_reached={res['T_reached']:.3f})")
        else:
            print(f"  min_N        = {res['min_N']:.3e}")
            print(f"  mass drift   = {res['mass_drift']:.3e}")
            print(f"  density Linf = {res['density_Linf']:.3e}")
            print(f"  phase jump   = {res['phase_jump']:.6f} rad")

    # ---- M3 ----
    print("\n[M3] Strang-split CN on Psi (dt=5e-3)")
    M3 = run_M3(dt=5e-3)
    print(f"  min_N        = {M3['min_N']:.3e}")
    print(f"  mass drift   = {M3['mass_drift']:.3e}")
    print(f"  density Linf = {M3['density_Linf']:.3e}")
    print(f"  phase jump   = {M3['phase_jump']:.6f} rad")

    # ---- M4 ----
    print("\n[M4] Anti-periodic Fourier split-step on Psi (dt=1e-3)")
    M4 = run_M4(dt=1e-3)
    print(f"  min_N        = {M4['min_N']:.3e}")
    print(f"  mass drift   = {M4['mass_drift']:.3e}")
    print(f"  density L2   = {M4['density_L2err']:.3e}, Linf = {M4['density_Linf']:.3e}")
    print(f"  rho(x=0)     = {M4['rho_at_zero']:.3e}")
    print(f"  phase jump   = {M4['phase_jump']:.6f} rad (expect ±pi)")

    # ---- save ----
    npz_kwargs = dict(
        x=x,
        Psi0=Psi0,
        rho_exact=np.tanh(x) ** 2,
        # M1
        M1_Psi=M1["Psi"],
        M1_rho=M1["rho"],
        M1_phase=M1["phase"],
        # M3
        M3_Psi=M3["Psi"],
        M3_rho=M3["rho"],
        M3_phase=M3["phase"],
        # M4
        M4_Psi=M4["Psi"],
        M4_rho=M4["rho"],
        M4_phase=M4["phase"],
    )
    for tag, res in M2_eps_results.items():
        npz_kwargs[f"M2_{tag}_N"] = res["N"]
        npz_kwargs[f"M2_{tag}_phi"] = res["phi"]
        npz_kwargs[f"M2_{tag}_Psi"] = res["Psi"]
    np.savez(PRED / "S4.npz", **npz_kwargs)
    print(f"\n[OK] wrote {PRED/'S4.npz'} ({(PRED/'S4.npz').stat().st_size} bytes)")
    print(f"[time] total {time.time() - t0:.1f}s")

    # ---- summary dict for downstream JSON writing ----
    summary = {
        "M1": {
            "dt": M1["dt"], "min_N": M1["min_N"], "mass_drift": M1["mass_drift"],
            "density_L2err": M1["density_L2err"], "density_Linf": M1["density_Linf"],
            "phase_jump": M1["phase_jump"], "rho_at_zero": M1["rho_at_zero"],
            "energy": M1["energy"],
        },
        "M2": {
            tag: {
                "dt": r["dt"], "eps": r["eps"], "blew_up": bool(r["blew_up"]),
                "T_reached": r["T_reached"], "min_N": r["min_N"],
                "max_grad_phi": r["max_grad_phi"],
                "mass_drift": r["mass_drift"], "density_Linf": r["density_Linf"],
                "phase_jump": r["phase_jump"],
            } for tag, r in M2_eps_results.items()
        },
        "M3": {
            "dt": M3["dt"], "min_N": M3["min_N"], "mass_drift": M3["mass_drift"],
            "density_Linf": M3["density_Linf"], "phase_jump": M3["phase_jump"],
            "energy": M3["energy"],
        },
        "M4": {
            "dt": M4["dt"], "min_N": M4["min_N"], "mass_drift": M4["mass_drift"],
            "density_L2err": M4["density_L2err"], "density_Linf": M4["density_Linf"],
            "rho_at_zero": M4["rho_at_zero"], "phase_jump": M4["phase_jump"],
            "energy": M4["energy"],
        },
    }
    with open(HERE / "_run_summary.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
