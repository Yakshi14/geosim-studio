from pathlib import Path
import rasterio
import os

# Import CRS handler
from crs_handler import handle_raster_crs

# --------------------------------------------------
# 1. Resolve project root
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

# --------------------------------------------------
# 2. Input: Raw satellite file
# --------------------------------------------------
raw_sat = BASE_DIR / "data" / "raw" / "satellite" / "mumbai_satellite.jp2"

# --------------------------------------------------
# 3. Output: Processed satellite (ingestion only)
# --------------------------------------------------
processed_sat = BASE_DIR / "data" / "processed" / "satellite" / "mumbai_satellite.tif"

# CRS-normalized output
processed_sat_crs = BASE_DIR / "data" / "processed" / "satellite" / "mumbai_satellite_epsg4326.tif"

# --------------------------------------------------
# 4. Pre-flight checks
# --------------------------------------------------
print("📂 Project Root:", BASE_DIR)
print("🛰️ Raw Satellite Path:", raw_sat)

if not raw_sat.exists():
    raise FileNotFoundError(
        f"\n❌ Satellite file not found!\n"
        f"Expected at:\n{raw_sat}\n\n"
        f"✔ Check filename\n"
        f"✔ Check folder name (satellite)\n"
        f"✔ Ensure file is extracted (.jp2)\n"
    )

os.makedirs(processed_sat.parent, exist_ok=True)

# --------------------------------------------------
# 5. Satellite ingestion (NO CRS conversion here)
# --------------------------------------------------
with rasterio.open(raw_sat) as src:
    metadata = src.meta.copy()

    with rasterio.open(processed_sat, "w", **metadata) as dst:
        for band in range(1, src.count + 1):
            dst.write(src.read(band), band)

print("✅ Satellite ingestion completed")
print("📦 Ingested satellite saved at:", processed_sat)

# --------------------------------------------------
# 6. CRS Detection & Reprojection (Handled separately)
# --------------------------------------------------
handle_raster_crs(
    processed_sat,
    processed_sat_crs
)

print("🌍 CRS normalization completed")
print("📦 CRS-normalized satellite saved at:", processed_sat_crs)
