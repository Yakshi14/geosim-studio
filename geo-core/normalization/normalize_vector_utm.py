from pathlib import Path
import geopandas as gpd
from utm_utils import get_utm_crs_from_latlon

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_OSM_DIR = BASE_DIR / "data/processed/osm"
OUTPUT_DIR = BASE_DIR / "data/normalized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def normalize_vector(input_path: Path):
    if not input_path.exists():
        print(f"Missing file: {input_path}")
        return

    gdf = gpd.read_file(input_path)

    if gdf.empty:
        print(f"Empty file skipped: {input_path.name}")
        return

    minx, miny, maxx, maxy = gdf.total_bounds
    lon = (minx + maxx) / 2
    lat = (miny + maxy) / 2

    utm_crs = get_utm_crs_from_latlon(lat, lon)

    gdf_utm = gdf.to_crs(utm_crs)

    out_path = OUTPUT_DIR / f"{input_path.stem}_utm.geojson"
    gdf_utm.to_file(out_path, driver="GeoJSON")

    print(f"{input_path.stem.upper()} normalized → {utm_crs}")

if __name__ == "__main__":

    osm_files = list(PROCESSED_OSM_DIR.glob("*.geojson"))

    if not osm_files:
        print("No processed OSM files found")
    else:
        for osm in osm_files:
            normalize_vector(osm)
