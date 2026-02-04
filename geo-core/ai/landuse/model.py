import numpy as np

LANDUSE_CLASSES = [
    "urban",
    "forest",
    "grassland",
    "water",
    "bare_land",
    "agriculture"
]

def classify_landuse(satellite_img, dem_features):
    """
    Phase 1: Mock AI inference
    (Future: TorchGeo / SAM)
    """
    height, width = satellite_img.shape

    landuse_map = np.random.randint(0, len(LANDUSE_CLASSES), (height, width))
    confidence_map = np.random.uniform(0.6, 0.95, (height, width))

    return landuse_map, confidence_map
