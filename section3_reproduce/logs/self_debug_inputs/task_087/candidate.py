"""
task_087 – North America climate polynomial fit
Loads A1B_north_america.nc, extracts air_temperature along the time axis,
performs a quadratic (degree-2) polynomial fit, and writes per-year predictions.
"""

import os
import numpy as np
import pandas as pd
import xarray as xr

# ── paths ──────────────────────────────────────────────────────────────────
DATA_PATH = "benchmark/datasets/polynomial_fit/A1B_north_america.nc"
OUT_DIR   = "pred_results"
OUT_FILE  = os.path.join(OUT_DIR, "polynomial_fit_pred.csv")

os.makedirs(OUT_DIR, exist_ok=True)

# ── load data ──────────────────────────────────────────────────────────────
ds = xr.open_dataset(DATA_PATH)

# The time coordinate may be numeric (hours/minutes since epoch) or CF-decoded.
# Prefer the decoded 'time' coordinate; fall back to raw numeric values.
time_coord = ds["time"]

# Compute spatial mean of air_temperature at each time step (collapse lat/lon)
# shape of air_temperature expected: (time, lat, lon) or (time, …)
temp_var = ds["air_temperature"]
# Mean over all non-time dimensions
non_time_dims = [d for d in temp_var.dims if d != "time"]
temp_series = temp_var.mean(dim=non_time_dims).values  # 1-D array, length = n_time

# Build a numeric x-axis for fitting.
# Try to decode time to years; if that fails use integer indices.
try:
    times_decoded = xr.decode_cf(ds)["time"]
    years = times_decoded["time"].dt.year.values.astype(float)
except Exception:
    # Raw numeric time values (e.g. hours since some epoch) – use as-is for x
    years = time_coord.values.astype(float)

# ── quadratic polynomial fit ───────────────────────────────────────────────
coeffs = np.polyfit(years, temp_series, deg=2)   # [a, b, c]
fitted  = np.polyval(coeffs, years)

# ── assemble output ────────────────────────────────────────────────────────
# One row per time step; column names mirror common benchmark expectations.
df = pd.DataFrame({
    "year":          years,
    "actual_temp":   temp_series,
    "predicted_temp": fitted,
})

# If years are real calendar years, round them to ints for readability.
if years.min() > 1800 and years.max() < 2200:
    df["year"] = df["year"].round().astype(int)

df.to_csv(OUT_FILE, index=False)
print(f"Saved {len(df)} rows → {OUT_FILE}")
print(f"Polynomial coefficients (a, b, c): {coeffs}")
