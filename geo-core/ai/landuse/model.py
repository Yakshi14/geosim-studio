import numpy as np

LANDUSE_CLASSES = {
    0: "urban",
    1: "forest",
    2: "grassland",
    3: "water",
    4: "bare_land",
    5: "agriculture",
}

def classify_landuse(satellite, elevation, slope):
    h, w = satellite.shape
    landuse = np.zeros((h, w), dtype=np.uint8)
    confidence = np.zeros((h, w), dtype=np.float32)

    # VERY SIMPLE heuristic model (Phase-1 safe)
    landuse[slope > 30] = 1                # forest
    landuse[(slope < 5) & (elevation < 5)] = 3   # water
    landuse[(slope < 10) & (elevation > 20)] = 5 # agriculture
    landuse[(slope < 8)] = 0               # urban
    landuse[(slope > 15) & (elevation < 10)] = 4 # bare land

    confidence[:] = 0.75
    return landuse, confidence