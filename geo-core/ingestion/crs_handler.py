"""
CRS Handler Module
------------------
- Detects CRS
- Logs CRS info
- Reprojects to common CRS if required
- Saves output in processed folder

Supports:
- Raster data (DEM, Satellite) using rasterio
- Vector data (OSM) using geopandas
"""

from pathlib import Path
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd


# --------------------------------------------------
# Project-wide common CRS
# --------------------------------------------------
TARGET_CRS = "EPSG:4326"


# --------------------------------------------------
# Raster CRS handler (DEM, Satellite)
# --------------------------------------------------
def handle_raster_crs(input_path: str, output_path: str):
    input_path = Path(input_path)
    output_path = Path(output_path)

    try:
        with rasterio.open(input_path) as src:
            print(f"[Raster] File: {input_path.name}")
            print(f"[Raster] Original CRS: {src.crs}")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # CRS MATCH then COPY
            if src.crs == TARGET_CRS:
                metadata = src.meta.copy()

                with rasterio.open(output_path, "w", **metadata) as dst:
                    for band in range(1, src.count + 1):
                        dst.write(src.read(band), band)

                print(f"[Raster] Copied file saved at: {output_path}")
                print("-" * 50)
                return

            # CRS DIFFERENT then REPROJECT
            transform, width, height = calculate_default_transform(
                src.crs, TARGET_CRS, src.width, src.height, *src.bounds
            )

            metadata = src.meta.copy()
            metadata.update({
                "crs": TARGET_CRS,
                "transform": transform,
                "width": width,
                "height": height
            })

            with rasterio.open(output_path, "w", **metadata) as dst:
                for band in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, band),
                        destination=rasterio.band(dst, band),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=TARGET_CRS,
                        resampling=Resampling.nearest
                    )

            print(f"[Raster] Reprojected file saved at: {output_path}")
            print("-" * 50)

    except rasterio.errors.RasterioIOError as e:
        print(f"[Raster][SKIPPED] {input_path.name} → {e}")
        print("-" * 50)



# --------------------------------------------------
# Vector CRS handler (OSM)
# --------------------------------------------------
def handle_vector_crs(input_path: str, output_path: str):
    input_path = Path(input_path)
    output_path = Path(output_path)

    gdf = gpd.read_file(input_path)

    print(f"[Vector] File: {input_path.name}")
    print(f"[Vector] Original CRS: {gdf.crs}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # CRS MATCH then COPY
    if gdf.crs == TARGET_CRS:
        gdf.to_file(output_path, driver="GeoJSON")
        print(f"[Vector] Copied file saved at: {output_path}")
        print("-" * 50)
        return

    # CRS DIFFERENT then REPROJECT
    gdf = gdf.to_crs(TARGET_CRS)
    gdf.to_file(output_path, driver="GeoJSON")

    print(f"[Vector] Reprojected file saved at: {output_path}")
    print("-" * 50)

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[1]

    RAW_DIR = BASE_DIR / "data" / "raw"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"

    dem_in = RAW_DIR / "dem" / "mumbai_dem.tif"
    dem_out = PROCESSED_DIR / "dem" / "mumbai_dem_4326.tif"

    if dem_in.exists():
        handle_raster_crs(dem_in, dem_out)
    else:
        print("[DEM] Input file not found")

    sat_dir = RAW_DIR / "satellite"
    sat_files = list(sat_dir.glob("*.jp2")) + list(sat_dir.glob("*.tif"))

    for sat_file in sat_files:
        sat_out = PROCESSED_DIR / "satellite" / f"{sat_file.stem}_4326.tif"
        handle_raster_crs(sat_file, sat_out)

    if not sat_files:
        print("[Satellite] No satellite files found")

    osm_dir = RAW_DIR / "osm"
    vector_files = list(osm_dir.glob("*.geojson"))

    for vec in vector_files:
        vec_out = PROCESSED_DIR / "osm" / vec.name
        handle_vector_crs(vec, vec_out)

    if not vector_files:
        print("[OSM] No vector files found")
