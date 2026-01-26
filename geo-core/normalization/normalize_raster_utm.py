#Convert DEM & satellite → meters
#Align grid
#Output single UTM raster
# scripts/normalization/normalize_raster_utm.py
from pathlib import Path
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pyproj import Transformer
from .utm_utils import get_utm_crs_from_latlon

BASE_DIR = Path(__file__).resolve().parents[2]

INPUTS = {
    "dem": BASE_DIR / "data/processed/dem/mumbai_dem_4326.tif",
    "satellite": BASE_DIR / "data/processed/satellite/mumbai_satellite_4326.tif",
}

OUTPUT_DIR = BASE_DIR / "data/normalized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def normalize_raster(name, input_path):
    with rasterio.open(input_path) as src:
        lon, lat = src.bounds.left, src.bounds.bottom
        target_crs = get_utm_crs_from_latlon(lat, lon)

        transform, width, height = calculate_default_transform(
            src.crs,
            target_crs,
            src.width,
            src.height,
            *src.bounds
        )

        meta = src.meta.copy()
        meta.update({
            "crs": target_crs,
            "transform": transform,
            "width": width,
            "height": height
        })

        output_path = OUTPUT_DIR / f"{name}_utm.tif"

        with rasterio.open(output_path, "w", **meta) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.bilinear
                )

        print(f"✅ {name.upper()} normalized → {target_crs}")

if __name__ == "__main__":
    for name, path in INPUTS.items():
        normalize_raster(name, path)