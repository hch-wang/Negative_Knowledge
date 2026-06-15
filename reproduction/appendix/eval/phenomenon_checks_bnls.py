"""Phenomenon-based eval for Stage 3 B-NLS sub-tasks.

No closed-form reference. Each task takes a (T_save, 3, Nx) array with channels (u, N, phi).
Returns (useful: bool, diag: dict).

Tasks:
  T_A — bright soliton stability (kappa=+1, A=1.5, on Mcs at t=0)
  T_B — Gaussian density on Mcs, focusing NLS modulational instability
  T_C — Burgers bore × NLS bright soliton, kappa=+1, off Mcs
  T_D — Compound-soliton attractor: relaxation from off-Mcs perturbation
"""
import numpy as np
import json
import sys
from scipy.signal import find_peaks


L = 30.0
NX = 256
DX = L / NX
X = -15.0 + DX * np.arange(NX)


def _load(path):
    a = np.load(path)
    return a


def _normalize_shape(a):
    if a.ndim == 2:
        return a[None, ...]
    return a


def _spectral_dx(field):
    """Return phi_x on the grid (assumes field is periodic component only)."""
    k = 2 * np.pi * np.fft.fftfreq(NX, d=DX)
    return np.real(np.fft.ifft(1j * k * np.fft.fft(field)))


def _decompose_phi(phi, c_estimate=None):
    """Recover (c, phi_periodic) such that phi = c*x + phi_periodic with phi_p periodic.
    Robust to multiple conventions: c estimated from boundary slope if not given."""
    if c_estimate is None:
        # Estimate slope from phi
        c_estimate = float((phi[-1] - phi[0]) / (X[-1] - X[0]))
    phi_p = phi - c_estimate * X
    return c_estimate, phi_p


def _m_norm(u, N, phi, c_phi_guess=None):
    """Compute ||m||_2 with m = u - N * phi_x, robust to phi non-periodic parts."""
    c, phi_p = _decompose_phi(phi, c_phi_guess)
    phi_x = c + _spectral_dx(phi_p)
    m = u - N * phi_x
    return float(np.sqrt(DX * np.sum(m * m))), c, phi_x


def _peaks(N_field, threshold, distance=8):
    pks, props = find_peaks(N_field, height=threshold, distance=distance)
    return pks, props


def check_basic(snapshots, u_max=10.0, N_max=20.0, phi_max=100.0):
    """phi can grow unboundedly with time (lab-frame phase accumulation),
    so its threshold is loose. u and N are bound by physics."""
    diag = {}
    u_all = snapshots[:, 0, :]
    N_all = snapshots[:, 1, :]
    phi_all = snapshots[:, 2, :]
    diag["all_finite"] = bool(np.isfinite(snapshots).all())
    if not diag["all_finite"]:
        diag["n_nan"] = int(np.isnan(snapshots).sum())
        return diag
    mass_v0 = float(N_all[0].sum() * DX)
    mass_vT = float(N_all[-1].sum() * DX)
    diag["mass_N0"] = mass_v0
    diag["mass_NT"] = mass_vT
    diag["mass_drift_rel"] = abs(mass_vT - mass_v0) / max(abs(mass_v0), 1e-12)
    diag["u_max_abs"] = float(np.max(np.abs(u_all)))
    diag["N_max"] = float(np.max(N_all))
    diag["N_min"] = float(np.min(N_all))
    diag["phi_max_abs"] = float(np.max(np.abs(phi_all)))
    diag["bounded"] = bool(
        diag["u_max_abs"] < u_max
        and abs(diag["N_max"]) < N_max
        and abs(diag["N_min"]) < N_max
        and diag["phi_max_abs"] < phi_max
    )
    return diag


def _padding_signature(snapshots):
    """Heuristic: how many of the late snapshots are identical to the last 'physical' one,
    indicating the agent padded the run after early failure."""
    if snapshots.shape[0] < 2:
        return 0
    diffs = []
    for i in range(snapshots.shape[0] - 1):
        d = np.max(np.abs(snapshots[i+1] - snapshots[i]))
        diffs.append(d)
    diffs = np.array(diffs)
    n_pad = int(np.sum(diffs < 1e-10))
    return n_pad


def eval_T_A(pred_path):
    """T_A — Bright soliton stability under B-NLS.
    Useful = finite, bounded, mass drift < 5%, N_peak_T >= 0.5 * 2.25 = 1.125,
    ||m||_2 / ||N*phi_x||_2 < 0.2 (compound-soliton manifold near-preserved).
    """
    a = _normalize_shape(_load(pred_path))
    if a.shape[1:] != (3, NX):
        return False, {"error": f"wrong shape {a.shape}, expected (T_save, 3, {NX}) or (3, {NX})"}
    d = check_basic(a, u_max=10.0, N_max=20.0, phi_max=100.0)
    if not d["all_finite"] or not d["bounded"]:
        d["useful"] = False
        d["reason"] = "non-finite or unbounded"
        return False, d

    N0 = a[0, 1, :]; NT = a[-1, 1, :]
    uT = a[-1, 0, :]; phiT = a[-1, 2, :]
    N0_max = float(N0.max()); NT_max = float(NT.max())
    d["N0_max"] = N0_max; d["NT_max"] = NT_max
    d["amp_ratio"] = NT_max / max(N0_max, 1e-12)

    # Mcs deviation — note: phi convention varies (some agents save wrapped phase),
    # so this metric is informational only; not used as PASS/FAIL gate for T_A.
    m_T_norm, c_phi, phi_x_T = _m_norm(uT, NT, phiT, c_phi_guess=0.5)
    nphi_norm = float(np.sqrt(DX * np.sum((NT * phi_x_T) ** 2)))
    d["m_norm_T"] = m_T_norm
    d["nphi_norm_T"] = nphi_norm
    d["m_rel_T"] = m_T_norm / max(nphi_norm, 1e-12)

    n_peaks_T = len(_peaks(NT, threshold=1.125)[0])
    d["n_peaks_T"] = n_peaks_T

    d["n_padding_steps"] = _padding_signature(a)

    # Phenomenon gate: mass-conserved + bright soliton preserved (peak + amplitude).
    # m_rel is reported but NOT gated on (phi convention is too representation-dependent
    # — agents using Madelung-Psi with stripped linear-phase reconstruct phi as
    # wrapped atan2, giving an apparently large m even though the system is exactly on Mcs).
    useful = (
        d["mass_drift_rel"] < 0.05
        and NT_max >= 1.125
        and n_peaks_T >= 1
        and d["n_padding_steps"] < a.shape[0] // 2
    )
    d["useful"] = useful
    if not useful:
        rs = []
        if d["mass_drift_rel"] >= 0.05: rs.append(f"mass drift {d['mass_drift_rel']:.2%}")
        if NT_max < 1.125: rs.append(f"NT_max {NT_max:.2f} < 1.125")
        if n_peaks_T < 1: rs.append("no peak in final N")
        if d["n_padding_steps"] >= a.shape[0] // 2: rs.append(f"padded {d['n_padding_steps']}/{a.shape[0]} snapshots")
        d["reason"] = "; ".join(rs)
    return useful, d


def eval_T_B(pred_path):
    """T_B — Gaussian on Mcs, focusing NLS MI threshold test.
    Useful = finite, bounded, mass drift < 5%, >= 2 well-separated peaks with N >= 1.0.
    """
    a = _normalize_shape(_load(pred_path))
    if a.shape[1:] != (3, NX):
        return False, {"error": f"wrong shape {a.shape}"}
    d = check_basic(a, u_max=10.0, N_max=20.0, phi_max=100.0)
    if not d["all_finite"] or not d["bounded"]:
        d["useful"] = False
        d["reason"] = "non-finite or unbounded"
        return False, d

    N0 = a[0, 1, :]; NT = a[-1, 1, :]
    d["N0_max"] = float(N0.max()); d["NT_max"] = float(NT.max())
    pks, props = _peaks(NT, threshold=1.0, distance=8)
    d["n_peaks_T"] = int(len(pks))
    if len(pks) >= 2:
        d["peak_separations"] = [int(pks[i+1] - pks[i]) for i in range(len(pks)-1)]

    d["n_padding_steps"] = _padding_signature(a)

    useful = (
        d["mass_drift_rel"] < 0.05
        and d["n_peaks_T"] >= 2
        and d["NT_max"] >= 1.0
        and d["n_padding_steps"] < a.shape[0] // 2
    )
    d["useful"] = useful
    if not useful:
        rs = []
        if d["mass_drift_rel"] >= 0.05: rs.append(f"mass drift {d['mass_drift_rel']:.2%}")
        if d["n_peaks_T"] < 2: rs.append(f"only {d['n_peaks_T']} peaks (need >= 2)")
        if d["NT_max"] < 1.0: rs.append(f"NT_max {d['NT_max']:.2f} < 1.0")
        if d["n_padding_steps"] >= a.shape[0] // 2: rs.append(f"padded {d['n_padding_steps']}/{a.shape[0]} snapshots")
        d["reason"] = "; ".join(rs)
    return useful, d


def eval_T_C(pred_path):
    """T_C — Bore × NLS soliton interaction.
    Useful = finite, bore bounded (|u_max| < 5), soliton survives (N peak >= 0.3).
    """
    a = _normalize_shape(_load(pred_path))
    if a.shape[1:] != (3, NX):
        return False, {"error": f"wrong shape {a.shape}"}
    # T_C: u and N bounded by physics (~5); phi naturally accumulates with t.
    d = check_basic(a, u_max=5.0, N_max=10.0, phi_max=100.0)
    if not d["all_finite"] or not d["bounded"]:
        d["useful"] = False
        d["reason"] = "non-finite or unbounded"
        return False, d

    uT = a[-1, 0, :]; NT = a[-1, 1, :]; phiT = a[-1, 2, :]
    d["NT_max"] = float(NT.max())
    d["uT_max"] = float(np.max(np.abs(uT)))
    pks, props = _peaks(NT, threshold=0.3, distance=8)
    d["n_peaks_T"] = int(len(pks))

    d["n_padding_steps"] = _padding_signature(a)

    # Bonus: m-norm trajectory
    try:
        m_traj = []
        for snap in a:
            m_norm, _, _ = _m_norm(snap[0], snap[1], snap[2], c_phi_guess=0.6)
            m_traj.append(m_norm)
        d["m_norm_t0"] = float(m_traj[0])
        d["m_norm_tT"] = float(m_traj[-1])
        d["m_norm_min"] = float(min(m_traj))
        d["m_relative_change"] = (m_traj[-1] - m_traj[0]) / max(m_traj[0], 1e-12)
    except Exception as e:
        d["m_traj_error"] = str(e)

    useful = (
        d["NT_max"] >= 0.3
        and d["uT_max"] < 5.0
        and d["n_peaks_T"] >= 1
        and d["n_padding_steps"] < a.shape[0] // 2
    )
    d["useful"] = useful
    if not useful:
        rs = []
        if d["NT_max"] < 0.3: rs.append(f"NT_max {d['NT_max']:.2f} < 0.3 (soliton destroyed)")
        if d["uT_max"] >= 5.0: rs.append(f"uT_max {d['uT_max']:.2f} too large (bore blew up)")
        if d["n_peaks_T"] < 1: rs.append("no peak in final N")
        if d["n_padding_steps"] >= a.shape[0] // 2: rs.append(f"padded {d['n_padding_steps']}/{a.shape[0]} snapshots")
        d["reason"] = "; ".join(rs)
    return useful, d


def eval_T_D(pred_path):
    """T_D — Mcs attractor relaxation, research-grade task.
    Useful = numerically stable (mass drift < 5%, bounded, < 50% padding).
    Plus: characterize ||m||_2(t) — report whether decay/grow/plateau.
    """
    a = _normalize_shape(_load(pred_path))
    if a.shape[1:] != (3, NX):
        return False, {"error": f"wrong shape {a.shape}"}
    # T_D research-grade: be lenient on field bounds, strict on mass and padding.
    d = check_basic(a, u_max=50.0, N_max=50.0, phi_max=500.0)
    if not d["all_finite"] or not d["bounded"]:
        d["useful"] = False
        d["reason"] = "non-finite or unbounded"
        return False, d

    d["n_padding_steps"] = _padding_signature(a)

    try:
        m_traj = []
        for snap in a:
            mn, _, _ = _m_norm(snap[0], snap[1], snap[2], c_phi_guess=0.5)
            m_traj.append(mn)
        d["m_norm_t0"] = float(m_traj[0])
        d["m_norm_tT"] = float(m_traj[-1])
        d["m_norm_max"] = float(max(m_traj))
        d["m_norm_min"] = float(min(m_traj))
        d["m_relative_change"] = (m_traj[-1] - m_traj[0]) / max(m_traj[0], 1e-12)
        if d["m_relative_change"] > 0.5:
            d["m_qualitative"] = "GROWS"
        elif d["m_relative_change"] < -0.3:
            d["m_qualitative"] = "DECAYS"
        else:
            d["m_qualitative"] = "PLATEAUS"
    except Exception as e:
        d["m_traj_error"] = str(e)
        d["m_qualitative"] = "unknown"

    useful = (
        d["mass_drift_rel"] < 0.05
        and d["bounded"]
        and d["n_padding_steps"] < a.shape[0] // 2
    )
    d["useful"] = useful
    if not useful:
        rs = []
        if d["mass_drift_rel"] >= 0.05: rs.append(f"mass drift {d['mass_drift_rel']:.2%}")
        if not d["bounded"]: rs.append("unbounded fields")
        if d["n_padding_steps"] >= a.shape[0] // 2: rs.append(f"padded {d['n_padding_steps']}/{a.shape[0]} snapshots")
        d["reason"] = "; ".join(rs)
    return useful, d


EVALS = {"T_A": eval_T_A, "T_B": eval_T_B, "T_C": eval_T_C, "T_D": eval_T_D}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: phenomenon_checks_bnls.py <task_id> <pred_npy>")
        sys.exit(2)
    task_id, pred = sys.argv[1], sys.argv[2]
    useful, diag = EVALS[task_id](pred)
    print(json.dumps({"useful": useful, "diag": diag}, indent=2, default=float))
