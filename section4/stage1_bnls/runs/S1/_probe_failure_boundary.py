"""E2 probe: find the (dt, Nx) failure boundary of Strang split-step Fourier on the
focusing NLS bright soliton (A=sqrt(2), so |Psi|^2_max ~ 2). The nonlinear
half-step phase per step is kappa*|Psi|^2*(dt/2) ~ dt; the linear half-step phase
is (1/2)*k_max^2*dt with k_max = pi/dx = pi*Nx/L. We probe where each piece
blows up the soliton structure (aliasing, mass conservation is unconditional but
shape/energy/position can degrade).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

# Import the solver pieces from candidate.py
import importlib.util

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cand", HERE / "candidate.py")
cand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cand)

print("E2 probe: Strang split-step Fourier failure boundary scan")
print(f"Ground truth: |Psi|_max = sqrt(2) = {np.sqrt(2):.10f}, "
      f"|Psi|^2_max = 2.0, mass = 2*sqrt(2) = {2*np.sqrt(2):.10f}, "
      f"peak pos at T=8: -3.0")
print()

# Sweep coarse Nx and large dt
Nx_list = [32, 64, 96, 128]
dt_list = [0.5, 0.1, 0.05, 0.02, 0.01]

rows = []
for Nx in Nx_list:
    for dt in dt_list:
        r = cand.run("strang", dt, Nx)
        row = {k: v for k, v in r.items() if k not in ("x", "Psi_final", "Psi_initial", "Psi_exact_final")}
        rows.append(row)
        # Diagnose health: mass should be exactly conserved by Strang split (norm-preserving),
        # but the shape error vs exact reveals real failure
        print(f"  Nx={Nx:3d}  dt={dt:7.4f}  finite={r['finite']:1}  "
              f"|dM|/M={r['mass_drift_rel']:.2e}  "
              f"|dE|/|E|={r['energy_drift_rel']:.2e}  "
              f"|Psi|_max={r['peak_amplitude_final']:.4f} (gt~1.4142)  "
              f"peak_pos={r['peak_position_final']:+.4f} (gt=-3.0)  "
              f"relL2={r['relL2_error_vs_exact']:.2e}")

# Mark failure threshold: relL2 > 0.1 means soliton is essentially destroyed
print()
print("Failure analysis (relL2 > 0.1 ==> soliton structure lost):")
for row in rows:
    if row["relL2_error_vs_exact"] > 0.1 or not row["finite"]:
        print(f"  Nx={row['Nx']:3d}  dt={row['dt']:.4f}  relL2={row['relL2_error_vs_exact']:.2e}  "
              f"finite={row['finite']}  ==> FAIL")

with open(HERE / "_probe_failure_boundary.json", "w") as f:
    json.dump(rows, f, indent=2)
print(f"\nWrote _probe_failure_boundary.json with {len(rows)} rows.")
