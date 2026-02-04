from pathlib import Path
import geopandas as gpd
import pandas as pd   # IMPORTANT FIX
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
FEATURES_DIR = BASE_DIR / "data" / "features"
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------
# Helper Functions
# ------------------------------

def estimate_building_height(row):
    """Estimate height using footprint area (Phase 1 heuristic)."""
    area = row.geometry.area  # in sq meters (UTM)

    if area < 50:
        return 6.0      # small hut / shed
    elif area < 200:
        return 10.0     # small house
    elif area < 1000:
        return 18.0     # apartment
    else:
        return 30.0     # large building

def classify_building_usage(tags):
    """Robust classification from OSM tags (safe for missing values)."""

    if tags is None:
        return "unknown"

    t = str(tags).lower()

    if "residential" in t:
        return "residential"
    elif "commercial" in t:
        return "commercial"
    elif "industrial" in t:
        return "industrial"
    else:
        return "mixed"

def assign_lod(height):
    """Assign Level of Detail (LOD)."""
    if height < 10:
        return "LOD1"
    elif height < 25:
        return "LOD2"
    else:
        return "LOD3"

# ------------------------------
# Main Enrichment Function
# ------------------------------

def enrich_buildings():
    input_path = NORMALIZED_DIR / "buildings_utm.geojson"
    output_path = FEATURES_DIR / "buildings_enriched.geojson"

    if not input_path.exists():
        print("❌ buildings_utm.geojson not found. Run normalization first.")
        return

    gdf = gpd.read_file(input_path)

    print(f"Enriching {len(gdf)} buildings...")

    # ---- FIX: Handle missing 'tags' safely (CORRECT) ----
    if "tags" in gdf.columns:
        tags_series = gdf["tags"]
    else:
        print("⚠️ No 'tags' column found — using fallback classification.")
        tags_series = pd.Series(["unknown"] * len(gdf), index=gdf.index)

    # ---- Apply enrichments ----
    gdf["height_m"] = gdf.apply(estimate_building_height, axis=1)
    gdf["usage"] = tags_series.apply(classify_building_usage)
    gdf["lod"] = gdf["height_m"].apply(assign_lod)

    # Keep clean Phase-1 output only
    keep_cols = ["height_m", "usage", "lod", "geometry"]
    existing = [c for c in keep_cols if c in gdf.columns]
    gdf = gdf[existing]

    gdf.to_file(output_path, driver="GeoJSON")

    print(f"✅ Saved: {output_path}")
