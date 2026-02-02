import os
import rasterio
from scripts.ai.Vegetation.density import vegetation_density
from scripts.ai.Vegetation.zones import generate_zones


def run_vegetation():
    os.makedirs("data/ai", exist_ok=True)

    with rasterio.open("data/ai/landuse.tif") as src:
        landuse = src.read(1)
        meta = src.meta

    density = vegetation_density(landuse)

    meta.update(dtype=rasterio.float32)

    with rasterio.open("data/ai/vegetation_density.tif", "w", **meta) as dst:
        dst.write(density, 1)

    generate_zones("data/ai/tree_zones.geojson")

    print("✅ Module 7 completed: Vegetation maps generated")