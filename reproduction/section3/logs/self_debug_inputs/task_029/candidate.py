import numpy as np
import pandas as pd
import neurokit2 as nk
import os

# Setup
os.makedirs("pred_results", exist_ok=True)

SAMPLING_RATE = 100  # 100 Hz

# Load data
df = pd.read_csv("benchmark/datasets/biosignals/bio_eventrelated_100hz.csv")

# --- Event localization via Photosensor ---
# The Photosensor column marks stimulus events; transitions from low to high indicate event onset.
photosensor = df["Photosensor"].values

# Binarize: values > median are "high" (event on)
threshold = (photosensor.max() + photosensor.min()) / 2
binary = (photosensor > threshold).astype(int)

# Detect rising edges (0->1 transitions) as event onsets
diff = np.diff(binary, prepend=binary[0])
event_onsets = np.where(diff == 1)[0]

# If no photosensor events, fall back to equal segments
if len(event_onsets) == 0:
    # Fallback: split into 2 equal halves as Condition A and B
    n = len(df)
    event_onsets = np.array([0, n // 2])

# Build epochs: 2s pre-stimulus to 3s post-stimulus
pre_samples = int(2 * SAMPLING_RATE)   # 200 samples before
post_samples = int(3 * SAMPLING_RATE)  # 300 samples after

# Process full signals
ecg_signals, ecg_info = nk.ecg_process(df["ECG"].values, sampling_rate=SAMPLING_RATE)
eda_signals, eda_info = nk.eda_process(df["EDA"].values, sampling_rate=SAMPLING_RATE)
rsp_signals, rsp_info = nk.rsp_process(df["RSP"].values, sampling_rate=SAMPLING_RATE)

# Extract epoch-level features per event
records = []
for i, onset in enumerate(event_onsets):
    start = max(0, onset - pre_samples)
    end = min(len(df), onset + post_samples)

    condition = f"Condition_{i+1}"

    # ECG Rate Mean in epoch
    ecg_rate_epoch = ecg_signals["ECG_Rate"].iloc[start:end]
    ecg_rate_mean = ecg_rate_epoch.mean()

    # RSP Rate Mean in epoch
    rsp_rate_epoch = rsp_signals["RSP_Rate"].iloc[start:end]
    rsp_rate_mean = rsp_rate_epoch.mean()

    # EDA Peak Amplitude in epoch: max SCR amplitude detected
    eda_phasic_epoch = eda_signals["EDA_Phasic"].iloc[start:end]
    # SCR peaks within epoch
    scr_peaks_epoch = eda_signals["EDA_SCR_Peaks"].iloc[start:end]
    scr_peak_indices = np.where(scr_peaks_epoch.values == 1)[0]
    if len(scr_peak_indices) > 0:
        eda_peak_amplitude = eda_phasic_epoch.iloc[scr_peak_indices].max()
    else:
        # If no SCR peaks detected, use max phasic amplitude
        eda_peak_amplitude = eda_phasic_epoch.max()

    records.append({
        "Condition": condition,
        "ECG_Rate_Mean": ecg_rate_mean,
        "RSP_Rate_Mean": rsp_rate_mean,
        "EDA_Peak_Amplitude": eda_peak_amplitude,
    })

results_df = pd.DataFrame(records, columns=["Condition", "ECG_Rate_Mean", "RSP_Rate_Mean", "EDA_Peak_Amplitude"])
results_df.to_csv("pred_results/bio_eventrelated_100hz_analysis_pred.csv", index=False)
print("Saved:", results_df.shape)
print(results_df)
