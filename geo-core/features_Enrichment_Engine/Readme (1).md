# Feature Enrichment & Validation Module

```
Phase-1 Validation Notes:
- Attribute and schema validations are enforced
- CRS, geometry, and terrain checks may emit warnings if upstream data is missing
- Warnings do not block Phase-1 exports
```

## 📂 File Structure

```
geosim-studio/
└── 📁 geo-core/                    
    ├── features/
    │   └── enrichment_engine.py          ← Main enrichment logic
    ├── validation/
    │   └── validation_engine.py          ← Main validation logic
    ├── schemas/
    │   ├── feature_schemas.py            ← Schema definitions
    │   └── feature_schemas.json          ← Exported schemas
    ├── cli/
    │   └── geosim_features.py            ← Command-line interface
    ├── data/
    │   ├── clean/                        ← Input (from Module 3)
    │   │   ├── buildings_clean.geojson
    │   │   └── roads_clean.geojson
    │   ├── features/                     ← Output (enrichment)
    │   │   ├── buildings_enriched.geojson
    │   │   ├── roads_enriched.geojson
    │   │   └── enrichment_metadata.json
    │   └── validated/                    ← Output (validation)
    │       └── validation_report.json
    ├── Requirements.txt
    └── Readme.md
```

---

## 🚀 Installation

### 1. Install Dependencies

```bash
pip install -r Requirements.txt
```

### 2. Install CLI Tool

```bash
pip install -e .
```

---

## 💻 Usage

### Option 1: Python API

```python
from features.enrichment_engine import FeatureEnricher
from validation.validation_engine import ValidationEngine
import geopandas as gpd

# Initialize enricher
enricher = FeatureEnricher(dem_path='data/normalized/dem_utm.tif')

# Load clean data
buildings = gpd.read_file('data/clean/buildings_clean.geojson')
roads = gpd.read_file('data/clean/roads_clean.geojson')

# Enrich features
buildings_enriched = enricher.enrich_buildings(buildings)
roads_enriched = enricher.enrich_roads(roads)

# Save enriched data
enricher.save_enriched_data(
    buildings_enriched,
    roads_enriched,
    'data/features'
)

# Validate
validator = ValidationEngine()
results = validator.validate_all('data')
validator.save_report('data/validated/validation_report.json')
```

### Option 2: CLI Commands

#### Enrich Features
```bash
geosim-features enrich \
  -b data/clean/buildings_clean.geojson \
  -r data/clean/roads_clean.geojson \
  -d data/normalized/dem_utm.tif \
  -o data/features/
```

#### Validate Data
```bash
geosim-features validate \
  -d data/ \
  -o data/validated/validation_report.json \
  --min-confidence 0.6 \
  --min-ai-confidence 0.8
```

#### View Statistics
```bash
geosim-features stats \
  -b data/features/buildings_enriched.geojson \
  -r data/features/roads_enriched.geojson
```

#### Run Complete Pipeline
```bash
geosim-features pipeline \
  -b data/clean/buildings_clean.geojson \
  -r data/clean/roads_clean.geojson \
  -d data/normalized/dem_utm.tif \
  -o data/features/
```

#### Export Schemas
```bash
geosim-features export-schemas -o schemas/feature_schemas.json
```

---

## 📊 Output Format

### Buildings (enriched)
```json
{
  "type": "Feature",
  "geometry": { "type": "Polygon", "coordinates": [...] },
  "properties": {
    "height_m": 12.5,
    "usage_type": "residential",
    "lod_class": 2,
    "footprint_area_m2": 150.0,
    "perimeter_m": 50.0,
    "confidence": 0.85,
    "building": "residential",
    "building:levels": "3"
  }
}
```

### Roads (enriched)
```json
{
  "type": "Feature",
  "geometry": { "type": "LineString", "coordinates": [...] },
  "properties": {
    "width_m": 7.0,
    "road_type": "residential",
    "nav_weight": 3.0,
    "length_m": 245.5,
    "speed_limit_kmh": 30,
    "lanes": 2,
    "confidence": 0.75,
    "highway": "residential",
    "surface": "asphalt"
  }
}
```

### Validation Report
```json
{
  "timestamp": "2025-01-17T10:30:00",
  "passed": true,
  "checks": {
    "crs_uniformity": { "passed": true, "crs": "EPSG:32643" },
    "geometry_buildings": { "total_features": 1523, "invalid_count": 0 },
    "buildings_attributes": { "passed": true, "null_counts": {...} },
    "buildings_confidence": { "mean_confidence": 0.82 }
  },
  "errors": [],
  "warnings": [
    {
      "check": "attribute_completeness",
      "feature_type": "buildings",
      "warning": "height_m has 12.5% null values"
    }
  ]
}
```

---

## 🔧 Enrichment Logic

### Buildings

**Height Estimation (Priority Order):**
1. OSM `building:levels` tag → `levels × 3.5m`
2. OSM `height` tag → direct value
3. DEM-based estimation (if available)
4. Default by building type

**Usage Classification:**
- Residential, Commercial, Industrial, Institutional
- Religious, Recreational, Agricultural, Other
- Based on OSM `building` and `amenity` tags

**LOD Assignment:**
- LOD 0: < 10m² (very low detail)
- LOD 1: 10-100m² (low detail)
- LOD 2: 100-500m² (medium detail)
- LOD 3: 500-2000m² (high detail)
- LOD 4: > 2000m² or landmarks (very high detail)

### Roads

**Width Estimation (Priority Order):**
1. OSM `width` tag → direct value
2. OSM `lanes` tag → `lanes × 3.5m`
3. Default by highway type

**Type Classification:**
- Highway, Primary, Secondary, Residential
- Service, Pedestrian, Other
- Based on OSM `highway` tag

**Navigation Weight Calculation:**
- Lower weight = preferred route
- Based on road type, surface quality, oneway status
- Range: 1.0 (motorway) to 10.0 (footway)

---

## ✅ Validation Checks

### 1. CRS Uniformity
- Ensures all datasets use the same coordinate system
- Checks both vector and raster files
- **Critical**: Mixed CRS will cause engine crashes

### 2. Geometry Validity
- Validates polygon/linestring geometry
- Checks for self-intersections, empty geometries
- Provides reasons for invalid geometries

### 3. Attribute Completeness
- Verifies all required attributes exist
- Checks for null values in critical fields
- Warns if > 10% null values

### 4. Schema Validation
- Validates data types (float, int, string)
- Checks value ranges (e.g., height 0-1000m)
- Ensures enum values are valid

### 5. Terrain Continuity
- Checks for NoData/NaN gaps
- Validates against infinite values
- Reports data quality statistics

### 6. AI Confidence
- Validates AI classification confidence
- Checks feature enrichment confidence
- Flags low-confidence areas

### 7. Data Consistency
- Logical checks (height > 0, width > 0)
- Range validation (LOD 0-4, confidence 0-1)
- Cross-attribute validation

## 🔗 Integration Points

### Inputs (from other modules):
- **Module 3**: Clean geometries
  - `data/clean/buildings_clean.geojson`
  - `data/clean/roads_clean.geojson`
- **Module 4**: Terrain data 
  - `data/normalized/dem_utm.tif`

### Outputs (to other modules):
- **Module 9**: Packaged features
  - `data/features/buildings_enriched.geojson`
  - `data/features/roads_enriched.geojson`
  - `data/validated/validation_report.json`

---

## 📚 Key Dependencies

```
geopandas>=0.14.0    # Vector data manipulation
shapely>=2.0.0       # Geometry operations
rasterio>=1.3.0      # Raster data reading
numpy>=1.24.0        # Numerical operations
click>=8.1.0         # CLI framework
pyproj>=3.6.0        # CRS operations
```
