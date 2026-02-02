import geopandas as gpd
from shapely.geometry import Polygon

def generate_zones(output_path):
    zones = [
        Polygon([(0,0), (100,0), (100,100), (0,100)])
    ]

    gdf = gpd.GeoDataFrame(
        {"zone": ["high_density_forest"]},
        geometry=zones,
        crs="EPSG:32643"  # example UTM
    )

    gdf.to_file(output_path, driver="GeoJSON")