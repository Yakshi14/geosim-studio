# geo-core/normalization/normalize_raster_utm.py

from pathlib import Path
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from utm_utils import get_utm_crs_from_latlon

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

def normalize_raster_to_utm(input_path: Path, reference_path: Path = None):
    if not input_path.exists():
        print(f"[MISSING] {input_path}")
        return None

    with rasterio.open(input_path) as src:
        lon = (src.bounds.left + src.bounds.right) / 2
        lat = (src.bounds.bottom + src.bounds.top) / 2
        target_crs = get_utm_crs_from_latlon(lat, lon)

        # If reference raster exists, MATCH ITS GRID
        if reference_path and reference_path.exists():
            with rasterio.open(reference_path) as ref:
                transform = ref.transform
                width = ref.width
                height = ref.height
        else:
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

        output_path = NORMALIZED_DIR / f"{input_path.stem}_utm.tif"

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

        print(f"[NORMALIZED] {input_path.name} → {target_crs}")
        return output_path


if __name__ == "__main__":
    dem_dir = PROCESSED_DIR / "dem"
    sat_dir = PROCESSED_DIR / "satellite"

    dem_files = list(dem_dir.glob("*.tif"))
    sat_files = list(sat_dir.glob("*.tif"))

    if not dem_files:
        print("❌ No DEM found in data/processed/dem")
        exit(1)

    # STEP 1 — Normalize DEM first (MASTER GRID)
    print("\n=== Normalizing DEM (Master Grid) ===")
    dem_utm = normalize_raster_to_utm(dem_files[0])

    # STEP 2 — Normalize Satellite to MATCH DEM
    print("\n=== Normalizing Satellite to DEM Grid ===")
    for sat in sat_files:
        normalize_raster_to_utm(sat, reference_path=dem_utm)

    print("\n✅ Raster normalization completed.")
