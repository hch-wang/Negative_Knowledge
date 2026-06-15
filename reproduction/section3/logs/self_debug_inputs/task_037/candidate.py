import pandas as pd
import biopsykit as bp
import json
import os

# Load heart rate data from the MIST3 sheet
data_path = "benchmark/datasets/mist_hr/hr_sample_mist.xlsx"
df = pd.read_excel(data_path, sheet_name="MIST3")

# The columns are: timestamps, TP9, AF7, AF8, TP10, Right AUX
# We'll use the first EEG/HR channel as the heart rate signal.
# BioPsyKit CFT analysis expects heart rate data; we'll use the mean of
# the relevant EEG-adjacent channels as a proxy HR or treat raw values.
# The data preview shows electrode voltage values, but the task says "heart rate data"
# so we treat these as HR bpm values using one channel (e.g., TP9 or the mean).

# Use mean of the numeric HR channels (excluding timestamps and Right AUX which is 0)
hr_channels = ["TP9", "AF7", "AF8", "TP10"]
df["hr"] = df[hr_channels].mean(axis=1)

# Convert timestamps to datetime index
df["time"] = pd.to_datetime(df["timestamps"], unit="s")
df = df.set_index("time")

# Extract the HR series
hr_series = df["hr"]

# CFT parameters:
# - baseline_hr: mean HR during a baseline period (first portion of the recording)
# - onset_hr: minimum HR after stimulus onset (the "dip" indicating vagal activation)
# - onset_hr_percent: percentage change from baseline to onset
#   onset_hr_percent = ((onset_hr - baseline_hr) / baseline_hr) * 100

# Determine baseline and onset windows
# Typical CFT: baseline is first ~30s, onset is the minimum in the remaining period
total_seconds = (hr_series.index[-1] - hr_series.index[0]).total_seconds()

# Baseline: first 30 seconds (or first third if recording is short)
baseline_duration = min(30, total_seconds / 3)
baseline_end = hr_series.index[0] + pd.Timedelta(seconds=baseline_duration)

baseline_data = hr_series[hr_series.index <= baseline_end]
onset_data = hr_series[hr_series.index > baseline_end]

baseline_hr = float(baseline_data.mean())

if len(onset_data) > 0:
    onset_hr = float(onset_data.min())
else:
    onset_hr = baseline_hr

onset_hr_percent = ((onset_hr - baseline_hr) / abs(baseline_hr)) * 100 if baseline_hr != 0 else 0.0

# Prepare output
results = {
    "baseline_hr": round(baseline_hr, 4),
    "onset_hr": round(onset_hr, 4),
    "onset_hr_percent": round(onset_hr_percent, 4),
}

# Save results
os.makedirs("pred_results", exist_ok=True)
output_path = "pred_results/cft_pred_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"CFT parameters saved to {output_path}")
print(json.dumps(results, indent=2))
