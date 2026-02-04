import geopandas as gpd
from shapely.geometry import Polygon
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
AI_DIR = BASE_DIR / "data" / "ai"
AI_DIR.mkdir(parents=True, exist_ok=True)

def generate_tree_zones():
    """
    Phase 1: Procedural placeholder tree zones.
    (In Phase 2: this will come from ML or spatial clustering)
    """

    polygons = [
        Polygon([(0,0), (1,0), (1,1), (0,1)]),
        Polygon([(2,2), (3,2), (3,3), (2,3)])
    ]

    gdf = gpd.GeoDataFrame(
        {"zone": ["dense_forest", "scattered_trees"]},
        geometry=polygons,
        crs="EPSG:4326"
    )

    output_path = AI_DIR / "tree_zones.geojson"
    gdf.to_file(output_path, driver="GeoJSON")

    print(f"Saved tree zones → {output_path}")
