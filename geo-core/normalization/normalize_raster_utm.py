#Convert DEM & satellite → meters
#Align grid
#Output single UTM raster
from pathlib import Path
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from utm_utils import get_utm_crs_from_latlon

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "data" / "normalized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def normalize_raster(input_path: Path):
    if not input_path.exists():
        print(f"Missing file: {input_path}")
        return

    with rasterio.open(input_path) as src:
        lon = (src.bounds.left + src.bounds.right) / 2
        lat = (src.bounds.bottom + src.bounds.top) / 2
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

        output_name = f"{input_path.stem}.tif"
        output_path = OUTPUT_DIR / output_name

        with rasterio.open(output_path, "w", **meta) as dst:
            for band in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, band),
                    destination=rasterio.band(dst, band),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.bilinear
                )

        print(f" {input_path.name} → {target_crs}")

if __name__ == "__main__":
    dem_dir = PROCESSED_DIR / "dem"
    dem_files = list(dem_dir.glob("*.tif"))

    if not dem_files:
        print("No DEM rasters found")
    else:
        for dem in dem_files:
            normalize_raster(dem)

    sat_dir = PROCESSED_DIR / "satellite"
    sat_files = list(sat_dir.glob("*.tif"))

    if not sat_files:
        print("No satellite rasters found")
    else:
        for sat in sat_files:
            normalize_raster(sat)

