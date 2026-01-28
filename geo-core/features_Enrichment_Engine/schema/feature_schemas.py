"""
Schema definitions for enriched features
Ensures consistent data structure across pipeline
"""

from typing import Dict, Any, List
from enum import Enum


class UsageType(str, Enum):
    """Building usage categories"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    INSTITUTIONAL = "institutional"
    RELIGIOUS = "religious"
    RECREATIONAL = "recreational"
    AGRICULTURAL = "agricultural"
    OTHER = "other"


class RoadType(str, Enum):
    """Road classification categories"""
    HIGHWAY = "highway"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    RESIDENTIAL = "residential"
    SERVICE = "service"
    PEDESTRIAN = "pedestrian"
    OTHER = "other"


class LODClass(int, Enum):
    """Level of Detail classes"""
    VERY_LOW = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4


# Building Schema Definition
BUILDING_SCHEMA = {
    "type": "object",
    "required": [
        "geometry",
        "height_m",
        "usage_type",
        "lod_class",
        "footprint_area_m2",
        "perimeter_m",
        "confidence"
    ],
    "properties": {
        "geometry": {
            "type": "Polygon",
            "description": "Building footprint geometry"
        },
        "height_m": {
            "type": "float",
            "minimum": 0,
            "maximum": 1000,
            "description": "Building height in meters"
        },
        "usage_type": {
            "type": "string",
            "enum": [e.value for e in UsageType],
            "description": "Primary building usage classification"
        },
        "lod_class": {
            "type": "integer",
            "minimum": 0,
            "maximum": 4,
            "description": "Level of Detail class for rendering"
        },
        "footprint_area_m2": {
            "type": "float",
            "minimum": 0,
            "description": "Building footprint area in square meters"
        },
        "perimeter_m": {
            "type": "float",
            "minimum": 0,
            "description": "Building perimeter in meters"
        },
        "confidence": {
            "type": "float",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Data quality confidence score"
        },
        # Optional OSM attributes
        "building": {
            "type": "string",
            "description": "Original OSM building tag"
        },
        "building:levels": {
            "type": "string",
            "description": "Number of building levels from OSM"
        },
        "amenity": {
            "type": "string",
            "description": "OSM amenity tag"
        },
        "name": {
            "type": "string",
            "description": "Building name if available"
        }
    }
}


# Road Schema Definition
ROAD_SCHEMA = {
    "type": "object",
    "required": [
        "geometry",
        "width_m",
        "road_type",
        "nav_weight",
        "length_m",
        "speed_limit_kmh",
        "lanes",
        "confidence"
    ],
    "properties": {
        "geometry": {
            "type": "LineString",
            "description": "Road centerline geometry"
        },
        "width_m": {
            "type": "float",
            "minimum": 0,
            "maximum": 100,
            "description": "Road width in meters"
        },
        "road_type": {
            "type": "string",
            "enum": [e.value for e in RoadType],
            "description": "Road classification for simulation"
        },
        "nav_weight": {
            "type": "float",
            "minimum": 0,
            "description": "AI navigation weight (lower = preferred route)"
        },
        "length_m": {
            "type": "float",
            "minimum": 0,
            "description": "Road segment length in meters"
        },
        "speed_limit_kmh": {
            "type": "integer",
            "minimum": 0,
            "maximum": 200,
            "description": "Speed limit in kilometers per hour"
        },
        "lanes": {
            "type": "integer",
            "minimum": 1,
            "maximum": 12,
            "description": "Number of lanes"
        },
        "confidence": {
            "type": "float",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Data quality confidence score"
        },
        # Optional OSM attributes
        "highway": {
            "type": "string",
            "description": "Original OSM highway tag"
        },
        "surface": {
            "type": "string",
            "description": "Road surface type"
        },
        "oneway": {
            "type": "string",
            "description": "Oneway restriction"
        },
        "name": {
            "type": "string",
            "description": "Road name if available"
        },
        "ref": {
            "type": "string",
            "description": "Road reference number"
        }
    }
}


# Terrain Schema Definition
TERRAIN_SCHEMA = {
    "elevation": {
        "format": "GeoTIFF",
        "dtype": "float32",
        "nodata": -9999,
        "unit": "meters",
        "description": "Terrain elevation above sea level"
    },
    "slope": {
        "format": "GeoTIFF",
        "dtype": "float32",
        "nodata": -9999,
        "unit": "degrees",
        "range": [0, 90],
        "description": "Terrain slope angle"
    },
    "aspect": {
        "format": "GeoTIFF",
        "dtype": "float32",
        "nodata": -9999,
        "unit": "degrees",
        "range": [0, 360],
        "description": "Terrain aspect (compass direction)"
    },
    "curvature": {
        "format": "GeoTIFF",
        "dtype": "float32",
        "nodata": -9999,
        "unit": "1/meters",
        "description": "Terrain curvature"
    }
}


# AI Classification Schema
AI_LANDUSE_SCHEMA = {
    "landuse": {
        "format": "GeoTIFF",
        "dtype": "uint8",
        "nodata": 255,
        "classes": {
            0: "urban",
            1: "forest",
            2: "grassland",
            3: "water",
            4: "bare_land",
            5: "agriculture"
        },
        "description": "AI-classified land use"
    },
    "confidence_map": {
        "format": "GeoTIFF",
        "dtype": "float32",
        "nodata": -1,
        "range": [0, 1],
        "description": "Per-pixel classification confidence"
    }
}


# Vegetation Schema
VEGETATION_SCHEMA = {
    "tree_density": {
        "format": "GeoTIFF",
        "dtype": "float32",
        "nodata": -9999,
        "unit": "trees_per_hectare",
        "range": [0, 10000],
        "description": "Estimated tree density"
    },
    "grass_density": {
        "format": "GeoTIFF",
        "dtype": "float32",
        "nodata": -9999,
        "unit": "percent_coverage",
        "range": [0, 100],
        "description": "Grass coverage percentage"
    },
    "vegetation_height": {
        "format": "GeoTIFF",
        "dtype": "float32",
        "nodata": -9999,
        "unit": "meters",
        "description": "Average vegetation height"
    }
}


# Metadata Schema
METADATA_SCHEMA = {
    "type": "object",
    "required": [
        "version",
        "crs",
        "bounds",
        "processing_date",
        "data_sources"
    ],
    "properties": {
        "version": {
            "type": "string",
            "description": "Schema version"
        },
        "crs": {
            "type": "string",
            "description": "Coordinate Reference System (EPSG code)"
        },
        "bounds": {
            "type": "object",
            "properties": {
                "minx": {"type": "float"},
                "miny": {"type": "float"},
                "maxx": {"type": "float"},
                "maxy": {"type": "float"}
            },
            "description": "Bounding box in CRS units"
        },
        "processing_date": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of processing"
        },
        "data_sources": {
            "type": "object",
            "description": "Source data information"
        },
        "statistics": {
            "type": "object",
            "description": "Dataset statistics"
        }
    }
}


def validate_building_schema(feature_dict: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate a building feature against schema
    
    Args:
        feature_dict: Feature properties dictionary
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    for field in BUILDING_SCHEMA["required"]:
        if field == "geometry":
            continue  # Geometry checked separately
        if field not in feature_dict:
            errors.append(f"Missing required field: {field}")
    
    # Check data types and ranges
    if "height_m" in feature_dict:
        val = feature_dict["height_m"]
        if not isinstance(val, (int, float)) or val < 0 or val > 1000:
            errors.append(f"Invalid height_m: {val}")
    
    if "usage_type" in feature_dict:
        val = feature_dict["usage_type"]
        if val not in [e.value for e in UsageType]:
            errors.append(f"Invalid usage_type: {val}")
    
    if "lod_class" in feature_dict:
        val = feature_dict["lod_class"]
        if not isinstance(val, int) or val < 0 or val > 4:
            errors.append(f"Invalid lod_class: {val}")
    
    if "confidence" in feature_dict:
        val = feature_dict["confidence"]
        if not isinstance(val, (int, float)) or val < 0 or val > 1:
            errors.append(f"Invalid confidence: {val}")
    
    return len(errors) == 0, errors


def validate_road_schema(feature_dict: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate a road feature against schema
    
    Args:
        feature_dict: Feature properties dictionary
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    for field in ROAD_SCHEMA["required"]:
        if field == "geometry":
            continue
        if field not in feature_dict:
            errors.append(f"Missing required field: {field}")
    
    # Check data types and ranges
    if "width_m" in feature_dict:
        val = feature_dict["width_m"]
        if not isinstance(val, (int, float)) or val < 0 or val > 100:
            errors.append(f"Invalid width_m: {val}")
    
    if "road_type" in feature_dict:
        val = feature_dict["road_type"]
        if val not in [e.value for e in RoadType]:
            errors.append(f"Invalid road_type: {val}")
    
    if "speed_limit_kmh" in feature_dict:
        val = feature_dict["speed_limit_kmh"]
        if not isinstance(val, int) or val < 0 or val > 200:
            errors.append(f"Invalid speed_limit_kmh: {val}")
    
    if "lanes" in feature_dict:
        val = feature_dict["lanes"]
        if not isinstance(val, int) or val < 1 or val > 12:
            errors.append(f"Invalid lanes: {val}")
    
    if "confidence" in feature_dict:
        val = feature_dict["confidence"]
        if not isinstance(val, (int, float)) or val < 0 or val > 1:
            errors.append(f"Invalid confidence: {val}")
    
    return len(errors) == 0, errors


def get_schema_version() -> str:
    """Get current schema version"""
    return "1.0.0"


def export_schemas_to_json(output_path: str):
    """
    Export all schemas to JSON file for documentation
    
    Args:
        output_path: Path to save schema JSON
    """
    import json
    from pathlib import Path
    
    schemas = {
        "version": get_schema_version(),
        "buildings": BUILDING_SCHEMA,
        "roads": ROAD_SCHEMA,
        "terrain": TERRAIN_SCHEMA,
        "ai_landuse": AI_LANDUSE_SCHEMA,
        "vegetation": VEGETATION_SCHEMA,
        "metadata": METADATA_SCHEMA
    }
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w') as f:
        json.dump(schemas, f, indent=2)
    
    print(f"✓ Schemas exported to {output_path}")


if __name__ == "__main__":
    # Export schemas
    export_schemas_to_json("schemas/feature_schemas.json")
    
    # Example validation
    test_building = {
        "height_m": 12.5,
        "usage_type": "residential",
        "lod_class": 2,
        "footprint_area_m2": 150.0,
        "perimeter_m": 50.0,
        "confidence": 0.85
    }
    
    valid, errors = validate_building_schema(test_building)
    print(f"\nBuilding validation: {'✓ PASS' if valid else '✗ FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")