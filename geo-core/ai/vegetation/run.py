# ===== MODULE 6 RUNNER (STANDALONE, WORKS WITH geo-core FOLDER) =====

from pathlib import Path
import rasterio
import numpy as np
from rasterio.warp import reproject, Resampling

# 🔹 IMPORTANT FIX: relative import (NO geo_core)
from model import classify_landuse

# ---------------- PATHS ----------------
BASE_DIR = Path(__file__).resolve().parents[3]   # goes up to geosim-studio
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
AI_DIR = BASE_DIR / "data" / "ai"
AI_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- HELPERS ----------------
def find_first_tif(directory, keyword):
    """Find first matching .tif file"""
    files = list(directory.glob("*.tif"))
    for f in files:
        if keyword in f.name.lower():
            return f
    return files[0] if files else None

def align_to_reference(reference_path, target_path):
    """Align DEM to satellite grid"""
    with rasterio.open(reference_path) as ref:
        ref_meta = ref.meta.copy()
        ref_shape = (ref.height, ref.width)

        with rasterio.open(target_path) as tgt:
            aligned = np.zeros(ref_shape, dtype=tgt.dtypes[0])

            reproject(
                source=rasterio.band(tgt, 1),
                destination=aligned,
                src_transform=tgt.transform,
                src_crs=tgt.crs,
                dst_transform=ref.transform,
                dst_crs=ref.crs,
                resampling=Resampling.bilinear,
            )

    return aligned, ref_meta

def save_raster(array, reference_meta, out_path):
    """
    Safe GeoTIFF writer (fixes opj_read_header error)
    """

    meta = reference_meta.copy()

    # 🔹 CRITICAL FIXES 🔹
    meta.update({
        "driver": "GTiff",           # <-- IMPORTANT
        "count": 1,
        "dtype": "float32" if array.dtype.kind == "f" else "int32",
        "compress": "lzw"
    })

    # Ensure directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(array.astype(meta["dtype"]), 1)


# ---------------- MAIN PIPELINE ----------------
def run_landuse():
    print("\n=== MODULE 6 — AI LANDUSE CLASSIFICATION ===")

    sat_path = find_first_tif(NORMALIZED_DIR, "sat")
    dem_path = find_first_tif(NORMALIZED_DIR, "dem")

    if not sat_path or not dem_path:
        print("❌ Missing normalized inputs!")
        print("Files in data/normalized:", list(NORMALIZED_DIR.glob("*.tif")))
        return

    print("Using:")
    print("  Satellite:", sat_path)
    print("  DEM:", dem_path)

    # Align DEM to satellite grid
    elevation, meta = align_to_reference(sat_path, dem_path)

    # Read satellite band
    with rasterio.open(sat_path) as src:
        satellite = src.read(1)

    # AI (MOCK for Phase 1)
    landuse, confidence = classify_landuse(satellite, elevation)

    # Save outputs
    save_raster(landuse, meta, AI_DIR / "landuse.tif")
    save_raster(confidence, meta, AI_DIR / "confidence_map.tif")

    print("✅ Module 6 completed.")
    print("Outputs saved to:", AI_DIR)

if __name__ == "__main__":
    run_landuse()
