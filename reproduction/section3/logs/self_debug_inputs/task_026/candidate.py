"""
ScienceAgentBench task_026 — ligand-protein interaction fingerprints.

Generates ProLIF interaction fingerprints between a selected ligand and the
protein for the first 10 trajectory frames, then writes the results to
pred_results/ligand_fingerprint_pred.csv.

Column naming convention (from task description):
  <ligand_resname>.<ligand_resid>-<protein_resname>.<protein_resid>_<InteractionType>_frame<N>
  (ProLIF already produces multi-level column names; we flatten them and
   append the frame index.)

The output CSV has one row per (frame, interaction pair), with column Y
holding the boolean/integer fingerprint status.
"""

import os
import warnings

import MDAnalysis as mda
import prolif as plf
import pandas as pd

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "benchmark/datasets/ligand_protein")
OUT_DIR  = os.path.join(BASE_DIR, "pred_results")
os.makedirs(OUT_DIR, exist_ok=True)

TOP  = os.path.join(DATA_DIR, "top.pdb")
TRAJ = os.path.join(DATA_DIR, "traj.xtc")

# ---------------------------------------------------------------------------
# Load universe
# ---------------------------------------------------------------------------
u = mda.Universe(TOP, TRAJ)

# Identify the ligand residue name (first non-protein, non-water residue)
protein_sel = u.select_atoms("protein")
all_residues = u.atoms.residues
protein_resnames = set(protein_sel.residues.resnames)

water_resnames = {"WAT", "HOH", "TIP3", "SOL", "TIP", "SPC"}

ligand_resname = None
for res in all_residues:
    if res.resname not in protein_resnames and res.resname not in water_resnames:
        ligand_resname = res.resname
        break

if ligand_resname is None:
    raise RuntimeError("Could not identify a ligand residue in the topology.")

print(f"Detected ligand residue name: {ligand_resname}")

# ---------------------------------------------------------------------------
# Select atoms
# ---------------------------------------------------------------------------
ligand  = u.select_atoms(f"resname {ligand_resname}")
protein = u.select_atoms("protein")

# ---------------------------------------------------------------------------
# Run ProLIF fingerprint for the first 10 frames
# ---------------------------------------------------------------------------
fp = plf.Fingerprint()

# Collect frames 0-9
frame_indices = list(range(10))

fp.run(u.trajectory[frame_indices[0]:frame_indices[-1]+1],
       ligand, protein,
       residues=None)

# fp.ifp  : dict  frame_index -> {(lig_res, prot_res): {interaction: bool, ...}}
# fp.to_dataframe() gives a MultiIndex DataFrame

df_wide = fp.to_dataframe(return_atoms=False)

# ---------------------------------------------------------------------------
# Reshape to long format for CSV
# ---------------------------------------------------------------------------
# df_wide index = frame numbers, columns = MultiIndex (ligand, protein, interaction)
records = []
for frame_idx, row in df_wide.iterrows():
    for col, value in row.items():
        # col is a tuple: (ligand_res_str, protein_res_str, interaction_type)
        if isinstance(col, tuple) and len(col) == 3:
            lig_res, prot_res, interaction = col
        else:
            lig_res, prot_res, interaction = str(col), "", ""

        col_name = f"{lig_res}-{prot_res}_{interaction}_frame{frame_idx}"
        records.append({
            "column_name": col_name,
            "ligand":      lig_res,
            "protein":     prot_res,
            "interaction": interaction,
            "frame":       frame_idx,
            "Y":           int(bool(value)),
        })

df_out = pd.DataFrame(records)

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
out_path = os.path.join(OUT_DIR, "ligand_fingerprint_pred.csv")
df_out.to_csv(out_path, index=False)
print(f"Saved {len(df_out)} rows to {out_path}")
