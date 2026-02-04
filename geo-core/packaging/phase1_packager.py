import shutil
import json
from pathlib import Path
from datetime import datetime

# ------------------ PATHS ------------------
BASE_DIR = Path(__file__).resolve().parents[2]

NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
FEATURES_DIR = BASE_DIR / "data" / "features"
AI_DIR = BASE_DIR / "data" / "ai"
VALIDATED_DIR = BASE_DIR / "data" / "validated"

PHASE1_OUT = BASE_DIR / "data" / "phase1_output"
TERRAIN_OUT = PHASE1_OUT / "terrain"
FEATURES_OUT = PHASE1_OUT / "features"
AI_OUT = PHASE1_OUT / "ai"

# Ensure output directories exist
for d in [PHASE1_OUT, TERRAIN_OUT, FEATURES_OUT, AI_OUT]:
    d.mkdir(parents=True, exist_ok=True)

# ------------------ HELPERS ------------------
def copy_all(src_dir: Path, dst_dir: Path, pattern: str):
    """Copy all matching files from src to dst."""
    files = list(src_dir.glob(pattern))
    for f in files:
        shutil.copy2(f, dst_dir / f.name)

def package_phase1():
    print("\n=== MODULE 9 — PHASE 1 PACKAGING ===")

    # 1️⃣ Copy TERRAIN (GeoTIFF)
    print("📦 Packaging terrain...")
    copy_all(NORMALIZED_DIR, TERRAIN_OUT, "*.tif")

    # 2️⃣ Copy FEATURES (GeoJSON)
    print("📦 Packaging features...")
    copy_all(FEATURES_DIR, FEATURES_OUT, "*.geojson")

    # 3️⃣ Copy AI OUTPUTS (GeoTIFF + GeoJSON)
    print("📦 Packaging AI outputs...")
    copy_all(AI_DIR, AI_OUT, "*.tif")
    copy_all(AI_DIR, AI_OUT, "*.geojson")

    # 4️⃣ Create METADATA.JSON (handoff document)
    metadata = {
        "phase": 1,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_root": str(BASE_DIR),
        "validation_report": str((VALIDATED_DIR / "validation_report.json").resolve()),
        "contents": {
            "terrain": list(f.name for f in TERRAIN_OUT.glob("*")),
            "features": list(f.name for f in FEATURES_OUT.glob("*")),
            "ai": list(f.name for f in AI_OUT.glob("*")),
        },
        "formats": {
            "terrain": "GeoTIFF",
            "features": "GeoJSON",
            "ai": ["GeoTIFF", "GeoJSON"]
        },
        "notes": [
            "Ready for deck.gl visualization",
            "CRS is consistent across all layers",
            "AI confidence checked in Module 8",
            "No meshes generated in Phase 1"
        ]
    }

    meta_path = PHASE1_OUT / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("✅ Phase 1 packaging complete.")
    print("Output folder:", PHASE1_OUT)

if __name__ == "__main__":
    package_phase1()
