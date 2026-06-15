import os
import pickle
import numpy as np
import deepchem as dc
from deepchem.models import CGCNNModel

# Ensure output directory exists
os.makedirs("pred_results", exist_ok=True)

# Load the perovskite dataset from pkl files
with open("benchmark/datasets/perovskite/perovskite_train.pkl", "rb") as f:
    train_data = pickle.load(f)

with open("benchmark/datasets/perovskite/perovskite_test.pkl", "rb") as f:
    test_data = pickle.load(f)

# The pkl files contain NumpyDataset objects (deepchem.data.NumpyDataset)
# If they are already NumpyDataset, use directly; otherwise wrap them.
if isinstance(train_data, dc.data.NumpyDataset):
    train_dataset = train_data
else:
    # Assume dict-like or tuple with X, y
    if isinstance(train_data, dict):
        X_train = train_data["X"]
        y_train = train_data["y"]
        w_train = train_data.get("w", np.ones(len(y_train)))
        ids_train = train_data.get("ids", np.arange(len(y_train)))
    else:
        X_train, y_train = train_data[0], train_data[1]
        w_train = np.ones(len(y_train))
        ids_train = np.arange(len(y_train))
    train_dataset = dc.data.NumpyDataset(X=X_train, y=y_train, w=w_train, ids=ids_train)

if isinstance(test_data, dc.data.NumpyDataset):
    test_dataset = test_data
else:
    if isinstance(test_data, dict):
        X_test = test_data["X"]
        y_test = test_data.get("y", np.zeros(len(X_test)))
        w_test = test_data.get("w", np.ones(len(y_test)))
        ids_test = test_data.get("ids", np.arange(len(y_test)))
    else:
        X_test = test_data[0]
        y_test = test_data[1] if len(test_data) > 1 else np.zeros(len(X_test))
        w_test = np.ones(len(y_test))
        ids_test = np.arange(len(y_test))
    test_dataset = dc.data.NumpyDataset(X=X_test, y=y_test, w=w_test, ids=ids_test)

# Determine feature dimensions from training data
# CGCNN expects graph-structured inputs; NumpyDataset X should be GraphData objects
# Use CGCNNModel for regression
model = CGCNNModel(
    mode="regression",
    n_tasks=1,
    batch_size=32,
    learning_rate=0.001,
)

# Train the model
model.fit(train_dataset, nb_epoch=50)

# Predict on test set
predictions = model.predict(test_dataset)

# predictions shape: (n_samples, n_tasks) or (n_samples,)
predictions = np.array(predictions).flatten()

# Save predictions
np.savetxt("pred_results/formation_energy_prediction_pred.txt", predictions)
