from pathlib import Path
import json

from raster_checks import (
    check_crs_uniformity,
    check_terrain_continuity,
    check_ai_confidence,
)

from vector_checks import (
    check_geometry_validity,
    check_attribute_completeness,
)

BASE_DIR = Path(__file__).resolve().parents[2]
VALIDATED_DIR = BASE_DIR / "data" / "validated"
VALIDATED_DIR.mkdir(parents=True, exist_ok=True)

def run_validation():
    print("\n=== MODULE 8 — VALIDATION & CONSISTENCY ENGINE ===")

    report = {
        "crs": check_crs_uniformity(),
        "terrain": check_terrain_continuity(),
        "ai": check_ai_confidence(),
        "geometry": check_geometry_validity(),
        "attributes": check_attribute_completeness(),
    }

    out_path = VALIDATED_DIR / "validation_report.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print("✅ Validation complete.")
    print("Report saved to:", out_path)

if __name__ == "__main__":
    run_validation()
