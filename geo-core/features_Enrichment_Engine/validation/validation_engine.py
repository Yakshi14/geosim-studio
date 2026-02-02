"""
Validation & Consistency Engine
Guarantees export safety with schema checks and confidence metrics
"""

import geopandas as gpd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import rasterio
from shapely.geometry import shape
from shapely.validation import explain_validity


class ValidationEngine:
    """Main validation engine for Phase 1 outputs"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize validation engine
        
        Args:
            config: Configuration dict with validation thresholds
        """
        # Start with defaults and merge custom config
        self.config = self._default_config()
        if config:
            self.config.update(config)
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': [],
            'warnings': [],
            'passed': False
        }
    
    def _default_config(self) -> Dict:
        """Default validation configuration"""
        return {
            'min_confidence': 0.6,
            'min_ai_confidence': 0.8,
            'required_crs': None,  # Will be set from first dataset
            'geometry_tolerance': 0.01,
            'max_geometry_errors': 10,
            'required_building_attrs': [
                'height_m', 'usage_type', 'lod_class', 
                'footprint_area_m2', 'confidence'
            ],
            'required_road_attrs': [
                'width_m', 'road_type', 'nav_weight', 
                'length_m', 'speed_limit_kmh', 'lanes', 'confidence'
            ],
            'required_water_attrs': [
                'water_type', 'surface_area_m2', 'perimeter_m',
                'depth_m', 'confidence'
            ],
            'required_terrain_files': [
                'elevation.tif', 'slope.tif', 'aspect.tif'
            ]
        }
    
    def validate_all(self, data_dir: str) -> Dict:
        """
        Run complete validation suite
        
        Args:
            data_dir: Root data directory
            
        Returns:
            Validation report dictionary
        """
        data_path = Path(data_dir)
        
        print("🔍 Starting Phase 1 validation...")
        
        # 1. CRS Uniformity Check
        print("  ├─ Checking CRS uniformity...")
        self._check_crs_uniformity(data_path)
        
        # 2. Geometry Validity Check
        print("  ├─ Validating geometries...")
        self._validate_geometries(data_path)
        
        # 3. Attribute Completeness Check
        print("  ├─ Checking attribute completeness...")
        self._check_attribute_completeness(data_path)
        
        # 4. Terrain Continuity Check
        print("  ├─ Validating terrain continuity...")
        self._validate_terrain_continuity(data_path)
        
        # 5. AI Confidence Check
        print("  ├─ Checking AI confidence thresholds...")
        self._validate_ai_confidence(data_path)
        
        # 6. Schema Validation
        print("  ├─ Validating schemas...")
        self._validate_schemas(data_path)
        
        # 7. Data Consistency Check
        print("  ├─ Checking data consistency...")
        self._check_data_consistency(data_path)
        
        # Determine overall pass/fail
        self.validation_results['passed'] = len(self.validation_results['errors']) == 0
        
        print(f"\n{'✅' if self.validation_results['passed'] else '❌'} Validation complete")
        print(f"  - Errors: {len(self.validation_results['errors'])}")
        print(f"  - Warnings: {len(self.validation_results['warnings'])}")
        
        return self.validation_results
    
    def _check_crs_uniformity(self, data_path: Path):
        """Verify all datasets use the same CRS"""
        crs_dict = {}
        
        # Check vector files
        vector_files = [
            'features/buildings.geojson',
            'features/roads.geojson',
            'features/water.geojson',
            'clean/buildings_clean.geojson',
            'clean/roads_clean.geojson',
            'clean/water_clean.geojson'
        ]
        
        for file in vector_files:
            file_path = data_path / file
            if file_path.exists():
                try:
                    gdf = gpd.read_file(file_path)
                    crs_dict[file] = str(gdf.crs)
                except Exception as e:
                    self.validation_results['errors'].append({
                        'check': 'crs_uniformity',
                        'file': file,
                        'error': f"Could not read CRS: {e}"
                    })
        
        # Check raster files
        raster_files = [
            'terrain/elevation.tif',
            'terrain/slope.tif',
            'terrain/aspect.tif',
            'normalized/dem_utm.tif'
        ]
        
        for file in raster_files:
            file_path = data_path / file
            if file_path.exists():
                try:
                    with rasterio.open(file_path) as src:
                        crs_dict[file] = str(src.crs)
                except Exception as e:
                    self.validation_results['warnings'].append({
                        'check': 'crs_uniformity',
                        'file': file,
                        'warning': f"Could not read CRS: {e}"
                    })
        
        # Check uniformity
        unique_crs = set(crs_dict.values())
        
        if len(unique_crs) > 1:
            self.validation_results['errors'].append({
                'check': 'crs_uniformity',
                'error': 'Multiple CRS detected',
                'details': crs_dict
            })
        elif len(unique_crs) == 1:
            self.validation_results['checks']['crs_uniformity'] = {
                'passed': True,
                'crs': list(unique_crs)[0],
                'files_checked': len(crs_dict)
            }
        else:
            self.validation_results['warnings'].append({
                'check': 'crs_uniformity',
                'warning': 'No files found to check CRS'
            })
    
    def _validate_geometries(self, data_path: Path):
        """Check geometry validity"""
        geometry_issues = []
        
        vector_files = [
            ('buildings', 'features/buildings.geojson'),
            ('roads', 'features/roads.geojson'),
            ('water', 'features/water.geojson')
        ]
        
        for name, file in vector_files:
            file_path = data_path / file
            if not file_path.exists():
                self.validation_results['warnings'].append({
                    'check': 'geometry_validity',
                    'warning': f'File not found: {file}'
                })
                continue
            
            try:
                gdf = gpd.read_file(file_path)
                
                # Check for invalid geometries
                invalid = ~gdf.geometry.is_valid
                invalid_count = invalid.sum()
                
                if invalid_count > 0:
                    # Get reasons for invalidity
                    invalid_geoms = gdf[invalid].geometry
                    reasons = [explain_validity(geom) for geom in invalid_geoms[:5]]  # First 5
                    
                    if invalid_count > self.config['max_geometry_errors']:
                        self.validation_results['errors'].append({
                            'check': 'geometry_validity',
                            'feature_type': name,
                            'error': f'{invalid_count} invalid geometries (max allowed: {self.config["max_geometry_errors"]})',
                            'sample_reasons': reasons
                        })
                    else:
                        self.validation_results['warnings'].append({
                            'check': 'geometry_validity',
                            'feature_type': name,
                            'warning': f'{invalid_count} invalid geometries',
                            'sample_reasons': reasons
                        })
                
                # Check for empty geometries
                empty = gdf.geometry.is_empty
                empty_count = empty.sum()
                
                if empty_count > 0:
                    self.validation_results['warnings'].append({
                        'check': 'geometry_validity',
                        'feature_type': name,
                        'warning': f'{empty_count} empty geometries'
                    })
                
                # Store results
                self.validation_results['checks'][f'geometry_{name}'] = {
                    'total_features': len(gdf),
                    'invalid_count': int(invalid_count),
                    'empty_count': int(empty_count),
                    'passed': invalid_count <= self.config['max_geometry_errors']
                }
                
            except Exception as e:
                self.validation_results['errors'].append({
                    'check': 'geometry_validity',
                    'feature_type': name,
                    'error': str(e)
                })
    
    def _check_attribute_completeness(self, data_path: Path):
        """Check that all required attributes exist"""
        
        # Buildings
        buildings_file = data_path / 'features/buildings.geojson'
        if buildings_file.exists():
            try:
                gdf = gpd.read_file(buildings_file)
                missing_attrs = self._check_required_attributes(
                    gdf,
                    self.config['required_building_attrs'],
                    'buildings'
                )
                
                if missing_attrs:
                    self.validation_results['errors'].append({
                        'check': 'attribute_completeness',
                        'feature_type': 'buildings',
                        'error': 'Missing required attributes',
                        'missing': missing_attrs
                    })
                else:
                    # Check for null values
                    null_counts = self._check_null_values(
                        gdf,
                        self.config['required_building_attrs']
                    )
                    
                    self.validation_results['checks']['buildings_attributes'] = {
                        'passed': True,
                        'null_counts': null_counts
                    }
                    
                    # Warn if high null percentage
                    for attr, count in null_counts.items():
                        pct = (count / len(gdf)) * 100
                        if pct > 10:
                            self.validation_results['warnings'].append({
                                'check': 'attribute_completeness',
                                'feature_type': 'buildings',
                                'warning': f'{attr} has {pct:.1f}% null values'
                            })
            except Exception as e:
                self.validation_results['errors'].append({
                    'check': 'attribute_completeness',
                    'feature_type': 'buildings',
                    'error': str(e)
                })
        
        # Roads
        roads_file = data_path / 'features/roads.geojson'
        if roads_file.exists():
            try:
                gdf = gpd.read_file(roads_file)
                missing_attrs = self._check_required_attributes(
                    gdf,
                    self.config['required_road_attrs'],
                    'roads'
                )
                
                if missing_attrs:
                    self.validation_results['errors'].append({
                        'check': 'attribute_completeness',
                        'feature_type': 'roads',
                        'error': 'Missing required attributes',
                        'missing': missing_attrs
                    })
                else:
                    # Check for null values
                    null_counts = self._check_null_values(
                        gdf,
                        self.config['required_road_attrs']
                    )
                    
                    self.validation_results['checks']['roads_attributes'] = {
                        'passed': True,
                        'null_counts': null_counts
                    }
                    
                    # Warn if high null percentage
                    for attr, count in null_counts.items():
                        pct = (count / len(gdf)) * 100
                        if pct > 10:
                            self.validation_results['warnings'].append({
                                'check': 'attribute_completeness',
                                'feature_type': 'roads',
                                'warning': f'{attr} has {pct:.1f}% null values'
                            })
            except Exception as e:
                self.validation_results['errors'].append({
                    'check': 'attribute_completeness',
                    'feature_type': 'roads',
                    'error': str(e)
                })
        
        # Water
        water_file = data_path / 'features/water.geojson'
        if water_file.exists():
            try:
                gdf = gpd.read_file(water_file)
                missing_attrs = self._check_required_attributes(
                    gdf,
                    self.config['required_water_attrs'],
                    'water'
                )
                
                if missing_attrs:
                    self.validation_results['errors'].append({
                        'check': 'attribute_completeness',
                        'feature_type': 'water',
                        'error': 'Missing required attributes',
                        'missing': missing_attrs
                    })
                else:
                    # Check for null values
                    null_counts = self._check_null_values(
                        gdf,
                        self.config['required_water_attrs']
                    )
                    
                    self.validation_results['checks']['water_attributes'] = {
                        'passed': True,
                        'null_counts': null_counts
                    }
                    
                    # Warn if high null percentage
                    for attr, count in null_counts.items():
                        pct = (count / len(gdf)) * 100
                        if pct > 10:
                            self.validation_results['warnings'].append({
                                'check': 'attribute_completeness',
                                'feature_type': 'water',
                                'warning': f'{attr} has {pct:.1f}% null values'
                            })
            except Exception as e:
                self.validation_results['errors'].append({
                    'check': 'attribute_completeness',
                    'feature_type': 'water',
                    'error': str(e)
                })
    
    def _check_required_attributes(self, gdf: gpd.GeoDataFrame, 
                                   required: List[str], 
                                   feature_type: str) -> List[str]:
        """Check for missing required attributes"""
        existing = set(gdf.columns)
        required_set = set(required)
        missing = list(required_set - existing)
        return missing
    
    def _check_null_values(self, gdf: gpd.GeoDataFrame, 
                          attributes: List[str]) -> Dict[str, int]:
        """Count null values in required attributes"""
        null_counts = {}
        for attr in attributes:
            if attr in gdf.columns:
                null_counts[attr] = int(gdf[attr].isnull().sum())
        return null_counts
    
    def _validate_terrain_continuity(self, data_path: Path):
        """Check terrain data for gaps and consistency"""
        terrain_checks = {}
        
        for file in self.config['required_terrain_files']:
            file_path = data_path / 'terrain' / file
            
            if not file_path.exists():
                self.validation_results['warnings'].append({
                    'check': 'terrain_continuity',
                    'warning': f'Terrain file not found: {file}'
                })
                continue
            
            try:
                with rasterio.open(file_path) as src:
                    data = src.read(1)
                    
                    # Check for NoData values
                    nodata = src.nodata
                    if nodata is not None:
                        nodata_count = np.sum(data == nodata)
                        nodata_pct = (nodata_count / data.size) * 100
                    else:
                        nodata_count = 0
                        nodata_pct = 0
                    
                    # Check for NaN values
                    nan_count = np.sum(np.isnan(data))
                    nan_pct = (nan_count / data.size) * 100
                    
                    # Check for infinite values
                    inf_count = np.sum(np.isinf(data))
                    inf_pct = (inf_count / data.size) * 100
                    
                    terrain_checks[file] = {
                        'shape': data.shape,
                        'nodata_pct': float(nodata_pct),
                        'nan_pct': float(nan_pct),
                        'inf_pct': float(inf_pct),
                        'min': float(np.nanmin(data[~np.isinf(data)])) if data.size > 0 else None,
                        'max': float(np.nanmax(data[~np.isinf(data)])) if data.size > 0 else None,
                        'mean': float(np.nanmean(data[~np.isinf(data)])) if data.size > 0 else None
                    }
                    
                    # Warn on high gaps
                    if nodata_pct > 5 or nan_pct > 5:
                        self.validation_results['warnings'].append({
                            'check': 'terrain_continuity',
                            'file': file,
                            'warning': f'High NoData/NaN percentage: {nodata_pct + nan_pct:.1f}%'
                        })
                    
                    if inf_pct > 0:
                        self.validation_results['errors'].append({
                            'check': 'terrain_continuity',
                            'file': file,
                            'error': f'Contains infinite values: {inf_pct:.1f}%'
                        })
                        
            except Exception as e:
                self.validation_results['errors'].append({
                    'check': 'terrain_continuity',
                    'file': file,
                    'error': str(e)
                })
        
        self.validation_results['checks']['terrain_continuity'] = terrain_checks
    
    def _validate_ai_confidence(self, data_path: Path):
        """Check AI confidence thresholds"""
        
        # Check land-use AI confidence
        landuse_file = data_path / 'ai/landuse.tif'
        confidence_file = data_path / 'ai/confidence_map.tif'
        
        if confidence_file.exists():
            try:
                with rasterio.open(confidence_file) as src:
                    confidence_data = src.read(1)
                    
                    # Calculate statistics
                    valid_data = confidence_data[~np.isnan(confidence_data)]
                    mean_confidence = float(np.mean(valid_data))
                    min_confidence = float(np.min(valid_data))
                    low_confidence_pct = float(np.sum(valid_data < self.config['min_ai_confidence']) / len(valid_data) * 100)
                    
                    ai_check = {
                        'mean_confidence': mean_confidence,
                        'min_confidence': min_confidence,
                        'low_confidence_pct': low_confidence_pct,
                        'threshold': self.config['min_ai_confidence'],
                        'passed': mean_confidence >= self.config['min_ai_confidence']
                    }
                    
                    self.validation_results['checks']['ai_landuse_confidence'] = ai_check
                    
                    if not ai_check['passed']:
                        self.validation_results['warnings'].append({
                            'check': 'ai_confidence',
                            'warning': f'Mean AI confidence ({mean_confidence:.2f}) below threshold ({self.config["min_ai_confidence"]})'
                        })
                    
                    if low_confidence_pct > 20:
                        self.validation_results['warnings'].append({
                            'check': 'ai_confidence',
                            'warning': f'{low_confidence_pct:.1f}% of pixels have low confidence'
                        })
                        
            except Exception as e:
                self.validation_results['errors'].append({
                    'check': 'ai_confidence',
                    'error': f'Could not validate AI confidence: {e}'
                })
        
        # Check feature confidence scores
        for feature_type in ['buildings', 'roads', 'water']:
            file_path = data_path / f'features/{feature_type}.geojson'
            if file_path.exists():
                try:
                    gdf = gpd.read_file(file_path)
                    if 'confidence' in gdf.columns:
                        mean_conf = float(gdf['confidence'].mean())
                        low_conf_count = int((gdf['confidence'] < self.config['min_confidence']).sum())
                        low_conf_pct = (low_conf_count / len(gdf)) * 100
                        
                        self.validation_results['checks'][f'{feature_type}_confidence'] = {
                            'mean_confidence': mean_conf,
                            'low_confidence_count': low_conf_count,
                            'low_confidence_pct': float(low_conf_pct),
                            'threshold': self.config['min_confidence']
                        }
                        
                        if low_conf_pct > 15:
                            self.validation_results['warnings'].append({
                                'check': 'feature_confidence',
                                'feature_type': feature_type,
                                'warning': f'{low_conf_pct:.1f}% features have low confidence'
                            })
                except Exception as e:
                    self.validation_results['warnings'].append({
                        'check': 'feature_confidence',
                        'feature_type': feature_type,
                        'warning': f'Could not check confidence: {e}'
                    })
    
    def _validate_schemas(self, data_path: Path):
        """Validate data type schemas"""
        
        # Define expected schemas
        schemas = {
            'buildings': {
                'height_m': float,
                'usage_type': str,
                'lod_class': int,
                'footprint_area_m2': float,
                'perimeter_m': float,
                'confidence': float
            },
            'roads': {
                'width_m': float,
                'road_type': str,
                'nav_weight': float,
                'length_m': float,
                'speed_limit_kmh': int,
                'lanes': int,
                'confidence': float
            },
            'water': {
                'water_type': str,
                'surface_area_m2': float,
                'perimeter_m': float,
                'depth_m': float,
                'confidence': float
            }
        }
        
        for feature_type, schema in schemas.items():
            file_path = data_path / f'features/{feature_type}.geojson'
            if not file_path.exists():
                continue
            
            try:
                gdf = gpd.read_file(file_path)
                schema_errors = []
                
                for attr, expected_type in schema.items():
                    if attr not in gdf.columns:
                        continue
                    
                    # Check data types
                    actual_dtype = gdf[attr].dtype
                    
                    if expected_type == float:
                        if not np.issubdtype(actual_dtype, np.floating) and not np.issubdtype(actual_dtype, np.integer):
                            schema_errors.append(f'{attr}: expected numeric, got {actual_dtype}')
                    elif expected_type == int:
                        if not np.issubdtype(actual_dtype, np.integer):
                            schema_errors.append(f'{attr}: expected integer, got {actual_dtype}')
                    elif expected_type == str:
                        # Pandas stores strings as 'object' dtype or 'string' dtype
                        # Accept: object, string, str (various representations)
                        dtype_str = str(actual_dtype).lower()
                        dtype_name = actual_dtype.name.lower()
                        
                        is_string_dtype = (
                            actual_dtype == np.object_ or 
                            dtype_name == 'object' or
                            dtype_name == 'string' or
                            dtype_str == 'object' or
                            dtype_str == 'string' or
                            dtype_str == 'str' or
                            'string' in dtype_str or
                            'object' in dtype_str
                        )
                        
                        if not is_string_dtype:
                            schema_errors.append(f'{attr}: expected string, got {actual_dtype}')
                
                if schema_errors:
                    self.validation_results['errors'].append({
                        'check': 'schema_validation',
                        'feature_type': feature_type,
                        'error': 'Schema type mismatches',
                        'details': schema_errors
                    })
                else:
                    self.validation_results['checks'][f'{feature_type}_schema'] = {
                        'passed': True,
                        'attributes_checked': len(schema)
                    }
                    
            except Exception as e:
                self.validation_results['errors'].append({
                    'check': 'schema_validation',
                    'feature_type': feature_type,
                    'error': str(e)
                })
    
    def _check_data_consistency(self, data_path: Path):
        """Check for logical data consistency"""
        
        # Buildings consistency
        buildings_file = data_path / 'features/buildings.geojson'
        if buildings_file.exists():
            try:
                gdf = gpd.read_file(buildings_file)
                issues = []
                
                # Check height > 0
                if 'height_m' in gdf.columns:
                    invalid_height = gdf[gdf['height_m'] <= 0]
                    if len(invalid_height) > 0:
                        issues.append(f'{len(invalid_height)} buildings with height <= 0')
                
                # Check area > 0
                if 'footprint_area_m2' in gdf.columns:
                    invalid_area = gdf[gdf['footprint_area_m2'] <= 0]
                    if len(invalid_area) > 0:
                        issues.append(f'{len(invalid_area)} buildings with area <= 0')
                
                # Check LOD class range
                if 'lod_class' in gdf.columns:
                    invalid_lod = gdf[(gdf['lod_class'] < 0) | (gdf['lod_class'] > 4)]
                    if len(invalid_lod) > 0:
                        issues.append(f'{len(invalid_lod)} buildings with invalid LOD class')
                
                # Check confidence range
                if 'confidence' in gdf.columns:
                    invalid_conf = gdf[(gdf['confidence'] < 0) | (gdf['confidence'] > 1)]
                    if len(invalid_conf) > 0:
                        issues.append(f'{len(invalid_conf)} buildings with invalid confidence')
                
                if issues:
                    self.validation_results['warnings'].append({
                        'check': 'data_consistency',
                        'feature_type': 'buildings',
                        'warning': 'Consistency issues found',
                        'details': issues
                    })
                else:
                    self.validation_results['checks']['buildings_consistency'] = {
                        'passed': True
                    }
                    
            except Exception as e:
                self.validation_results['warnings'].append({
                    'check': 'data_consistency',
                    'feature_type': 'buildings',
                    'warning': str(e)
                })
        
        # Roads consistency
        roads_file = data_path / 'features/roads.geojson'
        if roads_file.exists():
            try:
                gdf = gpd.read_file(roads_file)
                issues = []
                
                # Check width > 0
                if 'width_m' in gdf.columns:
                    invalid_width = gdf[gdf['width_m'] <= 0]
                    if len(invalid_width) > 0:
                        issues.append(f'{len(invalid_width)} roads with width <= 0')
                
                # Check length > 0
                if 'length_m' in gdf.columns:
                    invalid_length = gdf[gdf['length_m'] <= 0]
                    if len(invalid_length) > 0:
                        issues.append(f'{len(invalid_length)} roads with length <= 0')
                
                # Check lanes >= 1
                if 'lanes' in gdf.columns:
                    invalid_lanes = gdf[gdf['lanes'] < 1]
                    if len(invalid_lanes) > 0:
                        issues.append(f'{len(invalid_lanes)} roads with lanes < 1')
                
                # Check speed limit reasonable
                if 'speed_limit_kmh' in gdf.columns:
                    invalid_speed = gdf[(gdf['speed_limit_kmh'] < 0) | (gdf['speed_limit_kmh'] > 200)]
                    if len(invalid_speed) > 0:
                        issues.append(f'{len(invalid_speed)} roads with unrealistic speed limits')
                
                if issues:
                    self.validation_results['warnings'].append({
                        'check': 'data_consistency',
                        'feature_type': 'roads',
                        'warning': 'Consistency issues found',
                        'details': issues
                    })
                else:
                    self.validation_results['checks']['roads_consistency'] = {
                        'passed': True
                    }
                    
            except Exception as e:
                self.validation_results['warnings'].append({
                    'check': 'data_consistency',
                    'feature_type': 'roads',
                    'warning': str(e)
                })
        
        # Water consistency
        water_file = data_path / 'features/water.geojson'
        if water_file.exists():
            try:
                gdf = gpd.read_file(water_file)
                issues = []
                
                # Check area > 0
                if 'surface_area_m2' in gdf.columns:
                    invalid_area = gdf[gdf['surface_area_m2'] <= 0]
                    if len(invalid_area) > 0:
                        issues.append(f'{len(invalid_area)} water bodies with area <= 0')
                
                # Check depth >= 0
                if 'depth_m' in gdf.columns:
                    invalid_depth = gdf[gdf['depth_m'] < 0]
                    if len(invalid_depth) > 0:
                        issues.append(f'{len(invalid_depth)} water bodies with negative depth')
                
                # Check confidence range
                if 'confidence' in gdf.columns:
                    invalid_conf = gdf[(gdf['confidence'] < 0) | (gdf['confidence'] > 1)]
                    if len(invalid_conf) > 0:
                        issues.append(f'{len(invalid_conf)} water bodies with invalid confidence')
                
                if issues:
                    self.validation_results['warnings'].append({
                        'check': 'data_consistency',
                        'feature_type': 'water',
                        'warning': 'Consistency issues found',
                        'details': issues
                    })
                else:
                    self.validation_results['checks']['water_consistency'] = {
                        'passed': True
                    }
                    
            except Exception as e:
                self.validation_results['warnings'].append({
                    'check': 'data_consistency',
                    'feature_type': 'water',
                    'warning': str(e)
                })
    
    def save_report(self, output_path: str):
        """
        Save validation report to JSON file
        
        Args:
            output_path: Path to save report
        """
        report_path = Path(output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_to_serializable(obj):
            """Recursively convert numpy types to Python native types"""
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        serializable_results = convert_to_serializable(self.validation_results)
        
        with open(report_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"✓ Validation report saved to {output_path}")
    
    def print_summary(self):
        """Print human-readable validation summary"""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        if self.validation_results['passed']:
            print("✅ VALIDATION PASSED")
        else:
            print("❌ VALIDATION FAILED")
        
        print(f"\nErrors: {len(self.validation_results['errors'])}")
        for error in self.validation_results['errors']:
            print(f"  ❌ [{error['check']}] {error.get('error', 'Unknown error')}")
        
        print(f"\nWarnings: {len(self.validation_results['warnings'])}")
        for warning in self.validation_results['warnings'][:10]:  # Show first 10
            print(f"  ⚠️  [{warning['check']}] {warning.get('warning', 'Unknown warning')}")
        
        if len(self.validation_results['warnings']) > 10:
            print(f"  ... and {len(self.validation_results['warnings']) - 10} more warnings")
        
        print("\n" + "="*60)


# Example usage
if __name__ == "__main__":
    # Initialize validator
    validator = ValidationEngine()
    
    # Run validation
    results = validator.validate_all('data')
    
    # Save report
    validator.save_report('data/validated/validation_report.json')
    
    # Print summary
    validator.print_summary()
