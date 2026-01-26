import osmnx as ox
from pathlib import Path

# Import CRS handler
from crs_handler import handle_vector_crs

# -------------------------
# 1. Resolve project root
# -------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

# -------------------------
# 2. Place definition
# -------------------------
place_name = "Mumbai City, Maharashtra, India"

# -------------------------
# 3. Output directories
# -------------------------
output_dir = BASE_DIR / "data" / "processed" / "osm"
output_dir.mkdir(parents=True, exist_ok=True)

# Ingested outputs (NO CRS conversion here)
buildings_out = output_dir / "mumbai_buildings.geojson"
roads_out = output_dir / "mumbai_roads.geojson"

# CRS-normalized outputs
buildings_crs_out = output_dir / "mumbai_buildings_epsg4326.geojson"
roads_crs_out = output_dir / "mumbai_roads_epsg4326.geojson"

# -------------------------
# 4. Ingest buildings
# -------------------------
print("🏢 Downloading OSM building footprints...")
buildings = ox.features_from_place(
    place_name,
    tags={"building": True}
)

buildings.to_file(
    buildings_out,
    driver="GeoJSON"
)

print("✅ Buildings ingested:", buildings_out)

# -------------------------
# 5. Ingest roads
# -------------------------
print("🛣️ Downloading OSM road network...")
roads_graph = ox.graph_from_place(
    place_name,
    network_type="drive"
)

roads_gdf = ox.graph_to_gdfs(
    roads_graph,
    nodes=False,
    edges=True
)

roads_gdf.to_file(
    roads_out,
    driver="GeoJSON"
)

print("✅ Roads ingested:", roads_out)

# -------------------------
# 6. CRS Detection & Reprojection (Handled separately)
# -------------------------
handle_vector_crs(
    buildings_out,
    buildings_crs_out
)

handle_vector_crs(
    roads_out,
    roads_crs_out
)

print("🌍 CRS normalization completed for OSM data")
print("📦 CRS-normalized files saved in:", output_dir)
