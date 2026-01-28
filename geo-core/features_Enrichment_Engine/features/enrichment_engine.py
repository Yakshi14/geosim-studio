"""
Feature Enrichment Engine for Buildings and Roads
Converts GIS features into simulation primitives
"""

import geopandas as gpd
import numpy as np
from typing import Optional
import rasterio
import json
from pathlib import Path


class FeatureEnricher:
    def __init__(self, dem_path: Optional[str] = None):
        self.dem_path = dem_path
        self.dem_data = None
        self.dem_transform = None

        if dem_path:
            self._load_dem()

    def _load_dem(self):
        try:
            with rasterio.open(self.dem_path) as src:
                self.dem_data = src.read(1)
                self.dem_transform = src.transform
        except Exception as e:
            print(f"Warning: Could not load DEM: {e}")

    # ---------------- BUILDINGS ---------------- #

    def enrich_buildings(self, buildings_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        enriched = buildings_gdf.copy()

        enriched["height_m"] = enriched.apply(self._estimate_building_height, axis=1)
        enriched["usage_type"] = enriched.apply(self._classify_building_usage, axis=1)
        enriched["lod_class"] = enriched.apply(self._assign_lod_class, axis=1)

        enriched["footprint_area_m2"] = enriched.geometry.area
        enriched["perimeter_m"] = enriched.geometry.length

        enriched["confidence"] = enriched.apply(
            self._calculate_building_confidence, axis=1
        )

        return enriched

    def _estimate_building_height(self, row) -> float:
        levels = row.get("building:levels")
        if isinstance(levels, (int, float, str)):
            try:
                return float(levels) * 3.5
            except:
                pass

        height = row.get("height")
        if isinstance(height, (int, float, str)):
            try:
                return float(height)
            except:
                pass

        building_type = row.get("building")
        building_type = building_type.lower() if isinstance(building_type, str) else "yes"

        return self._get_default_height(building_type)

    def _get_default_height(self, building_type: str) -> float:
        defaults = {
            "house": 6.0,
            "residential": 10.5,
            "apartments": 21.0,
            "commercial": 14.0,
            "retail": 7.0,
            "industrial": 8.0,
            "warehouse": 10.0,
            "office": 35.0,
            "hospital": 24.5,
            "school": 10.5,
            "church": 12.0,
            "yes": 7.0,
        }
        return defaults.get(building_type, 7.0)

    def _classify_building_usage(self, row) -> str:
        building = row.get("building")
        amenity = row.get("amenity")

        building = building.lower() if isinstance(building, str) else "unknown"
        amenity = amenity.lower() if isinstance(amenity, str) else ""

        if building in ["house", "residential", "apartments", "dormitory"]:
            return "residential"

        if building in ["commercial", "retail", "office", "hotel"]:
            return "commercial"
        if amenity in ["restaurant", "cafe", "bank", "shop"]:
            return "commercial"

        if building in ["industrial", "warehouse", "factory"]:
            return "industrial"

        if building in ["hospital", "school", "college", "university"]:
            return "institutional"
        if amenity in ["hospital", "school", "library"]:
            return "institutional"

        if building in ["church", "mosque", "temple"]:
            return "religious"

        return "other"

    def _assign_lod_class(self, row) -> int:
        area = row.geometry.area
        usage = row.get("usage_type", "other")

        if usage in ["religious", "institutional"] and area > 1000:
            return 4
        if area > 2000:
            return 4
        if area > 500:
            return 3
        if area > 100:
            return 2
        if area > 10:
            return 1
        return 0

    def _calculate_building_confidence(self, row) -> float:
        score = 0.5

        if row.get("building:levels"):
            score += 0.2
        if row.get("height"):
            score += 0.2
        if isinstance(row.get("building"), str):
            score += 0.1
        if isinstance(row.get("amenity"), str):
            score += 0.1
        if row.geometry.is_valid:
            score += 0.1

        return min(score, 1.0)

    # ---------------- ROADS ---------------- #

    def enrich_roads(self, roads_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        enriched = roads_gdf.copy()

        enriched["width_m"] = enriched.apply(self._estimate_road_width, axis=1)
        enriched["road_type"] = enriched.apply(self._classify_road_type, axis=1)
        enriched["nav_weight"] = enriched.apply(
            self._calculate_navigation_weight, axis=1
        )
        enriched["length_m"] = enriched.geometry.length
        enriched["speed_limit_kmh"] = enriched.apply(
            self._estimate_speed_limit, axis=1
        )
        enriched["lanes"] = enriched.apply(self._estimate_lanes, axis=1)
        enriched["confidence"] = enriched.apply(
            self._calculate_road_confidence, axis=1
        )

        return enriched

    def _estimate_road_width(self, row) -> float:
        width = row.get("width")
        if isinstance(width, (int, float, str)):
            try:
                return float(width)
            except:
                pass

        lanes = row.get("lanes")
        if isinstance(lanes, (int, float, str)):
            try:
                return int(lanes) * 3.5
            except:
                pass

        highway = row.get("highway")
        highway = highway.lower() if isinstance(highway, str) else "unclassified"
        return self._get_default_width(highway)

    def _get_default_width(self, highway: str) -> float:
        defaults = {
            "motorway": 14.0,
            "primary": 10.5,
            "secondary": 7.0,
            "residential": 5.5,
            "service": 3.5,
            "path": 1.5,
        }
        return defaults.get(highway, 5.5)

    def _classify_road_type(self, row) -> str:
        highway = row.get("highway")
        highway = highway.lower() if isinstance(highway, str) else "unclassified"

        if highway in ["motorway", "trunk"]:
            return "highway"
        if highway in ["primary"]:
            return "primary"
        if highway in ["secondary", "tertiary"]:
            return "secondary"
        if highway in ["residential"]:
            return "residential"
        if highway in ["service"]:
            return "service"
        if highway in ["footway", "path", "cycleway"]:
            return "pedestrian"
        return "other"

    def _calculate_navigation_weight(self, row) -> float:
        highway = row.get("highway")
        highway = highway.lower() if isinstance(highway, str) else "unclassified"

        surface = row.get("surface")
        surface = surface.lower() if isinstance(surface, str) else ""

        base = {
            "motorway": 1.0,
            "primary": 1.5,
            "secondary": 2.0,
            "residential": 3.0,
            "service": 4.0,
        }

        weight = base.get(highway, 3.0)

        if surface in ["gravel", "dirt"]:
            weight *= 1.5

        return weight

    def _estimate_speed_limit(self, row) -> int:
        speed = row.get("maxspeed")
        if isinstance(speed, (int, float, str)):
            try:
                return int(speed)
            except:
                pass

        highway = row.get("highway")
        highway = highway.lower() if isinstance(highway, str) else "unclassified"

        defaults = {
            "motorway": 120,
            "primary": 80,
            "secondary": 60,
            "residential": 30,
        }
        return defaults.get(highway, 50)

    def _estimate_lanes(self, row) -> int:
        lanes = row.get("lanes")
        if isinstance(lanes, (int, float, str)):
            try:
                return int(lanes)
            except:
                pass

        return max(1, int(self._estimate_road_width(row) / 3.5))

    def _calculate_road_confidence(self, row) -> float:
        score = 0.5

        if row.get("width"):
            score += 0.15
        if row.get("lanes"):
            score += 0.15
        if row.get("surface"):
            score += 0.1
        if row.get("maxspeed"):
            score += 0.1
        if row.geometry.is_valid:
            score += 0.1

        return min(score, 1.0)

    # ---------------- SAVE ---------------- #

    def save_enriched_data(self, buildings, roads, output_dir):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        buildings.to_file(output_dir / "buildings_enriched.geojson", driver="GeoJSON")
        roads.to_file(output_dir / "roads_enriched.geojson", driver="GeoJSON")

        print("✓ Enriched data saved")


