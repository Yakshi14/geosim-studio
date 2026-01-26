from pathlib import Path
import rasterio

# Import CRS handler
from crs_handler import handle_raster_crs

# --------------------------------------------------
# 1. Resolve project root safely
#    Assumes structure:
#    geo_project/
#      ├── scripts/
#      │     └── dem_ingest.py
#      └── data/
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

# --------------------------------------------------
# 2. INPUT: Raw DEM file path
# --------------------------------------------------
raw_dem = BASE_DIR / "data" / "raw" / "dem" / "mumbai_dem.tif"

# --------------------------------------------------
# 3. OUTPUT: Processed DEM (ingestion output only)
# --------------------------------------------------
processed_dem = BASE_DIR / "data" / "processed" / "dem" / "mumbai_dem.tif"

# CRS-normalized output
processed_dem_crs = BASE_DIR / "data" / "processed" / "dem" / "mumbai_dem_epsg4326.tif"

# --------------------------------------------------
# 4. Pre-flight checks
# --------------------------------------------------
print("📂 Project Root:", BASE_DIR)
print("📄 Raw DEM Path:", raw_dem)

if not raw_dem.exists():
    raise FileNotFoundError(
        f"\n❌ DEM file not found!\n"
        f"Expected at:\n{raw_dem}\n\n"
        f"✔ Check filename\n"
        f"✔ Check folder name (dem)\n"
        f"✔ Ensure DEM is extracted (.tif, not .zip)\n"
    )

# Create processed directory if not exists
processed_dem.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 5. DEM Ingestion (NO CRS conversion here)
# --------------------------------------------------
with rasterio.open(raw_dem) as src:
    metadata = src.meta.copy()

    with rasterio.open(processed_dem, "w", **metadata) as dst:
        for band in range(1, src.count + 1):
            dst.write(src.read(band), band)

print("✅ DEM ingestion completed")
print("📦 Ingested DEM saved at:", processed_dem)

# --------------------------------------------------
# 6. CRS Detection & Reprojection (Handled separately)
# --------------------------------------------------
handle_raster_crs(
    processed_dem,
    processed_dem_crs
)

print("🌍 CRS normalization completed")
print("📦 CRS-normalized DEM saved at:", processed_dem_crs)
