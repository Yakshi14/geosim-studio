import numpy as np

def vegetation_density(landuse):
    density = np.zeros_like(landuse, dtype=np.float32)

    density[landuse == 1] = 0.9   # forest
    density[landuse == 5] = 0.7   # agriculture
    density[landuse == 2] = 0.5   # grassland

    return density