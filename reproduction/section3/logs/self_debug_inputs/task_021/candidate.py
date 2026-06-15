import geopandas as gpd
import pandas as pd
import os

# Load data
roads = gpd.read_file("benchmark/datasets/deforestation/roads.geojson")
deforested = gpd.read_file("benchmark/datasets/deforestation/deforestedArea.geojson")

# Ensure both layers are in a projected CRS for metric distance buffers
# Use a suitable UTM zone for Rondônia, Brazil (approx. UTM zone 20S: EPSG:32720)
roads_proj = roads.to_crs(epsg=32720)
deforested_proj = deforested.to_crs(epsg=32720)

# Create 5.5km buffer around road geometries and dissolve into one polygon
buffer_dist_m = 5500  # 5.5 km in meters
roads_buffer = roads_proj.copy()
roads_buffer["geometry"] = roads_proj.geometry.buffer(buffer_dist_m)
roads_buffer_dissolved = roads_buffer.dissolve()

# Clip the deforested area to the road buffer zone
deforested_in_buffer = gpd.clip(deforested_proj, roads_buffer_dissolved)

# Calculate areas
total_deforested_area = deforested_proj.geometry.area.sum()
deforested_in_buffer_area = deforested_in_buffer.geometry.area.sum()

# Percentage of deforested area within the buffer zone
percentage = (deforested_in_buffer_area / total_deforested_area) * 100

# Save result
os.makedirs("pred_results", exist_ok=True)
result_df = pd.DataFrame({"percentage_deforestation": [percentage]})
result_df.to_csv("pred_results/deforestation_rate.csv", index=False)

print(f"Deforestation percentage within 5.5km road buffer: {percentage:.4f}%")
