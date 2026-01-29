from pathlib import Path
from typing import Optional
import sys
import shutil

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))
import ingest_utils

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DEM_DIR = BASE_DIR / "data" / "raw" / "dem"
RAW_DEM_DIR.mkdir(parents=True, exist_ok=True)


def ingest_dem(file_path: Optional[Path] = None, source: str = "SRTM") -> bool:
    if file_path is None:
        tif_files = list(RAW_DEM_DIR.glob("*.tif"))
        if not tif_files:
            print(f"No DEM file found in {RAW_DEM_DIR}")
            print("Supported formats: .tif, .tiff")
            return False
        file_path = tif_files[0]
    
    if not ingest_utils.validate_file(file_path):
        print(f"Invalid file: {file_path}")
        return False
    
    if not ingest_utils.validate_format(file_path, ['.tif', '.tiff']):
        print(f"Unsupported format. Expected: .tif, .tiff")
        return False
    
    dest_path = RAW_DEM_DIR / file_path.name
    if file_path != dest_path:
        shutil.copy2(file_path, dest_path)
        print(f"Copied {file_path.name} to {dest_path}")
    
    source_map = {
        "SRTM": "USGS EarthExplorer",
        "Copernicus": "Copernicus DEM"
    }
    
    metadata = ingest_utils.generate_metadata(
        dest_path,
        source_map.get(source, source),
        f"{source} DEM data",
        "dem"
    )
    
    metadata_path = RAW_DEM_DIR / "metadata.json"
    ingest_utils.save_metadata(metadata, metadata_path)
    
    print(f"DEM ingested: {dest_path.name}")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest DEM data")
    parser.add_argument("--file", type=Path, help="Path to DEM file")
    parser.add_argument("--source", default="SRTM", choices=["SRTM", "Copernicus"], help="Data source")
    args = parser.parse_args()
    
    ingest_dem(args.file, args.source)
