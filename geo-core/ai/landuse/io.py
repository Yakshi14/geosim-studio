import rasterio
import numpy as np
from rasterio.warp import reproject, Resampling

def align_to_reference(reference_path, target_path):
    """
    Align target raster to reference raster grid
    """

    with rasterio.open(reference_path) as ref:
        ref_data = ref.read(1)
        ref_meta = ref.meta

    with rasterio.open(target_path) as src:
        target_data = src.read(1)

        aligned = np.empty_like(ref_data, dtype=np.float32)

        reproject(
            source=target_data,
            destination=aligned,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref.transform,
            dst_crs=ref.crs,
            resampling=Resampling.bilinear,
        )

    return aligned, ref_meta