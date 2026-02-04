from pathlib import Path
import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parents[2]
FEATURES_DIR = BASE_DIR / "data" / "features"

def check_geometry_validity():
    """
    Ensure no broken geometries in enriched features.
    """
    results = {}

    for fname in ["buildings_enriched.geojson", "roads_enriched.geojson"]:
        path = FEATURES_DIR / fname

        if not path.exists():
            results[fname] = "MISSING"
            continue

        gdf = gpd.read_file(path)
        invalid_count = (~gdf.is_valid).sum()

        results[fname] = {
            "status": "PASS" if invalid_count == 0 else "REVIEW",
            "invalid_geometries": int(invalid_count),
            "total_features": int(len(gdf))
        }

    return results

def check_attribute_completeness():
    """
    Ensure required attributes exist in enriched features.
    """
    results = {}

    # Required fields per your Module 5 spec
    building_required = {"height_est", "usage", "lod"}
    road_required = {"width_est", "road_type", "nav_weight"}

    # ---- Buildings ----
    b_path = FEATURES_DIR / "buildings_enriched.geojson"
    if not b_path.exists():
        results["buildings"] = "MISSING"
    else:
        gdf = gpd.read_file(b_path)
        missing = building_required - set(gdf.columns)

        results["buildings"] = {
            "status": "PASS" if not missing else "REVIEW",
            "missing_fields": list(missing)
        }

    # ---- Roads ----
    r_path = FEATURES_DIR / "roads_enriched.geojson"
    if not r_path.exists():
        results["roads"] = "MISSING"
    else:
        gdf = gpd.read_file(r_path)
        missing = road_required - set(gdf.columns)

        results["roads"] = {
            "status": "PASS" if not missing else "REVIEW",
            "missing_fields": list(missing)
        }

    return results
