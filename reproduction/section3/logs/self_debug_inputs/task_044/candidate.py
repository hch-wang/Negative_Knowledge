import os
import json
import pickle
import pandas as pd
import biopsykit as bp
from biopsykit.sleep.sleep_processing_pipeline import predict_pipeline_acceleration

# Paths
data_path = "benchmark/datasets/sleep_imu_data/sleep_data.pkl"
output_dir = "pred_results"
output_path = os.path.join(output_dir, "imu_pred.json")

# Load data
with open(data_path, "rb") as f:
    data = pickle.load(f)

# Ensure it's a DataFrame
if not isinstance(data, pd.DataFrame):
    data = pd.DataFrame(data)

# Ensure the index is a DatetimeIndex (with timezone) if 'time' is a column
if "time" in data.columns:
    data = data.set_index("time")

data.index = pd.to_datetime(data.index, utc=False)

# Extract acceleration columns
acc_cols = [c for c in data.columns if c.startswith("acc_")]
acc_data = data[acc_cols].copy()
# Rename to expected format if needed: acc_x, acc_y, acc_z
acc_data.columns = [c.replace("acc_", "") for c in acc_data.columns]

# Run the BioPsyKit sleep processing pipeline
sleep_results = predict_pipeline_acceleration(acc_data)

# Extract endpoints
# sleep_results is typically a dict with keys like 'sleep_onset', 'wake_onset', 'sleep_duration'
# or it may be an object with attributes; handle both cases

def extract_endpoint(results, *keys):
    """Try multiple key names and attribute access patterns."""
    for key in keys:
        if isinstance(results, dict):
            if key in results:
                val = results[key]
                if hasattr(val, "isoformat"):
                    return val.isoformat()
                return str(val)
        elif hasattr(results, key):
            val = getattr(results, key)
            if hasattr(val, "isoformat"):
                return val.isoformat()
            return str(val)
    return None

sleep_onset = extract_endpoint(sleep_results, "sleep_onset", "sleep_onset_time")
wake_onset = extract_endpoint(sleep_results, "wake_onset", "wake_onset_time", "wake_time")
total_sleep_duration = extract_endpoint(
    sleep_results, "total_sleep_duration", "sleep_duration", "duration"
)

# If total_sleep_duration is a timedelta or numeric, convert appropriately
if "total_sleep_duration" in (sleep_results if isinstance(sleep_results, dict) else {}):
    raw = sleep_results["total_sleep_duration"]
elif hasattr(sleep_results, "total_sleep_duration"):
    raw = sleep_results.total_sleep_duration
else:
    raw = None

if raw is not None and hasattr(raw, "total_seconds"):
    total_sleep_duration = raw.total_seconds() / 60.0  # minutes
elif raw is not None:
    try:
        total_sleep_duration = float(raw)
    except (TypeError, ValueError):
        total_sleep_duration = str(raw)

# Build output dict
output = {
    "sleep_onset": sleep_onset,
    "wake_onset": wake_onset,
    "total_sleep_duration": total_sleep_duration,
}

# Save
os.makedirs(output_dir, exist_ok=True)
with open(output_path, "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"Saved results to {output_path}")
print(json.dumps(output, indent=2, default=str))
