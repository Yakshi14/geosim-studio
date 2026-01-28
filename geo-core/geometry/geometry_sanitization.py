"""
MODULE 3 — GEOMETRY SANITIZATION ENGINE
-------------------------------------
Goal:
Prevent engine crashes by fixing or rejecting unsafe geometries.

Input:
C:\\Users\\TEJAS\\Desktop\\geo_project\\data\\normalized\\
    - buildings_utm.geojson
    - roads_utm.geojson

Output:
C:\\Users\\TEJAS\\Desktop\\geo_project\\data\\clean\\
    - buildings_clean.geojson
    - roads_clean.geojson

Rules:
- No CRS logic
- Units = meters
- Invalid geometry = DROP
"""

import os
import geopandas as gpd
from shapely.validation import make_valid

# ==================================================
# ABSOLUTE PATH CONFIG (FIXED FOR YOUR MACHINE)
# ==================================================

PROJECT_ROOT = r"C:\Users\TEJAS\Desktop\geo_project"

INPUT_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "clean")

BUILDINGS_IN = os.path.join(INPUT_DIR, "buildings_utm.geojson")
ROADS_IN = os.path.join(INPUT_DIR, "roads_utm.geojson")

BUILDINGS_OUT = os.path.join(OUTPUT_DIR, "buildings_clean.geojson")
ROADS_OUT = os.path.join(OUTPUT_DIR, "roads_clean.geojson")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================================================
# ENGINE-SAFE CONSTANTS
# ==================================================

BUILDING_SIMPLIFY_TOLERANCE = 0.4   # meters
ROAD_SIMPLIFY_TOLERANCE = 0.8       # meters
DEFAULT_BUILDING_HEIGHT = 10.0      # meters
MIN_BUILDING_AREA = 1.0             # m²
MIN_BUILDING_HEIGHT = 1.0           # meters

# ==================================================
# GEOMETRY FIXING
# ==================================================

def fix_geometry(geom):
    if geom is None or geom.is_empty:
        return None

    if geom.is_valid:
        return geom

    try:
        fixed = make_valid(geom)
        if fixed.is_valid:
            return fixed
    except Exception:
        pass

    try:
        fixed = geom.buffer(0)
        if fixed.is_valid:
            return fixed
    except Exception:
        pass

    return None  # HARD REJECT

# ==================================================
# HEIGHT RESOLUTION
# ==================================================

def resolve_height(row):
    if "height" in row and row["height"]:
        try:
            return float(row["height"])
        except Exception:
            pass

    if "levels" in row and row["levels"]:
        try:
            return float(row["levels"]) * 3.0
        except Exception:
            pass

    return DEFAULT_BUILDING_HEIGHT

# ==================================================
# SANITIZATION PIPELINES
# ==================================================

def sanitize_buildings(gdf):
    initial_count = len(gdf)

    gdf = gdf[~gdf.geometry.is_empty]
    gdf["geometry"] = gdf.geometry.apply(fix_geometry)
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.geometry.is_valid]

    gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])]

    gdf["geometry"] = gdf.geometry.simplify(
        tolerance=BUILDING_SIMPLIFY_TOLERANCE,
        preserve_topology=True
    )

    gdf["area"] = gdf.geometry.area
    gdf = gdf.sort_values("area", ascending=False)
    gdf = gdf.drop_duplicates(subset="geometry")

    gdf["height_m"] = gdf.apply(resolve_height, axis=1)

    if "building" not in gdf.columns:
        gdf["building"] = "generic"

    gdf = gdf[
        (gdf.geometry.area > MIN_BUILDING_AREA) &
        (gdf["height_m"] > MIN_BUILDING_HEIGHT)
    ]

    print(f"[BUILDINGS] {initial_count} → {len(gdf)} after sanitization")
    return gdf.drop(columns=["area"], errors="ignore")


def sanitize_roads(gdf):
    initial_count = len(gdf)

    gdf = gdf[~gdf.geometry.is_empty]
    gdf["geometry"] = gdf.geometry.apply(fix_geometry)
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.geometry.is_valid]

    gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])]

    gdf["geometry"] = gdf.geometry.simplify(
        tolerance=ROAD_SIMPLIFY_TOLERANCE,
        preserve_topology=True
    )

    print(f"[ROADS] {initial_count} → {len(gdf)} after sanitization")
    return gdf

# ==================================================
# MAIN
# ==================================================

def main():
    print("=== MODULE 3: GEOMETRY SANITIZATION ENGINE ===")

    print("Checking input files...")
    print("Buildings exists:", os.path.exists(BUILDINGS_IN))
    print("Roads exists:", os.path.exists(ROADS_IN))

    if not os.path.exists(BUILDINGS_IN) or not os.path.exists(ROADS_IN):
        raise FileNotFoundError("❌ Input files not found. Check paths.")

    print("Loading data...")
    buildings = gpd.read_file(BUILDINGS_IN)
    roads = gpd.read_file(ROADS_IN)

    print("Sanitizing buildings...")
    buildings_clean = sanitize_buildings(buildings)

    print("Sanitizing roads...")
    roads_clean = sanitize_roads(roads)

    print("Saving outputs...")
    buildings_clean.to_file(BUILDINGS_OUT, driver="GeoJSON")
    roads_clean.to_file(ROADS_OUT, driver="GeoJSON")

    print("✅ Geometry sanitization complete.")
    print("Output written to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
