from pathlib import Path
import geopandas as gpd
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
FEATURES_DIR = BASE_DIR / "data" / "features"
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------
# Helper Functions
# ------------------------------

def estimate_road_width(tags):
    """Estimate width based on road type (robust)."""

    if tags is None:
        return 5.0  # default

    t = str(tags).lower()

    if "motorway" in t:
        return 12.0
    elif "primary" in t:
        return 10.0
    elif "secondary" in t:
        return 8.0
    elif "residential" in t:
        return 6.0
    else:
        return 5.0  # fallback

def classify_road_type(tags):
    """Extract road type safely."""
    if isinstance(tags, dict) and "highway" in tags:
        return tags["highway"]
    return "unknown"

def compute_navigation_weight(road_type):
    """Lower weight = easier for AI navigation."""

    if road_type in ["motorway", "primary"]:
        return 0.3
    elif road_type in ["secondary", "tertiary"]:
        return 0.5
    elif road_type == "residential":
        return 0.7
    else:
        return 0.9

# ------------------------------
# Main Enrichment Function
# ------------------------------

def enrich_roads():
    input_path = NORMALIZED_DIR / "roads_utm.geojson"
    output_path = FEATURES_DIR / "roads_enriched.geojson"

    if not input_path.exists():
        print("❌ roads_utm.geojson not found. Run normalization first.")
        return

    gdf = gpd.read_file(input_path)

    print(f"Enriching {len(gdf)} roads...")

    # ---- Handle missing tags ----
    if "tags" in gdf.columns:
        tags_series = gdf["tags"]
    else:
        print("⚠️ No 'tags' column found — using fallback.")
        tags_series = pd.Series([None] * len(gdf), index=gdf.index)

    gdf["width_m"] = tags_series.apply(estimate_road_width)
    gdf["road_type"] = tags_series.apply(classify_road_type)
    gdf["nav_weight"] = gdf["road_type"].apply(compute_navigation_weight)

    # Keep clean output
    keep_cols = ["width_m", "road_type", "nav_weight", "geometry"]
    existing = [c for c in keep_cols if c in gdf.columns]
    gdf = gdf[existing]

    gdf.to_file(output_path, driver="GeoJSON")

    print(f"✅ Saved: {output_path}")
