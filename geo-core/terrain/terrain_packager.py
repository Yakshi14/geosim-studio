"""
MODULE 9 — TERRAIN PACKAGING (FINAL PHASE 1 OUTPUT)

Takes normalized DEM and produces:
- elevation.tif
- slope.tif
- aspect.tif
- terrain_stats.json

Output:
data/phase1_output/terrain/
"""

from pathlib import Path
import json
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from scipy.ndimage import sobel

BASE_DIR = Path(__file__).resolve().parents[2]

NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
PHASE1_TERRAIN = BASE_DIR / "data" / "phase1_output" / "terrain"
PHASE1_TERRAIN.mkdir(parents=True, exist_ok=True)

def load_dem():
    """Load the normalized DEM (UTM preferred)"""
    dem_files = list(NORMALIZED_DIR.glob("*dem*.tif"))

    if not dem_files:
        raise FileNotFoundError("No normalized DEM found in data/normalized")

    # Prefer UTM version if exists
    for f in dem_files:
        if "utm" in f.name.lower():
            return f

    return dem_files[0]  # fallback

def compute_slope_aspect(dem_array, transform):
    """Compute slope and aspect from DEM"""

    # Pixel size
    xres = transform.a
    yres = abs(transform.e)

    dzdx = sobel(dem_array, axis=1) / (8 * xres)
    dzdy = sobel(dem_array, axis=0) / (8 * yres)

    slope = np.arctan(np.sqrt(dzdx**2 + dzdy**2)) * (180 / np.pi)

    aspect = np.arctan2(dzdy, -dzdx) * (180 / np.pi)
    aspect = np.mod(aspect + 360, 360)

    return slope, aspect

def save_raster(array, meta, out_path):
    meta = meta.copy()
    meta.update({
        "count": 1,
        "dtype": rasterio.float32
    })

    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(array.astype(np.float32), 1)

def generate_terrain_stats(dem_array):
    return {
        "min_elevation": float(np.nanmin(dem_array)),
        "max_elevation": float(np.nanmax(dem_array)),
        "mean_elevation": float(np.nanmean(dem_array)),
        "std_elevation": float(np.nanstd(dem_array))
    }

def package_terrain():
    print("\n=== MODULE 9: TERRAIN PACKAGING ===")

    dem_path = load_dem()
    print(f"Using DEM: {dem_path}")

    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        meta = src.meta

    slope, aspect = compute_slope_aspect(dem, meta["transform"])

    # Save final terrain outputs
    save_raster(dem, meta, PHASE1_TERRAIN / "elevation.tif")
    save_raster(slope, meta, PHASE1_TERRAIN / "slope.tif")
    save_raster(aspect, meta, PHASE1_TERRAIN / "aspect.tif")

    stats = generate_terrain_stats(dem)

    with open(PHASE1_TERRAIN / "terrain_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print("Saved to data/phase1_output/terrain/")
    print("✔ elevation.tif")
    print("✔ slope.tif")
    print("✔ aspect.tif")
    print("✔ terrain_stats.json")

if __name__ == "__main__":
    package_terrain()
