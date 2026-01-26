import hashlib
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any


def validate_file(filepath: Path) -> bool:
    if not filepath.exists() or not filepath.is_file():
        return False
    return True


def validate_format(filepath: Path, expected_extensions: list) -> bool:
    return filepath.suffix.lower() in [ext.lower() for ext in expected_extensions]


def calculate_hash(filepath: Path, algorithm: str = 'sha256') -> str:
    hash_obj = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def generate_version(filepath: Path) -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{filepath.stem}_{timestamp}{filepath.suffix}"


def generate_metadata(
    filepath: Path,
    source: str,
    description: str,
    data_type: str,
    additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if additional_info is None:
        additional_info = {}
    
    file_stats = filepath.stat()
    
    metadata = {
        "filename": filepath.name,
        "filepath": str(filepath.relative_to(filepath.parents[2])),
        "source": source,
        "description": description,
        "data_type": data_type,
        "size_bytes": file_stats.st_size,
        "created_at": datetime.datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
        "modified_at": datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
        "ingested_at": datetime.datetime.now().isoformat(),
        "hash_type": "sha256",
        "hash": calculate_hash(filepath),
        **additional_info
    }
    return metadata


def save_metadata(metadata: Dict[str, Any], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved: {output_path}")


def consolidate_metadata(metadata_files: list, output_path: Path):
    all_metadata = []
    for meta_file in metadata_files:
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                all_metadata.append(json.load(f))
    
    consolidated = {
        "ingestion_date": datetime.datetime.now().isoformat(),
        "total_files": len(all_metadata),
        "files": all_metadata
    }
    
    save_metadata(consolidated, output_path)
