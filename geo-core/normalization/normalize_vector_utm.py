# scripts/normalization/normalize_vector_utm.py
from pathlib import Path
import geopandas as gpd
from .utm_utils import get_utm_crs_from_latlon

BASE_DIR = Path(__file__).resolve().parents[2]

INPUTS = {
    "buildings": BASE_DIR / "data/processed/osm/mumbai_buildings.geojson",
    "roads": BASE_DIR / "data/processed/osm/mumbai_roads.geojson",
}

OUTPUT_DIR = BASE_DIR / "data/normalized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def normalize_vector(name, path):
    gdf = gpd.read_file(path)

    # ── CHANGE APPLIED HERE ──
    bounds = gdf.total_bounds
    minx, miny, maxx, maxy = bounds

    lon = (minx + maxx) / 2
    lat = (miny + maxy) / 2

    utm_crs = get_utm_crs_from_latlon(lat, lon)
    # ────────────────────────

    gdf_utm = gdf.to_crs(utm_crs)

    out_path = OUTPUT_DIR / f"{name}_utm.geojson"
    gdf_utm.to_file(out_path, driver="GeoJSON")

    print(f"✅ {name.upper()} normalized → {utm_crs}")

if __name__ == "__main__":
    for name, path in INPUTS.items():
        normalize_vector(name, path)
