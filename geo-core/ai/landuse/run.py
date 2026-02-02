import os
import rasterio
from scripts.ai.landuse.io import align_to_reference
from scripts.ai.landuse.model import classify_landuse

OUTPUT_DIR = "data/ai"

def run_landuse():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    satellite_path = "data/normalized/satellite_utm.tif"
    elevation_path = "data/terrain/elevation.tif"
    slope_path = "data/terrain/slope.tif"

    elevation, meta = align_to_reference(satellite_path, elevation_path)
    slope, _ = align_to_reference(satellite_path, slope_path)

    with rasterio.open(satellite_path) as src:
        satellite = src.read(1)

    landuse, confidence = classify_landuse(satellite, elevation, slope)

    # --- LANDUSE ---
    landuse_meta = meta.copy()
    landuse_meta.update(
        driver="GTiff",
        dtype=rasterio.uint8,
        count=1
    )

    with rasterio.open(f"{OUTPUT_DIR}/landuse.tif", "w", **landuse_meta) as dst:
        dst.write(landuse, 1)

    # --- CONFIDENCE ---
    conf_meta = meta.copy()
    conf_meta.update(
        driver="GTiff",
        dtype=rasterio.float32,
        count=1
    )

    with rasterio.open(f"{OUTPUT_DIR}/confidence_map.tif", "w", **conf_meta) as dst:
        dst.write(confidence, 1)

    print("✅ Module 6 — Land-use classification completed")