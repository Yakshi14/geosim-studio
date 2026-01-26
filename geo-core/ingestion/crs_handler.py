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

    with rasterio.open(input_path) as src:
        print(f"[Raster] File: {input_path.name}")
        print(f"[Raster] Original CRS: {src.crs}")

        # If CRS already matches target
        if src.crs == TARGET_CRS:
            print("[Raster] CRS already matches target. No reprojection needed.")
            return

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

        output_path.parent.mkdir(parents=True, exist_ok=True)

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


# --------------------------------------------------
# Vector CRS handler (OSM)
# --------------------------------------------------
def handle_vector_crs(input_path: str, output_path: str):
    input_path = Path(input_path)
    output_path = Path(output_path)

    gdf = gpd.read_file(input_path)

    print(f"[Vector] File: {input_path.name}")
    print(f"[Vector] Original CRS: {gdf.crs}")

    if gdf.crs == TARGET_CRS:
        print("[Vector] CRS already matches target. No reprojection needed.")
        return

    gdf = gdf.to_crs(TARGET_CRS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GeoJSON")

    print(f"[Vector] Reprojected file saved at: {output_path}")
    print("-" * 50)
