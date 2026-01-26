from pathlib import Path
from typing import Optional
import sys
import shutil

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))
import ingest_utils

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_SAT_DIR = BASE_DIR / "data" / "raw" / "satellite"
RAW_SAT_DIR.mkdir(parents=True, exist_ok=True)


def ingest_satellite(file_path: Optional[Path] = None) -> bool:
    if file_path is None:
        jp2_files = list(RAW_SAT_DIR.glob("*.jp2"))
        tif_files = list(RAW_SAT_DIR.glob("*.tif"))
        all_files = jp2_files + tif_files
        
        if not all_files:
            print(f"No satellite file found in {RAW_SAT_DIR}")
            print("Supported formats: .jp2, .tif")
            return False
        file_path = all_files[0]
    
    if not ingest_utils.validate_file(file_path):
        print(f"Invalid file: {file_path}")
        return False
    
    if not ingest_utils.validate_format(file_path, ['.jp2', '.tif', '.tiff']):
        print(f"Unsupported format. Expected: .jp2, .tif, .tiff")
        return False
    
    dest_path = RAW_SAT_DIR / file_path.name
    if file_path != dest_path:
        shutil.copy2(file_path, dest_path)
        print(f"Copied {file_path.name} to {dest_path}")
    
    metadata = ingest_utils.generate_metadata(
        dest_path,
        "Copernicus Data Space",
        "Sentinel-2 L2A Imagery",
        "satellite"
    )
    
    metadata_path = RAW_SAT_DIR / "metadata.json"
    ingest_utils.save_metadata(metadata, metadata_path)
    
    print(f"Satellite data ingested: {dest_path.name}")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest satellite data")
    parser.add_argument("--file", type=Path, help="Path to satellite file")
    args = parser.parse_args()
    
    ingest_satellite(args.file)
