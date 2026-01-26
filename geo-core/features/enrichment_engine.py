"""
Feature Enrichment Engine for Buildings and Roads
Converts GIS features into simulation primitives
"""

import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, LineString
from typing import Dict, List, Optional
import rasterio
from rasterio.mask import mask
import json
from pathlib import Path


class FeatureEnricher:
    """Main class for enriching building and road features"""
    
    def __init__(self, dem_path: Optional[str] = None):
        """
        Initialize enrichment engine
        
        Args:
            dem_path: Path to normalized DEM file for height estimation
        """
        self.dem_path = dem_path
        self.dem_data = None
        self.dem_transform = None
        
        if dem_path:
            self._load_dem()
    
    def _load_dem(self):
        """Load DEM for height calculations"""
        try:
            with rasterio.open(self.dem_path) as src:
                self.dem_data = src.read(1)
                self.dem_transform = src.transform
        except Exception as e:
            print(f"Warning: Could not load DEM: {e}")
    
    def enrich_buildings(self, buildings_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Enrich building features with simulation-ready attributes
        
        Args:
            buildings_gdf: GeoDataFrame with clean building geometries
            
        Returns:
            Enriched GeoDataFrame with height, usage, and LOD attributes
        """
        enriched = buildings_gdf.copy()
        
        # Add height estimation
        enriched['height_m'] = enriched.apply(
            lambda row: self._estimate_building_height(row), axis=1
        )
        
        # Add usage classification
        enriched['usage_type'] = enriched.apply(
            lambda row: self._classify_building_usage(row), axis=1
        )
        
        # Add LOD class
        enriched['lod_class'] = enriched.apply(
            lambda row: self._assign_lod_class(row), axis=1
        )
        
        # Add area calculation
        enriched['footprint_area_m2'] = enriched.geometry.area
        
        # Add perimeter
        enriched['perimeter_m'] = enriched.geometry.length
        
        # Add confidence score
        enriched['confidence'] = enriched.apply(
            lambda row: self._calculate_building_confidence(row), axis=1
        )
        
        return enriched
    
    def _estimate_building_height(self, row) -> float:
        """
        Estimate building height using multiple methods
        
        Priority:
        1. OSM building:levels tag
        2. OSM height tag
        3. DEM-based estimation
        4. Default by building type
        """
        # Method 1: OSM building:levels
        if 'building:levels' in row and row['building:levels']:
            try:
                levels = float(row['building:levels'])
                return levels * 3.5  # Average 3.5m per floor
            except:
                pass
        
        # Method 2: OSM height tag
        if 'height' in row and row['height']:
            try:
                return float(row['height'])
            except:
                pass
        
        # Method 3: DEM-based (placeholder - needs full implementation)
        if self.dem_data is not None:
            # This would sample DEM at building corners
            # For now, return default
            pass
        
        # Method 4: Default by type
        building_type = row.get('building', 'yes')
        return self._get_default_height(building_type)
    
    def _get_default_height(self, building_type: str) -> float:
        """Default heights by building type"""
        defaults = {
            'house': 6.0,
            'residential': 10.5,  # 3 floors
            'apartments': 21.0,   # 6 floors
            'commercial': 14.0,   # 4 floors
            'retail': 7.0,
            'industrial': 8.0,
            'warehouse': 10.0,
            'office': 35.0,       # 10 floors
            'hospital': 24.5,     # 7 floors
            'school': 10.5,       # 3 floors
            'church': 12.0,
            'yes': 7.0,           # Generic fallback
        }
        return defaults.get(building_type, 7.0)
    
    def _classify_building_usage(self, row) -> str:
        """
        Classify building usage type
        
        Categories: residential, commercial, industrial, institutional, 
                   religious, recreational, agricultural, other
        """
        building_tag = row.get('building', 'yes').lower()
        amenity_tag = row.get('amenity', '').lower()
        
        # Residential
        if building_tag in ['house', 'residential', 'apartments', 'dormitory', 'terrace']:
            return 'residential'
        
        # Commercial
        if building_tag in ['commercial', 'retail', 'office', 'hotel', 'supermarket']:
            return 'commercial'
        if amenity_tag in ['restaurant', 'cafe', 'shop', 'bank']:
            return 'commercial'
        
        # Industrial
        if building_tag in ['industrial', 'warehouse', 'factory', 'manufacture']:
            return 'industrial'
        
        # Institutional
        if building_tag in ['hospital', 'school', 'university', 'college', 'public']:
            return 'institutional'
        if amenity_tag in ['hospital', 'school', 'university', 'library']:
            return 'institutional'
        
        # Religious
        if building_tag in ['church', 'cathedral', 'mosque', 'temple', 'synagogue', 'shrine']:
            return 'religious'
        if amenity_tag in ['place_of_worship']:
            return 'religious'
        
        # Recreational
        if building_tag in ['stadium', 'sports_hall', 'pavilion']:
            return 'recreational'
        if amenity_tag in ['theatre', 'cinema', 'community_centre']:
            return 'recreational'
        
        # Agricultural
        if building_tag in ['barn', 'farm_auxiliary', 'greenhouse', 'silo']:
            return 'agricultural'
        
        return 'other'
    
    def _assign_lod_class(self, row) -> int:
        """
        Assign Level of Detail class for rendering optimization
        
        LOD 0: Very Low (distant view, < 10m²)
        LOD 1: Low (background, 10-100m²)
        LOD 2: Medium (standard view, 100-500m²)
        LOD 3: High (detailed view, 500-2000m²)
        LOD 4: Very High (hero buildings, > 2000m²)
        """
        area = row.geometry.area
        usage = row.get('usage_type', 'other')
        
        # Hero buildings (landmarks)
        if usage in ['religious', 'institutional'] and area > 1000:
            return 4
        
        # Large buildings
        if area > 2000:
            return 4
        elif area > 500:
            return 3
        elif area > 100:
            return 2
        elif area > 10:
            return 1
        else:
            return 0
    
    def _calculate_building_confidence(self, row) -> float:
        """Calculate confidence score for building data quality"""
        score = 0.5  # Base score
        
        # Has explicit height data
        if 'building:levels' in row and row['building:levels']:
            score += 0.2
        if 'height' in row and row['height']:
            score += 0.2
        
        # Has specific building type
        if row.get('building', 'yes') != 'yes':
            score += 0.1
        
        # Has amenity tag
        if 'amenity' in row and row['amenity']:
            score += 0.1
        
        # Geometry quality
        if row.geometry.is_valid and not row.geometry.is_empty:
            score += 0.1
        
        return min(score, 1.0)
    
    def enrich_roads(self, roads_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Enrich road features with simulation-ready attributes
        
        Args:
            roads_gdf: GeoDataFrame with clean road geometries
            
        Returns:
            Enriched GeoDataFrame with width, type, and navigation weight
        """
        enriched = roads_gdf.copy()
        
        # Add width estimation
        enriched['width_m'] = enriched.apply(
            lambda row: self._estimate_road_width(row), axis=1
        )
        
        # Add road type classification
        enriched['road_type'] = enriched.apply(
            lambda row: self._classify_road_type(row), axis=1
        )
        
        # Add AI navigation weight
        enriched['nav_weight'] = enriched.apply(
            lambda row: self._calculate_navigation_weight(row), axis=1
        )
        
        # Add length
        enriched['length_m'] = enriched.geometry.length
        
        # Add speed limit estimation
        enriched['speed_limit_kmh'] = enriched.apply(
            lambda row: self._estimate_speed_limit(row), axis=1
        )
        
        # Add lanes estimation
        enriched['lanes'] = enriched.apply(
            lambda row: self._estimate_lanes(row), axis=1
        )
        
        # Add confidence score
        enriched['confidence'] = enriched.apply(
            lambda row: self._calculate_road_confidence(row), axis=1
        )
        
        return enriched
    
    def _estimate_road_width(self, row) -> float:
        """
        Estimate road width from OSM tags or highway type
        """
        # Method 1: Explicit width tag
        if 'width' in row and row['width']:
            try:
                return float(row['width'])
            except:
                pass
        
        # Method 2: Lanes tag
        if 'lanes' in row and row['lanes']:
            try:
                lanes = int(row['lanes'])
                return lanes * 3.5  # 3.5m per lane
            except:
                pass
        
        # Method 3: Highway type defaults
        highway_type = row.get('highway', 'unclassified')
        return self._get_default_width(highway_type)
    
    def _get_default_width(self, highway_type: str) -> float:
        """Default widths by highway type"""
        defaults = {
            'motorway': 14.0,      # 4 lanes
            'trunk': 10.5,         # 3 lanes
            'primary': 10.5,       # 3 lanes
            'secondary': 7.0,      # 2 lanes
            'tertiary': 7.0,       # 2 lanes
            'unclassified': 5.5,   # 1.5 lanes
            'residential': 5.5,    # 1.5 lanes
            'service': 3.5,        # 1 lane
            'track': 3.0,          # Narrow
            'path': 1.5,           # Pedestrian
            'footway': 1.5,        # Pedestrian
            'cycleway': 2.0,       # Bike
            'pedestrian': 3.0,     # Pedestrian zone
        }
        return defaults.get(highway_type, 5.5)
    
    def _classify_road_type(self, row) -> str:
        """
        Classify road into simulation categories
        
        Categories: highway, primary, secondary, residential, 
                   service, pedestrian, other
        """
        highway_tag = row.get('highway', 'unclassified').lower()
        
        if highway_tag in ['motorway', 'trunk']:
            return 'highway'
        elif highway_tag in ['primary', 'primary_link']:
            return 'primary'
        elif highway_tag in ['secondary', 'secondary_link', 'tertiary', 'tertiary_link']:
            return 'secondary'
        elif highway_tag in ['residential', 'living_street']:
            return 'residential'
        elif highway_tag in ['service', 'track']:
            return 'service'
        elif highway_tag in ['footway', 'path', 'pedestrian', 'steps', 'cycleway']:
            return 'pedestrian'
        else:
            return 'other'
    
    def _calculate_navigation_weight(self, row) -> float:
        """
        Calculate AI navigation weight (lower = faster/preferred route)
        
        Based on road type, surface, and other attributes
        """
        highway_type = row.get('highway', 'unclassified')
        surface = row.get('surface', 'unknown')
        
        # Base weights by road type
        base_weights = {
            'motorway': 1.0,
            'trunk': 1.2,
            'primary': 1.5,
            'secondary': 2.0,
            'tertiary': 2.5,
            'residential': 3.0,
            'service': 4.0,
            'track': 5.0,
            'path': 8.0,
            'footway': 10.0,
        }
        
        weight = base_weights.get(highway_type, 3.0)
        
        # Surface penalties
        if surface in ['unpaved', 'gravel', 'dirt']:
            weight *= 1.5
        elif surface in ['grass', 'sand']:
            weight *= 2.0
        
        # Oneway bonus 
        if row.get('oneway', 'no') == 'yes':
            weight *= 0.9
        
        return weight
    
    def _estimate_speed_limit(self, row) -> int:
        """Estimate speed limit in km/h"""
        # Explicit maxspeed tag
        if 'maxspeed' in row and row['maxspeed']:
            try:
                return int(row['maxspeed'])
            except:
                pass
        
        # Defaults by highway type
        highway_type = row.get('highway', 'unclassified')
        defaults = {
            'motorway': 120,
            'trunk': 100,
            'primary': 80,
            'secondary': 60,
            'tertiary': 50,
            'residential': 30,
            'service': 20,
            'track': 15,
        }
        return defaults.get(highway_type, 50)
    
    def _estimate_lanes(self, row) -> int:
        """Estimate number of lanes"""
        # Explicit lanes tag
        if 'lanes' in row and row['lanes']:
            try:
                return int(row['lanes'])
            except:
                pass
        
        # Estimate from width
        width = self._estimate_road_width(row)
        return max(1, int(width / 3.5))
    
    def _calculate_road_confidence(self, row) -> float:
        """Calculate confidence score for road data quality"""
        score = 0.5  # Base score
        
        # Has explicit width/lanes
        if 'width' in row and row['width']:
            score += 0.15
        if 'lanes' in row and row['lanes']:
            score += 0.15
        
        # Has surface info
        if 'surface' in row and row['surface']:
            score += 0.1
        
        # Has speed limit
        if 'maxspeed' in row and row['maxspeed']:
            score += 0.1
        
        # Geometry quality
        if row.geometry.is_valid and not row.geometry.is_empty:
            score += 0.1
        
        return min(score, 1.0)
    
    def save_enriched_data(self, 
                          buildings_gdf: gpd.GeoDataFrame,
                          roads_gdf: gpd.GeoDataFrame,
                          output_dir: str):
        """
        Save enriched data to output directory
        
        Args:
            buildings_gdf: Enriched buildings
            roads_gdf: Enriched roads
            output_dir: Output directory path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save buildings
        buildings_gdf.to_file(
            output_path / 'buildings_enriched.geojson',
            driver='GeoJSON'
        )
        
        # Save roads
        roads_gdf.to_file(
            output_path / 'roads_enriched.geojson',
            driver='GeoJSON'
        )
        
        # Save metadata
        metadata = {
            'buildings': {
                'count': len(buildings_gdf),
                'avg_confidence': float(buildings_gdf['confidence'].mean()),
                'usage_distribution': buildings_gdf['usage_type'].value_counts().to_dict(),
                'lod_distribution': buildings_gdf['lod_class'].value_counts().to_dict(),
            },
            'roads': {
                'count': len(roads_gdf),
                'avg_confidence': float(roads_gdf['confidence'].mean()),
                'type_distribution': roads_gdf['road_type'].value_counts().to_dict(),
                'total_length_km': float(roads_gdf['length_m'].sum() / 1000),
            }
        }
        
        with open(output_path / 'enrichment_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Enriched data saved to {output_dir}")
        print(f"  - Buildings: {len(buildings_gdf)} features")
        print(f"  - Roads: {len(roads_gdf)} features")


# Example usage
if __name__ == "__main__":
    # Initialize enricher
    enricher = FeatureEnricher(dem_path='data/normalized/dem_utm.tif')
    
    # Load clean data
    buildings = gpd.read_file('data/clean/buildings_clean.geojson')
    roads = gpd.read_file('data/clean/roads_clean.geojson')
    
    # Enrich
    buildings_enriched = enricher.enrich_buildings(buildings)
    roads_enriched = enricher.enrich_roads(roads)
    
    # Save
    enricher.save_enriched_data(
        buildings_enriched,
        roads_enriched,
        'data/features'
    )