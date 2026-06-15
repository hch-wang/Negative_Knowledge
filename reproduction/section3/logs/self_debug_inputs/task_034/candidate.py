import pandas as pd
import numpy as np
import neurokit2 as nk
import os

# Ensure output directory exists
os.makedirs("pred_results", exist_ok=True)

# Load ECG data
data = pd.read_csv("benchmark/datasets/biosignals/bio_resting_5min_100hz.csv")
ecg_signal = data["ECG"].values
sampling_rate = 100  # Hz

# Process ECG: find peaks and clean signal
ecg_cleaned = nk.ecg_clean(ecg_signal, sampling_rate=sampling_rate)
_, rpeaks = nk.ecg_peaks(ecg_cleaned, sampling_rate=sampling_rate)

# Compute HRV indices across all three domains
hrv_time = nk.hrv_time(rpeaks, sampling_rate=sampling_rate)
hrv_freq = nk.hrv_frequency(rpeaks, sampling_rate=sampling_rate)
hrv_nonlinear = nk.hrv_nonlinear(rpeaks, sampling_rate=sampling_rate)

# Combine all features into one DataFrame
hrv_all = pd.concat([hrv_time, hrv_freq, hrv_nonlinear], axis=1)

# Save to output
hrv_all.to_csv("pred_results/hrv_analysis_pred.csv", index=False)
print("HRV analysis complete. Results saved to pred_results/hrv_analysis_pred.csv")
