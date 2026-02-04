import rasterio
import numpy as np
from rasterio.warp import reproject, Resampling

def align_to_reference(ref_path, target_path):
    """
    Align target raster (DEM) to match reference raster (satellite).
    Returns aligned array + metadata.
    """

    with rasterio.open(ref_path) as ref:
        ref_meta = ref.meta.copy()
        ref_shape = (ref.height, ref.width)

        with rasterio.open(target_path) as tgt:
            aligned = np.zeros(ref_shape, dtype=tgt.dtypes[0])

            reproject(
                source=rasterio.band(tgt, 1),
                destination=aligned,
                src_transform=tgt.transform,
                src_crs=tgt.crs,
                dst_transform=ref.transform,
                dst_crs=ref.crs,
                resampling=Resampling.bilinear,
            )

    return aligned, ref_meta


def export_landuse(landuse, confidence, path="data/ai"):
    transform = None  # We reuse existing transform later

    with rasterio.open(
        f"{path}/landuse.tif",
        "w",
        driver="GTiff",
        height=landuse.shape[0],
        width=landuse.shape[1],
        count=1,
        dtype=landuse.dtype,
    ) as dst:
        dst.write(landuse, 1)

    with rasterio.open(
        f"{path}/confidence_map.tif",
        "w",
        driver="GTiff",
        height=confidence.shape[0],
        width=confidence.shape[1],
        count=1,
        dtype=confidence.dtype,
    ) as dst:
        dst.write(confidence, 1)
