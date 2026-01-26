# scripts/normalization/utm_utils.py
from pyproj import CRS

def get_utm_crs_from_latlon(lat: float, lon: float) -> CRS:
    """
    Determine UTM CRS based on latitude & longitude
    """
    zone = int((lon + 180) / 6) + 1
    is_northern = lat >= 0

    epsg = 32600 + zone if is_northern else 32700 + zone
    return CRS.from_epsg(epsg)