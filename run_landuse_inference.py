import os
import torch
import rasterio
import numpy as np

# Output directory
OUT_DIR = "data/ai"
os.makedirs(OUT_DIR, exist_ok=True)

# ------------------------------------------------------------------
# DUMMY MODEL OUTPUT (replace with TorchGeo + SAM later)
# ------------------------------------------------------------------
# This proves the pipeline + saving works

H, W = 1024, 1024

# Classes:
# 0 Urban | 1 Forest | 2 Grassland | 3 Water | 4 Bare | 5 Agriculture
landuse = np.random.randint(0, 6, (H, W)).astype("uint8")
confidence = np.random.uniform(0.4, 0.95, (H, W)).astype("float32")

# Geo metadata (fake but valid)
transform = rasterio.transform.from_origin(72.8, 19.3, 10, 10)

profile = {
    "driver": "GTiff",
    "height": H,
    "width": W,
    "count": 1,
    "dtype": "uint8",
    "crs": "EPSG:4326",
    "transform": transform
}

# Save landuse
with rasterio.open(f"{OUT_DIR}/landuse.tif", "w", **profile) as dst:
    dst.write(landuse, 1)

# Save confidence
profile["dtype"] = "float32"
with rasterio.open(f"{OUT_DIR}/confidence_map.tif", "w", **profile) as dst:
    dst.write(confidence, 1)

print("✅ AI landuse inference complete")
print("📁 Outputs saved to data/ai/")
