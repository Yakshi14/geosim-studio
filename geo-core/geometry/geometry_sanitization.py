"""
MODULE 3 — GEOMETRY SANITIZATION ENGINE
-------------------------------------------------------------
Goal:
Prevent engine crashes AND remove visual clutter from tiny buildings.
Intelligent height assignment + aggressive size filtering.

Input:
GEOSIM-STUDIO/data/normalized/
    - *.geojson (all vector layers)

Output:
GEOSIM-STUDIO/data/clean/
    - *_clean.geojson

Rules:
- No CRS logic
- Units = meters
- Invalid geometry = DROP
- Small buildings = DROP (configurable)
- Smart height defaults based on building type/area
"""

import os
from pathlib import Path
import geopandas as gpd
from shapely.validation import make_valid
import random

# ==================================================
# PATH CONFIG
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "clean")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================================================
# ENGINE-SAFE CONSTANTS
# ==================================================

BUILDING_SIMPLIFY_TOLERANCE = 0.4   # meters
ROAD_SIMPLIFY_TOLERANCE = 0.8       # meters

# ==================================================
# 🔧 CONFIGURABLE FILTERING THRESHOLDS
# ==================================================

MIN_BUILDING_AREA = 10.0       # m² - Drops sheds, kiosks, small structures
MIN_BUILDING_HEIGHT = 2.5      # m  - Drops very low structures

MIN_WATER_AREA = 50.0          # m² - Drops tiny puddles / noise polygons

# ==================================================

WATER_SIMPLIFY_TOLERANCE = 1.2  # meters — coarser than buildings, water edges are softer

# ==================================================
# WATER DETECTION — OSM TAG SETS
# ==================================================
# Any feature whose tags match ANY of these sets is classified as water
# and routed to sanitize_water() instead of sanitize_polygons().

WATER_NATURAL_TAGS  = {"water", "wetland", "bay", "spring"}
WATER_WATERWAY_TAGS = {"river", "stream", "canal", "ditch", "drain"}
WATER_LANDUSE_TAGS  = {"reservoir", "basin"}

# ==================================================

# Height variation range (±%)
HEIGHT_VARIATION_PERCENT = 0.15     # ±15% variation for realism

# ==================================================
# SMART HEIGHT DEFAULTS BY BUILDING TYPE
# ==================================================

BUILDING_TYPE_HEIGHTS = {
    # Residential
    "apartments": 18.0,         # ~6 floors
    "house": 6.0,               # ~2 floors
    "residential": 12.0,        # ~4 floors
    "bungalow": 4.5,           # ~1.5 floors
    "hut": 3.0,                # Single story low
    "detached": 7.5,           # ~2.5 floors
    "terrace": 9.0,            # ~3 floors
    
    # Commercial/Retail
    "commercial": 15.0,         # ~5 floors
    "retail": 12.0,            # ~4 floors
    "office": 21.0,            # ~7 floors
    "shop": 9.0,               # ~3 floors
    "supermarket": 6.0,        # Single/double story
    "mall": 18.0,              # ~6 floors
    
    # Industrial/Storage
    "industrial": 8.0,          # Single story high ceiling
    "warehouse": 8.0,           # Single story high ceiling
    "factory": 10.0,           # Single story high ceiling
    "storage_tank": 12.0,      # Tall tanks
    "silo": 20.0,              # Very tall
    
    # Institutional
    "school": 12.0,            # ~4 floors
    "college": 15.0,           # ~5 floors
    "university": 18.0,        # ~6 floors
    "hospital": 21.0,          # ~7 floors
    "government": 18.0,        # ~6 floors
    "civic": 15.0,             # ~5 floors
    "public": 12.0,            # ~4 floors
    
    # Religious
    "cathedral": 30.0,         # Tall
    "church": 15.0,            # Medium-tall
    "temple": 12.0,            # Medium
    "mosque": 18.0,            # Tall with minaret
    "synagogue": 12.0,         # Medium
    "shrine": 6.0,             # Low
    
    # Transportation
    "train_station": 15.0,     # ~5 floors
    "transportation": 12.0,    # ~4 floors
    "parking": 9.0,            # ~3 floors (multi-level)
    "garage": 3.0,             # Single story
    
    # Special
    "stadium": 30.0,           # Very tall
    "sports_hall": 12.0,       # High ceiling
    "construction": 10.0,      # Default
    "roof": 3.0,               # Just a roof
    "ruins": 4.0,              # Partial structure
    
    # Default
    "yes": 10.0,               # Generic building
}

# ==================================================
# INPUT DISCOVERY
# ==================================================

def find_all_vectors(input_dir):
    files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith(".geojson")
    ]

    if not files:
        raise FileNotFoundError(
            f"❌ No GeoJSON files found in {input_dir}"
        )

    return files

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
# INTELLIGENT HEIGHT RESOLUTION
# ==================================================

def resolve_height_intelligent(row, area):
    """
    Intelligent height resolution with fallback chain:
    1. Explicit height tag
    2. Building levels × 3m
    3. Building type lookup
    4. Area-based heuristic
    5. Smart default with variation
    """
    
    # PRIORITY 1: Explicit height tag
    if "height" in row and row["height"]:
        try:
            height = float(row["height"])
            if height > 0:
                return height
        except (ValueError, TypeError):
            pass
    
    # PRIORITY 2: Building levels
    levels_col = None
    if "building:levels" in row and row["building:levels"]:
        levels_col = "building:levels"
    elif "levels" in row and row["levels"]:
        levels_col = "levels"
    
    if levels_col:
        try:
            levels = float(row[levels_col])
            if levels > 0:
                return levels * 3.0
        except (ValueError, TypeError):
            pass
    
    # PRIORITY 3: Building type lookup
    building_type = row.get("building", "yes")
    if building_type and building_type in BUILDING_TYPE_HEIGHTS:
        base_height = BUILDING_TYPE_HEIGHTS[building_type]
        variation = random.uniform(
            1 - HEIGHT_VARIATION_PERCENT,
            1 + HEIGHT_VARIATION_PERCENT
        )
        return base_height * variation
    
    # PRIORITY 4: Area-based heuristic
    if area:
        if area > 2000:      # Huge buildings (>2000 m²)
            base_height = 25.0
        elif area > 1000:    # Large buildings (1000-2000 m²)
            base_height = 18.0
        elif area > 500:     # Medium-large (500-1000 m²)
            base_height = 15.0
        elif area > 200:     # Medium (200-500 m²)
            base_height = 12.0
        elif area > 50:      # Small-medium (50-200 m²)
            base_height = 9.0
        elif area > 10:      # Small (10-50 m²)
            base_height = 6.0
        else:                # Tiny (<10 m²)
            base_height = 4.0
        
        variation = random.uniform(
            1 - HEIGHT_VARIATION_PERCENT,
            1 + HEIGHT_VARIATION_PERCENT
        )
        return base_height * variation
    
    # PRIORITY 5: Final fallback with variation
    default_height = 10.0
    variation = random.uniform(
        1 - HEIGHT_VARIATION_PERCENT,
        1 + HEIGHT_VARIATION_PERCENT
    )
    return default_height * variation

# ==================================================
# SANITIZATION PIPELINES
# ==================================================

def sanitize_polygons(gdf, use_intelligent_heights=True):
    """
    Sanitize polygon geometries (buildings) with.
    """
    initial_count = len(gdf)
    
    print(f"  Starting with: {initial_count:,} buildings")

    # Filter 1: Remove null/empty geometries
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
    dropped = initial_count - len(gdf)
    if dropped > 0:
        print(f"    Dropped {dropped:,} null/empty geometries")
    
    # Filter 2: Fix invalid geometries
    gdf["geometry"] = gdf.geometry.apply(fix_geometry)
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.geometry.is_valid]
    dropped = initial_count - len(gdf)
    if dropped > 0:
        print(f"    Dropped {dropped:,} invalid geometries")

    # Filter 3: Keep only Polygon/MultiPolygon
    before_geom_filter = len(gdf)
    gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    dropped = before_geom_filter - len(gdf)
    if dropped > 0:
        print(f"    Dropped {dropped:,} non-polygon geometries (Points/Lines)")

    # Simplify geometries for performance
    gdf["geometry"] = gdf.geometry.simplify(
        tolerance=BUILDING_SIMPLIFY_TOLERANCE,
        preserve_topology=True
    )

    # Calculate area
    gdf["area"] = gdf.geometry.area
    
    # Filter 4: Remove tiny buildings (CONFIGURABLE)
    before_area_filter = len(gdf)
    gdf = gdf[gdf["area"] > MIN_BUILDING_AREA]
    dropped = before_area_filter - len(gdf)
    if dropped > 0:
        print(f"    Dropped {dropped:,} tiny buildings (area ≤ {MIN_BUILDING_AREA} m²)")
    
    # Show size distribution
    if len(gdf) > 0:
        tiny = (gdf["area"] < 10).sum()
        small = ((gdf["area"] >= 10) & (gdf["area"] < 50)).sum()
        medium = ((gdf["area"] >= 50) & (gdf["area"] < 200)).sum()
        large = ((gdf["area"] >= 200) & (gdf["area"] < 1000)).sum()
        huge = (gdf["area"] >= 1000).sum()
        print(f"    Size distribution:")
        print(f"      Tiny (<10 m²):        {tiny:6,}")
        print(f"      Small (10-50 m²):     {small:6,}")
        print(f"      Medium (50-200 m²):   {medium:6,}")
        print(f"      Large (200-1000 m²):  {large:6,}")
        print(f"      Huge (>1000 m²):      {huge:6,}")

    # Assign heights
    if use_intelligent_heights:
        gdf["height_m"] = gdf.apply(
            lambda row: resolve_height_intelligent(row, row["area"]),
            axis=1
        )
    else:
        gdf["height_m"] = 10.0  # Simple default
    
    # Filter 5: Remove buildings with invalid heights (CONFIGURABLE)
    before_height_filter = len(gdf)
    gdf = gdf[gdf["height_m"] > MIN_BUILDING_HEIGHT]
    dropped = before_height_filter - len(gdf)
    if dropped > 0:
        print(f"    Dropped {dropped:,} very short buildings (height ≤ {MIN_BUILDING_HEIGHT} m)")

    print(f"  ✓ Final result: {initial_count:,} → {len(gdf):,} ({len(gdf)/initial_count*100:.1f}% kept)")
    
    # Generate statistics
    if len(gdf) > 0:
        print(f"    Height range: {gdf['height_m'].min():.1f}m - {gdf['height_m'].max():.1f}m")
        print(f"    Mean height: {gdf['height_m'].mean():.1f}m")
        print(f"    Median height: {gdf['height_m'].median():.1f}m")
        print(f"    Mean area: {gdf['area'].mean():.1f} m²")
        print(f"    Total footprint: {gdf['area'].sum()/10000:.2f} hectares")
    
    return gdf.drop(columns=["area"], errors="ignore")


# ==================================================
# WATER DETECTION
# ==================================================

def is_water_feature(row) -> bool:
    """
    Return True if OSM tags on this row mark it as a water feature.
    Checks natural, waterway, and landuse columns.
    """
    natural  = str(row.get("natural", "")).strip().lower()
    waterway = str(row.get("waterway", "")).strip().lower()
    landuse  = str(row.get("landuse", "")).strip().lower()

    return (
        natural  in WATER_NATURAL_TAGS  or
        waterway in WATER_WATERWAY_TAGS or
        landuse  in WATER_LANDUSE_TAGS
    )


def split_water_from_polygons(gdf):
    """
    Split a polygon GeoDataFrame into (buildings, water) based on OSM tags.
    Returns two GeoDataFrames; either can be empty.
    """
    water_mask = gdf.apply(is_water_feature, axis=1)
    return gdf[~water_mask].copy(), gdf[water_mask].copy()


# ==================================================
# SANITIZATION PIPELINES — WATER
# ==================================================

def sanitize_water(gdf):
    """
    Sanitize water-body polygon geometries.
    No height assignment.  Drops tiny slivers below MIN_WATER_AREA.
    """
    initial_count = len(gdf)
    print(f"  Starting with: {initial_count:,} water bodies")

    #Remove null/empty geometries
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
    dropped = initial_count - len(gdf)
    if dropped > 0:
        print(f"    Dropped {dropped:,} null/empty geometries")

    #Fix invalid geometries
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.apply(fix_geometry)
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.geometry.is_valid]
    dropped = initial_count - len(gdf)
    if dropped > 0:
        print(f"    Dropped {dropped:,} invalid geometries")

    #Keep only Polygon/MultiPolygon
    before_geom_filter = len(gdf)
    gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    dropped = before_geom_filter - len(gdf)
    if dropped > 0:
        print(f"    Dropped {dropped:,} non-polygon geometries")

    # Simplify (coarser tolerance than buildings)
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.simplify(
        tolerance=WATER_SIMPLIFY_TOLERANCE,
        preserve_topology=True
    )

    # Calculate area
    gdf = gdf.copy()
    gdf["area"] = gdf.geometry.area

    # Filter 4: Remove tiny water slivers
    before_area_filter = len(gdf)
    gdf = gdf[gdf["area"] > MIN_WATER_AREA]
    dropped = before_area_filter - len(gdf)
    if dropped > 0:
        print(f"    Dropped {dropped:,} tiny water slivers (area ≤ {MIN_WATER_AREA} m²)")

    # Size distribution
    if len(gdf) > 0:
        small  = (gdf["area"] < 500).sum()
        medium = ((gdf["area"] >= 500) & (gdf["area"] < 10000)).sum()
        large  = ((gdf["area"] >= 10000) & (gdf["area"] < 100000)).sum()
        huge   = (gdf["area"] >= 100000).sum()
        print(f"    Size distribution:")
        print(f"      Small  (<500 m²):          {small:6,}")
        print(f"      Medium (500-10 000 m²):    {medium:6,}")
        print(f"      Large  (10 000-100 000 m²):{large:6,}")
        print(f"      Huge   (>100 000 m²):      {huge:6,}")

    if len(gdf) > 0:
        print(f"  ✓ Final result: {initial_count:,} → {len(gdf):,} "
              f"({len(gdf)/initial_count*100:.1f}% kept)")
        print(f"    Total surface area: {gdf['area'].sum()/10000:.2f} hectares")
    else:
        print(f"  ✓ Final result: {initial_count:,} → 0")

    return gdf.drop(columns=["area"], errors="ignore")


def sanitize_lines(gdf):
    initial_count = len(gdf)

    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
    gdf["geometry"] = gdf.geometry.apply(fix_geometry)
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.geometry.is_valid]

    gdf = gdf[gdf.geometry.geom_type.isin(
        ["LineString", "MultiLineString"]
    )]

    gdf["geometry"] = gdf.geometry.simplify(
        tolerance=ROAD_SIMPLIFY_TOLERANCE,
        preserve_topology=True
    )

    print(f"  Lines: {initial_count} → {len(gdf)}")
    return gdf


def main():
    print("=" * 70)
    print(" " * 15 + "MODULE 3: GEOMETRY SANITIZATION ENGINE")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  Min building area:   {MIN_BUILDING_AREA} m²")
    print(f"  Min building height: {MIN_BUILDING_HEIGHT} m")
    print(f"  Min water area:      {MIN_WATER_AREA} m²")
    print(f"  Height variation:    ±{HEIGHT_VARIATION_PERCENT*100:.0f}%")
    print("\nFeatures:")
    print("  • Intelligent height assignment based on building type")
    print("  • Area-based height heuristics")
    print("  • Aggressive filtering to remove visual clutter")
    print("  • Height variation for realism")
    print("  • Water body detection & dedicated sanitization pipeline")
    print("")

    vector_files = find_all_vectors(INPUT_DIR)
    print(f"Found {len(vector_files)} vector layers\n")

    total_input = 0
    total_output = 0

    for in_path in vector_files:
        name = Path(in_path).stem
        out_path = os.path.join(OUTPUT_DIR, f"{name}_clean.geojson")

        print(f"▶ Processing: {name}")
        gdf = gpd.read_file(in_path)
        total_input += len(gdf)

        geom_types = set(gdf.geometry.geom_type)

        if geom_types & {"Polygon", "MultiPolygon"}:
            # --- SPLIT water out before anything else ----------------
            buildings_gdf, water_gdf = split_water_from_polygons(gdf)

            # --- Water branch ----------------------------------------
            if not water_gdf.empty:
                print(f"  [water] Detected {len(water_gdf):,} water features by tag")
                water_clean = sanitize_water(water_gdf)

                if not water_clean.empty:
                    water_out = os.path.join(OUTPUT_DIR, "water_clean.geojson")
                    water_clean.to_file(water_out, driver="GeoJSON")
                    total_output += len(water_clean)
                    print(f"  ✔ Saved: {water_out}\n")
                else:
                    print("  ⚠️ Water result empty — not writing file\n")

            # --- Building branch -------------------------------------
            if not buildings_gdf.empty:
                print(f"  [buildings] Processing {len(buildings_gdf):,} building polygons")
                gdf_clean = sanitize_polygons(buildings_gdf, use_intelligent_heights=True)
            else:
                print("  ⚠️ No building polygons remaining after water split")
                continue

        elif geom_types & {"LineString", "MultiLineString"}:
            gdf_clean = sanitize_lines(gdf)

        else:
            print(f"  ⚠️ Skipped unsupported geometry types: {geom_types}")
            continue

        if gdf_clean.empty:
            print("  ⚠️ Result empty — not writing file")
            continue

        gdf_clean.to_file(out_path, driver="GeoJSON")
        total_output += len(gdf_clean)
        print(f"  ✔ Saved: {out_path}\n")

    print("=" * 70)
    print(f"✅ Geometry sanitization complete.")
    print(f"\nSummary:")
    print(f"  Input features:  {total_input:,}")
    print(f"  Output features: {total_output:,}")
    print(f"  Filtered out:    {total_input - total_output:,} ({(total_input-total_output)/total_input*100:.1f}%)")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("=" * 70)

# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":
    main()
