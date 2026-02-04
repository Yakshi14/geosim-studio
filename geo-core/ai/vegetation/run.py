from pathlib import Path
import rasterio
import numpy as np

from vegetation_model import compute_vegetation_density
from zones import generate_tree_zones

BASE_DIR = Path(__file__).resolve().parents[3]
AI_DIR = BASE_DIR / "data" / "ai"

def save_raster(array, reference_meta, out_path):
    meta = reference_meta.copy()
    meta.update({
        "driver": "GTiff",
        "count": 1,
        "dtype": "float32",
        "compress": "lzw"
    })

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(array.astype("float32"), 1)

def run_vegetation():
    print("\n=== MODULE 7 — AI VEGETATION INTELLIGENCE ===")

    landuse_path = AI_DIR / "landuse.tif"

    if not landuse_path.exists():
        print("❌ ERROR: landuse.tif not found. Run Module 6 first.")
        return

    print("Reading:", landuse_path)

    with rasterio.open(landuse_path) as src:
        landuse = src.read(1)
        meta = src.meta.copy()

    # Compute vegetation density
    vegetation_density = compute_vegetation_density(landuse)

    # Save vegetation density map
    veg_path = AI_DIR / "vegetation_density.tif"
    save_raster(vegetation_density, meta, veg_path)
    print("Saved:", veg_path)

    # Generate tree zones
    generate_tree_zones()

    print("✅ Module 7 completed.")

if __name__ == "__main__":
    run_vegetation()
