from pathlib import Path
import rasterio
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
AI_DIR = BASE_DIR / "data" / "ai"

def check_crs_uniformity():
    """
    Ensure all normalized rasters use the same CRS.
    """
    tifs = list(NORMALIZED_DIR.glob("*.tif"))

    if not tifs:
        return {"crs_uniformity": "FAIL", "reason": "No normalized rasters found"}

    with rasterio.open(tifs[0]) as ref:
        ref_crs = str(ref.crs)

    mismatches = []
    for tif in tifs:
        with rasterio.open(tif) as src:
            if str(src.crs) != ref_crs:
                mismatches.append(tif.name)

    return {
        "crs_uniformity": "PASS" if not mismatches else "REVIEW",
        "reference_crs": ref_crs,
        "mismatches": mismatches
    }

def check_terrain_continuity():
    """
    Basic terrain sanity check:
    - No all-zero DEM
    - No extreme spikes (NaN/Inf)
    """
    dem_files = list(NORMALIZED_DIR.glob("*dem*.tif"))
    if not dem_files:
        return {"terrain_continuity": "FAIL", "reason": "No normalized DEM found"}

    with rasterio.open(dem_files[0]) as src:
        dem = src.read(1)

    issues = []
    if np.all(dem == 0):
        issues.append("DEM is all zeros")

    if np.isnan(dem).any():
        issues.append("DEM contains NaN values")

    if np.isinf(dem).any():
        issues.append("DEM contains infinite values")

    return {
        "terrain_continuity": "PASS" if not issues else "REVIEW",
        "issues": issues
    }

def check_ai_confidence(threshold=0.6):
    """
    Validate AI confidence map from Module 6.
    """
    conf_path = AI_DIR / "confidence_map.tif"

    if not conf_path.exists():
        return {"ai_confidence": "FAIL", "reason": "confidence_map.tif missing"}

    with rasterio.open(conf_path) as src:
        conf = src.read(1)

    low_conf_pixels = int((conf < threshold).sum())

    return {
        "ai_confidence": "PASS" if low_conf_pixels == 0 else "REVIEW",
        "threshold": threshold,
        "low_confidence_pixels": low_conf_pixels
    }
