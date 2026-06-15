import pandas as pd
import biopsykit
import json
import os

# Load data
data = pd.read_pickle("benchmark/datasets/saliva_data/data.pkl")

# Compute standard features using biopsykit
features = biopsykit.saliva.standard_features(data)

# Reset index to work with the data more easily
features_reset = features.reset_index()

# Build the output dictionary of dictionaries
# The index is (condition, subject), so we group by those
result = {}

for _, row in features_reset.iterrows():
    condition = row["condition"]
    subject = row["subject"]

    subject_key = subject

    entry = {"condition": condition}
    for col in features_reset.columns:
        if col not in ("condition", "subject"):
            entry[col] = row[col]

    result[subject_key] = entry

# Ensure output directory exists
os.makedirs("pred_results", exist_ok=True)

# Write to JSON
with open("pred_results/saliva_pred.json", "w") as f:
    json.dump(result, f, indent=2)
