import pandas as pd
import os

# Paths
data_dir = "benchmark/datasets/papyrus"
output_dir = "pred_results"
os.makedirs(output_dir, exist_ok=True)

# Load datasets
unfiltered = pd.read_pickle(os.path.join(data_dir, "papyrus_unfiltered.pkl"))
protein_set = pd.read_pickle(os.path.join(data_dir, "papyrus_protein_set.pkl"))

# --- Filter 1: Quality 'medium' or above ---
# Quality levels (ascending): low < medium < high
quality_order = {"low": 0, "medium": 1, "high": 2}
# Normalize case for comparison
unfiltered["_quality_lower"] = unfiltered["Quality"].str.lower()
filtered = unfiltered[unfiltered["_quality_lower"].isin(["medium", "high"])].copy()
filtered.drop(columns=["_quality_lower"], inplace=True)

# --- Filter 2: Only keep proteins in two specific classes ---
# Use protein_set to identify which target_ids belong to:
# 'Ligand-gated ion channels' or 'SLC superfamily of solute carriers'
target_classes = ["Ligand-gated ion channels", "SLC superfamily of solute carriers"]

def belongs_to_target_class(classification, classes):
    """Check if the classification string contains any of the target classes."""
    if pd.isna(classification):
        return False
    for cls in classes:
        if cls in classification:
            return True
    return False

# Normalize column name (could be 'Classification' or 'classification')
class_col = [c for c in protein_set.columns if c.lower() == "classification"][0]
protein_set["_belongs"] = protein_set[class_col].apply(
    lambda x: belongs_to_target_class(x, target_classes)
)
valid_target_ids = set(protein_set.loc[protein_set["_belongs"], "target_id"])
filtered = filtered[filtered["target_id"].isin(valid_target_ids)].copy()

# --- Filter 3: Only keep activity types Ki or KD ---
# The columns type_KD and type_Ki are indicator columns (1 or 0, or semicolon-separated)
# Based on preview, type_Ki and type_KD have values like "0;0", "1;1"
# A row has Ki if any value in type_Ki is non-zero; same for KD
def has_activity(col_val):
    """Return True if the semicolon-separated string has at least one non-zero value."""
    if pd.isna(col_val):
        return False
    parts = str(col_val).split(";")
    return any(p.strip() not in ("0", "") for p in parts)

ki_mask = filtered["type_Ki"].apply(has_activity)
kd_mask = filtered["type_KD"].apply(has_activity)
filtered = filtered[ki_mask | kd_mask].copy()

# --- Filter 4: Only keep human and rat data ---
# Organism info is in protein_set; join on target_id
organism_col = [c for c in protein_set.columns if c.lower() == "organism"][0]
target_organism = protein_set[["target_id", organism_col]].drop_duplicates()
target_organism = target_organism.rename(columns={organism_col: "_organism"})
filtered = filtered.merge(target_organism, on="target_id", how="left")

human_rat_terms = ["homo sapiens", "rattus norvegicus"]
filtered["_org_lower"] = filtered["_organism"].str.lower().fillna("")
filtered = filtered[filtered["_org_lower"].apply(
    lambda x: any(term in x for term in human_rat_terms)
)].copy()
filtered.drop(columns=["_organism", "_org_lower"], inplace=True)

# Save result — same column names as original
output_path = os.path.join(output_dir, "papyrus_filtered.pkl")
filtered.to_pickle(output_path)
print(f"Filtered dataset saved to {output_path} with {len(filtered)} rows.")
