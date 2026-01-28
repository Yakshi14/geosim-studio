# --------------------------------------------------
# Terrain Intelligence Engine (NO GDAL / osgeo)
# --------------------------------------------------

import os
import numpy as np
import rasterio


# --------------------------------------------------
# CONFIG (FIXED PATH)
# --------------------------------------------------

DEM_PATH = r"C:\Users\TEJAS\Desktop\geo_project\data\processed\dem\mumbai_dem.tif"
OUTPUT_DIR = r"C:\Users\TEJAS\Desktop\geo_project\data\terrain"

# sanity checks
if not os.path.exists(DEM_PATH):
    raise FileNotFoundError(f"DEM file not found:\n{DEM_PATH}")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------------------------------
# LOAD DEM (BUG-FREE)
# --------------------------------------------------

def load_dem(path):
    with rasterio.open(path) as src:
        dem = src.read(1).astype("float32")
        transform = src.transform
        crs = src.crs
        profile = src.profile
        nodata = src.nodata

    if nodata is not None:
        dem[dem == nodata] = np.nan

    return dem, transform, crs, profile


# --------------------------------------------------
# TERRAIN COMPUTATIONS
# --------------------------------------------------

def compute_slope_aspect(dem, transform):
    # pixel resolution
    xres = transform.a
    yres = -transform.e

    # gradients
    dz_dx = np.gradient(dem, axis=1) / xres
    dz_dy = np.gradient(dem, axis=0) / yres

    # slope (degrees)
    slope = np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)))

    # aspect (degrees, 0–360)
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
# MAIN PIPELINE
# --------------------------------------------------

def run_terrain_engine():
    print("▶ Loading DEM...")
    dem, transform, crs, profile = load_dem(DEM_PATH)

    print("▶ Computing slope & aspect...")
    slope, aspect = compute_slope_aspect(dem, transform)

    print("▶ Saving outputs...")
    save_raster(dem, profile, os.path.join(OUTPUT_DIR, "elevation.tif"))
    save_raster(slope, profile, os.path.join(OUTPUT_DIR, "slope.tif"))
    save_raster(aspect, profile, os.path.join(OUTPUT_DIR, "aspect.tif"))

    print("✅ Terrain Intelligence completed successfully!")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    run_terrain_engine()
