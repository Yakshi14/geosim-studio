from pathlib import Path
import sys
import argparse

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

import dem_ingest
import satellite_ingest
import osm_ingest
import ingest_utils

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


def ingest_all(place_name: str = "Mumbai City, Maharashtra, India", dem_file: Path = None, satellite_file: Path = None):
    print("=" * 60)
    print("MODULE 1 - DATA INGESTION ENGINE")
    print("=" * 60)
    
    results = {}
    
    print("\n[1/3] Ingesting DEM...")
    results['dem'] = dem_ingest.ingest_dem(dem_file)
    
    print("\n[2/3] Ingesting Satellite...")
    results['satellite'] = satellite_ingest.ingest_satellite(satellite_file)
    
    print("\n[3/3] Ingesting OSM (Buildings, Roads, Water)...")
    osm_results = osm_ingest.ingest_osm(place_name)
    results['osm'] = osm_results
    
    print("\n" + "=" * 60)
    print("Consolidating metadata...")
    
    metadata_files = [
        RAW_DATA_DIR / "dem" / "metadata.json",
        RAW_DATA_DIR / "satellite" / "metadata.json",
        RAW_DATA_DIR / "osm" / "metadata.json"
    ]
    
    ingest_utils.consolidate_metadata(metadata_files, RAW_DATA_DIR / "metadata.json")
    
    print("\n" + "=" * 60)
    print("Ingestion Summary:")
    print(f"  DEM: {'OK' if results['dem'] else 'FAILED'}")
    print(f"  Satellite: {'OK' if results['satellite'] else 'FAILED'}")
    print(f"  OSM Buildings: {'OK' if results['osm'].get('buildings') else 'FAILED'}")
    print(f"  OSM Roads: {'OK' if results['osm'].get('roads') else 'FAILED'}")
    print(f"  OSM Water: {'OK' if results['osm'].get('water') else 'FAILED'}")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Ingestion Engine - Module 1")
    parser.add_argument("--place", default="Mumbai City, Maharashtra, India", help="Place name for OSM data")
    parser.add_argument("--dem-file", type=Path, help="Path to DEM file")
    parser.add_argument("--satellite-file", type=Path, help="Path to satellite file")
    parser.add_argument("--dem-only", action="store_true", help="Ingest DEM only")
    parser.add_argument("--satellite-only", action="store_true", help="Ingest satellite only")
    parser.add_argument("--osm-only", action="store_true", help="Ingest OSM only")
    
    args = parser.parse_args()
    
    if args.dem_only:
        dem_ingest.ingest_dem(args.dem_file)
    elif args.satellite_only:
        satellite_ingest.ingest_satellite(args.satellite_file)
    elif args.osm_only:
        osm_ingest.ingest_osm(args.place)
    else:
        ingest_all(args.place, args.dem_file, args.satellite_file)
