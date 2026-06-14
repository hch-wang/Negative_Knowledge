import os
import pandas as pd
from modnet.preprocessing import MODData
from modnet.models import MODNetModel

# Paths
TRAIN_PATH = "benchmark/datasets/experimental_band_gap/matbench_expt_gap_train"
TEST_PATH = "benchmark/datasets/experimental_band_gap/matbench_expt_gap_test"
OUTPUT_DIR = "pred_results"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "experimental_band_gap_prediction_pred.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load training data (matbench format: JSON/compressed pandas)
train_df = pd.read_json(TRAIN_PATH, orient="split", compression="gzip")
test_df = pd.read_json(TEST_PATH, orient="split", compression="gzip")

target_col = "gap_expt_eV"

# Build MODData for training
train_moddata = MODData(
    materials=train_df["structure"].tolist(),
    targets=train_df[[target_col]],
    target_names=[target_col],
)
train_moddata.featurize(fast=False, n_jobs=1)
train_moddata.feature_selection(n=150)

# Build MODData for test (inherit feature set from training)
test_moddata = MODData(
    materials=test_df["structure"].tolist(),
)
test_moddata.featurize(fast=False, n_jobs=1)

# Define model: 4-tuple of lists matching the architecture 256, 128, 16, 16
model = MODNetModel(
    [[target_col]],
    weights={target_col: 1},
    num_neurons=([256], [128], [16], [16]),
    n_feat=150,
    act="elu",
)

# Train
model.fit(train_moddata)

# Predict
predictions = model.predict(test_moddata)

# predictions is a DataFrame with columns matching target_names
if target_col not in predictions.columns:
    # rename first column if necessary
    predictions.columns = [target_col]

predictions[[target_col]].to_csv(OUTPUT_FILE, index=False)
print(f"Saved predictions to {OUTPUT_FILE}")
