"""
MODULE 4 — TERRAIN INTELLIGENCE ENGINE
-------------------------------------
Goal:
Extract simulation-critical terrain properties.

Generated Products:
- elevation.tif
- slope.tif
- aspect.tif
- terrain_stats.json
"""

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

import os
import json
import numpy as np
import rasterio
from pathlib import Path

# --------------------------------------------------
# CONFIG 
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "terrain")

os.makedirs(OUTPUT_DIR, exist_ok=True)

DEM_CANDIDATES = [
    f for f in os.listdir(NORMALIZED_DIR)
    if f.lower().endswith(".tif") and "dem" in f.lower()
]

if not DEM_CANDIDATES:
    raise FileNotFoundError("❌ No DEM file found in data/normalized/")

DEM_PATH = os.path.join(NORMALIZED_DIR, DEM_CANDIDATES[0])

# --------------------------------------------------
# LOAD DEM
# --------------------------------------------------

def load_dem(path):
    with rasterio.open(path) as src:
        dem = src.read(1).astype("float32")
        transform = src.transform
        profile = src.profile
        nodata = src.nodata

    if nodata is not None:
        dem[dem == nodata] = np.nan

    return dem, transform, profile

# --------------------------------------------------
# TERRAIN DERIVATIVES
# --------------------------------------------------

def compute_slope_aspect(dem, transform):
    xres = transform.a
    yres = -transform.e

    dz_dx = np.gradient(dem, axis=1) / xres
    dz_dy = np.gradient(dem, axis=0) / yres

    slope = np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)))

    aspect = np.degrees(np.arctan2(-dz_dx, dz_dy))
    aspect = np.where(aspect < 0, 360 + aspect, aspect)

    return slope, aspect

# --------------------------------------------------
# SAVE RASTER
# --------------------------------------------------

def save_raster(data, profile, out_path):
    profile = profile.copy()
    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=np.nan
    )

    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(data.astype("float32"), 1)

# --------------------------------------------------
# TERRAIN STATS
# --------------------------------------------------

def compute_stats(dem, slope,aspect):
    return {
        "elevation": {
            "min": float(np.nanmin(dem)),
            "max": float(np.nanmax(dem)),
            "mean": float(np.nanmean(dem))
        },
        "slope": {
            "min": float(np.nanmin(slope)),
            "max": float(np.nanmax(slope)),
            "mean": float(np.nanmean(slope))
        },
        "aspect":{
            "min": float(np.nanmin(aspect)),
            "max": float(np.nanmax(aspect)),
            "mean": float(np.nanmean(aspect))
        }
    }


def run_terrain_engine():
    print("▶ Loading DEM...")
    dem, transform, profile = load_dem(DEM_PATH)

    print("▶ Computing slope & aspect...")
    slope, aspect = compute_slope_aspect(dem, transform)


    print("▶ Saving rasters...")
    save_raster(dem, profile, os.path.join(OUTPUT_DIR, "elevation.tif"))
    save_raster(slope, profile, os.path.join(OUTPUT_DIR, "slope.tif"))
    save_raster(aspect, profile, os.path.join(OUTPUT_DIR, "aspect.tif"))

    print("▶ Computing terrain stats...")
    stats = compute_stats(dem, slope,aspect)

    with open(os.path.join(OUTPUT_DIR, "terrain_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    print("✅ Terrain Intelligence completed successfully!")

if __name__ == "__main__":
    run_terrain_engine()
