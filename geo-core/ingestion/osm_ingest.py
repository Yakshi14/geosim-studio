import osmnx as ox
from pathlib import Path
import sys
import geopandas as gpd

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))
import ingest_utils

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_OSM_DIR = BASE_DIR / "data" / "raw" / "osm"
RAW_OSM_DIR.mkdir(parents=True, exist_ok=True)


def ingest_buildings(place_name: str) -> bool:
    try:
        buildings = ox.features_from_place(place_name, tags={"building": True})
        
        raw_buildings_path = RAW_OSM_DIR / "buildings.geojson"
        buildings.to_file(raw_buildings_path, driver="GeoJSON")
        
        metadata = ingest_utils.generate_metadata(
            raw_buildings_path,
            "OpenStreetMap",
            f"Building footprints for {place_name}",
            "buildings"
        )
        
        metadata_path = RAW_OSM_DIR / "buildings_metadata.json"
        ingest_utils.save_metadata(metadata, metadata_path)
        
        print(f"Buildings ingested: {raw_buildings_path.name}")
        return True
    except Exception as e:
        print(f"Error ingesting buildings: {e}")
        return False


def ingest_roads(place_name: str) -> bool:
    try:
        roads_graph = ox.graph_from_place(place_name, network_type="drive")
        roads_gdf = ox.graph_to_gdfs(roads_graph, nodes=False, edges=True)
        
        raw_roads_path = RAW_OSM_DIR / "roads.geojson"
        roads_gdf.to_file(raw_roads_path, driver="GeoJSON")
        
        metadata = ingest_utils.generate_metadata(
            raw_roads_path,
            "OpenStreetMap",
            f"Road network for {place_name}",
            "roads"
        )
        
        metadata_path = RAW_OSM_DIR / "roads_metadata.json"
        ingest_utils.save_metadata(metadata, metadata_path)
        
        print(f"Roads ingested: {raw_roads_path.name}")
        return True
    except Exception as e:
        print(f"Error ingesting roads: {e}")
        return False


def ingest_water(place_name: str) -> bool:
    try:
        water_features = ox.features_from_place(
            place_name,
            tags={"natural": ["water", "bay"], "waterway": True, "water": True}
        )
        
        if len(water_features) == 0:
            print("No water features found")
            return False
        
        raw_water_path = RAW_OSM_DIR / "water.geojson"
        water_features.to_file(raw_water_path, driver="GeoJSON")
        
        metadata = ingest_utils.generate_metadata(
            raw_water_path,
            "OpenStreetMap",
            f"Water features for {place_name}",
            "water"
        )
        
        metadata_path = RAW_OSM_DIR / "water_metadata.json"
        ingest_utils.save_metadata(metadata, metadata_path)
        
        print(f"Water features ingested: {raw_water_path.name}")
        return True
    except Exception as e:
        print(f"Error ingesting water: {e}")
        return False


def ingest_osm(place_name: str, include_buildings: bool = True, include_roads: bool = True, include_water: bool = True):
    print(f"Ingesting OSM data for: {place_name}")
    
    results = {}
    
    if include_buildings:
        results['buildings'] = ingest_buildings(place_name)
    
    if include_roads:
        results['roads'] = ingest_roads(place_name)
    
    if include_water:
        results['water'] = ingest_water(place_name)
    
    metadata_files = [
        RAW_OSM_DIR / "buildings_metadata.json",
        RAW_OSM_DIR / "roads_metadata.json",
        RAW_OSM_DIR / "water_metadata.json"
    ]
    
    ingest_utils.consolidate_metadata(metadata_files, RAW_OSM_DIR / "metadata.json")
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest OSM data")
    parser.add_argument("--place", required=True, help="Place name (e.g., 'Mumbai City, Maharashtra, India')")
    parser.add_argument("--skip-buildings", action="store_true", help="Skip buildings")
    parser.add_argument("--skip-roads", action="store_true", help="Skip roads")
    parser.add_argument("--skip-water", action="store_true", help="Skip water")
    args = parser.parse_args()
    
    ingest_osm(
        args.place,
        include_buildings=not args.skip_buildings,
        include_roads=not args.skip_roads,
        include_water=not args.skip_water
    )
