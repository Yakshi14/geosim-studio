import os
import rasterio
from .density import vegetation_density
from .zones import generate_zones

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)

AI_DIR = os.path.join(BASE_DIR, "data", "ai")
os.makedirs(AI_DIR, exist_ok=True)


def run_vegetation():
    landuse_path = os.path.join(AI_DIR, "landuse.tif")

    with rasterio.open(landuse_path) as src:
        landuse = src.read(1)
        meta = src.meta.copy()

    density = vegetation_density(landuse)

    meta.update(dtype=rasterio.float32, count=1)

    density_path = os.path.join(AI_DIR, "vegetation_density.tif")
    with rasterio.open(density_path, "w", **meta) as dst:
        dst.write(density, 1)

    zones_path = os.path.join(AI_DIR, "tree_zones.geojson")
    generate_zones(zones_path)

    print("✅ Module 7 completed: Vegetation maps generated")


if __name__ == "__main__":
    run_vegetation()
