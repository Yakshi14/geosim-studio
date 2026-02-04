# geo-core/normalization/normalize_vector_utm.py

from pathlib import Path
import geopandas as gpd
from utm_utils import get_utm_crs_from_latlon

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

def normalize_vector_to_utm(input_path: Path):
    gdf = gpd.read_file(input_path)

    print(f"[VECTOR] {input_path.name}")
    print(f"Original CRS: {gdf.crs}")

    # Use centroid to pick UTM zone
    centroid = gdf.geometry.unary_union.centroid
    lon, lat = centroid.x, centroid.y

    target_crs = get_utm_crs_from_latlon(lat, lon)

    gdf_utm = gdf.to_crs(target_crs)

    output_path = NORMALIZED_DIR / f"{input_path.stem}_utm.geojson"
    gdf_utm.to_file(output_path, driver="GeoJSON")

    print(f"[NORMALIZED] Saved → {output_path}\n")


if __name__ == "__main__":
    osm_dir = PROCESSED_DIR / "osm"
    vector_files = list(osm_dir.glob("*.geojson"))

    if not vector_files:
        print("❌ No vector files found in data/processed/osm")
    else:
        for vec in vector_files:
            normalize_vector_to_utm(vec)

    print("✅ Vector normalization completed.")
