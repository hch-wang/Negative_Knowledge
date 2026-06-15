import numpy as np
import os
from sklearn.linear_model import Ridge

# Paths
train_sub01_path = "benchmark/datasets/thingseeg2/train/sub01.npy"
train_sub03_path = "benchmark/datasets/thingseeg2/train/sub03.npy"
test_sub01_path = "benchmark/datasets/thingseeg2/test/sub01.npy"
output_path = "pred_results/linear_sub01tosub03_pred.npy"

# Load data
train_sub01 = np.load(train_sub01_path)  # (16540, 17, 200)
train_sub03 = np.load(train_sub03_path)  # (16540, 17, 200)
test_sub01 = np.load(test_sub01_path)    # (200, 17, 200)

# Flatten spatial+temporal dims: (n_samples, 17*200)
n_train = train_sub01.shape[0]
n_test = test_sub01.shape[0]
n_features = train_sub01.shape[1] * train_sub01.shape[2]  # 17*200 = 3400

X_train = train_sub01.reshape(n_train, n_features)
Y_train = train_sub03.reshape(n_train, n_features)
X_test = test_sub01.reshape(n_test, n_features)

# Normalize based on training data statistics
X_mean = X_train.mean(axis=0, keepdims=True)
X_std = X_train.std(axis=0, keepdims=True) + 1e-8
Y_mean = Y_train.mean(axis=0, keepdims=True)
Y_std = Y_train.std(axis=0, keepdims=True) + 1e-8

X_train_norm = (X_train - X_mean) / X_std
Y_train_norm = (Y_train - Y_mean) / Y_std
X_test_norm = (X_test - X_mean) / X_std

# Train Ridge regression (linear model)
model = Ridge(alpha=1.0)
model.fit(X_train_norm, Y_train_norm)

# Predict on test set
Y_test_norm_pred = model.predict(X_test_norm)

# Denormalize predictions
Y_test_pred = Y_test_norm_pred * Y_std + Y_mean

# Reshape back to (200, 17, 200)
Y_test_pred = Y_test_pred.reshape(n_test, train_sub01.shape[1], train_sub01.shape[2])

# Save output
os.makedirs("pred_results", exist_ok=True)
np.save(output_path, Y_test_pred)
print(f"Saved predictions to {output_path}, shape: {Y_test_pred.shape}")
