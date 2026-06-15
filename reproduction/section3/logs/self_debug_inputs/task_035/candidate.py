import os
import numpy as np
import pandas as pd
import neurokit2 as nk

# Ensure output directory exists
os.makedirs("pred_results", exist_ok=True)

# Load data
data = pd.read_csv("benchmark/datasets/biosignals/bio_eventrelated_100hz.csv")

# Extract RSP signal
rsp_signal = data["RSP"].values
sampling_rate = 100  # Hz

# Clean the RSP signal
rsp_cleaned = nk.rsp_clean(rsp_signal, sampling_rate=sampling_rate)

# Extract inhalation peaks and respiratory rate signal
rsp_peaks, rsp_info = nk.rsp_peaks(rsp_cleaned, sampling_rate=sampling_rate)

# Get the respiratory rate signal
rsp_rate = nk.rsp_rate(rsp_peaks, sampling_rate=sampling_rate, desired_length=len(rsp_signal))

# Perform RRV analysis
# nk.rrv expects the inhalation peaks (troughs in neurokit2 convention) indices
# rsp_info contains 'RSP_Peaks' for peaks and 'RSP_Troughs' for troughs
# For RRV, we use the peak-to-peak intervals (inhalation onset = peaks)
rrv_indices = nk.rrv(
    rsp_rate,
    rsp_peaks,
    sampling_rate=sampling_rate,
    show=False
)

# Save results
rrv_indices.to_csv("pred_results/rrv_analysis_pred.csv", index=False)

print("RRV analysis complete. Results saved to pred_results/rrv_analysis_pred.csv")
print(rrv_indices)
