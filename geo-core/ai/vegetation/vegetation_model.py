import numpy as np

def compute_vegetation_density(landuse_map: np.ndarray) -> np.ndarray:
    """
    Generate vegetation density map from land-use classification.
    Output range: 0.0 to 1.0 (procedural density for game engines)

    Landuse class mapping (from Module 6):
    0 = urban
    1 = forest
    2 = grassland
    3 = water
    4 = bare_land
    5 = agriculture
    """

    # Initialize with zeros
    vegetation_density = np.zeros_like(landuse_map, dtype=np.float32)

    # Procedural rules (simulation-ready)
    vegetation_density[landuse_map == 1] = 0.9  # Forest → very dense
    vegetation_density[landuse_map == 5] = 0.7  # Agriculture → medium-high
    vegetation_density[landuse_map == 2] = 0.5  # Grassland → medium
    vegetation_density[landuse_map == 4] = 0.1  # Bare land → very low

    return vegetation_density
