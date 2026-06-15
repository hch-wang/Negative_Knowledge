import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score

# Load data
train_df = pd.read_csv("benchmark/datasets/dkpes/dkpes_train.csv", index_col=0)
test_df = pd.read_csv("benchmark/datasets/dkpes/dkpes_test.csv", index_col=0)

# Separate target and features in train
target_col = "Signal-inhibition"
feature_cols = [c for c in train_df.columns if c != target_col]

X_train = train_df[feature_cols].copy()
y_signal = train_df[target_col].copy()

# Handle non-numeric columns (e.g., ShapeQuery)
# Drop or encode string columns
string_cols = [c for c in feature_cols if X_train[c].dtype == object]
X_train = X_train.drop(columns=string_cols)

# Update feature list after dropping string cols
numeric_feature_cols = [c for c in feature_cols if c not in string_cols]

# Choose threshold: use 0.5 as a standard midpoint threshold for binary inhibition
# Signal inhibition values in the preview range ~0.24 to 0.686
# A threshold of 0.5 is a natural choice (inhibited vs. not inhibited)
threshold = 0.5
y_train = (y_signal >= threshold).astype(int)

# Prepare test features
X_test = test_df[numeric_feature_cols] if target_col not in test_df.columns else test_df[[c for c in numeric_feature_cols if c in test_df.columns]]

# If test_df has the target column, separate it
if target_col in test_df.columns:
    X_test = test_df[numeric_feature_cols]
else:
    # test may not have signal inhibition column; use available columns
    available_test_cols = [c for c in numeric_feature_cols if c in test_df.columns]
    X_test = test_df[available_test_cols]
    # Align train to same columns
    X_train = X_train[available_test_cols]

# Fill any missing values with column medians
X_train = X_train.fillna(X_train.median())
X_test = X_test.fillna(X_train.median())

# Train Random Forest classifier
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=42,
    n_jobs=-1
)
rf.fit(X_train, y_train)

# Predict on test set
y_pred_proba = rf.predict_proba(X_test)[:, 1]  # probability of class 1 (inhibited)
y_pred = (y_pred_proba >= 0.5).astype(int)

# Build output dataframe: index + predicted signal inhibition (as binary label)
# The task says "predicted signal inhibition" — we output the binary label (0 or 1)
out_df = pd.DataFrame({
    "index": test_df.index,
    "Signal-inhibition": y_pred
})
out_df = out_df.set_index("index")

# Save predictions
os.makedirs("pred_results", exist_ok=True)
out_df.to_csv("pred_results/dkpes_test_pred.csv")
