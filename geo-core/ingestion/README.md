# geo_spatial

## Data Download Instructions (Manual)

This project expects raw data to be downloaded manually from official sources to ensure correctness, licensing compliance, and reproducibility.

---

## DEM Download (SRTM – NASA)

**Source:** USGS EarthExplorer  
**Website:** https://earthexplorer.usgs.gov/

### Steps

1. Open the website:  
   https://earthexplorer.usgs.gov/

2. Create a **free USGS account** and log in.

3. In the **Search Criteria** tab:
   - Search location: type **Mumbai**
   - Or use map to draw/select region

4. Go to **Data Sets** tab:
   - Expand **Digital Elevation**
   - Select **SRTM**
   - Choose **SRTM 1 Arc-Second Global**

5. Click **Results**
6. Download the **`.tif`** file

### Store file at
data/raw/dem/

---

## Satellite Imagery Download (Sentinel-2 L2A)

**Source:** Copernicus Data Space  
**Website:** https://dataspace.copernicus.eu/

### Steps

1. Open the website:  
   https://dataspace.copernicus.eu/

2. Create a **free Copernicus account** and log in.

3. Search location:
   - Type **Mumbai**
   - Or select region on the map

4. Select product:
   - **Sentinel-2**
   - **Level-2A (L2A)**

5. Choose a cloud-free acquisition date

6. Download the product

### You will get
- Multiple `*.jp2` files (bands)

### Store files at
data/raw/satellite/

---

## OpenStreetMap (OSM) Download

**Source:** Geofabrik  
**Website:** https://download.geofabrik.de/

### Steps

1. Open the website:  
   https://download.geofabrik.de/

2. Navigate through:
Asia → India → Maharashtra

3. Download one of the following:
   - `*.osm.pbf` (recommended)
   - or `*.geojson`

### Store file at
data/raw/osm/

---

## How to Run the Data Ingestion Engine

### Prerequisites

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Project

#### Option 1: Run All Data Types (Recommended)

```bash
python scripts/ingest.py --place "Mumbai City, Maharashtra, India"
```

This will ingest:
- DEM data (from `data/raw/dem/`)
- Satellite data (from `data/raw/satellite/`)
- OSM Buildings, Roads, and Water (downloaded from OpenStreetMap)

#### Option 2: Run Individual Modules

**DEM only:**
```bash
python scripts/ingest.py --dem-only --dem-file path/to/dem.tif
```

**Satellite only:**
```bash
python scripts/ingest.py --satellite-only --satellite-file path/to/satellite.jp2
```

**OSM only:**
```bash
python scripts/ingest.py --osm-only --place "Mumbai City, Maharashtra, India"
```

#### Option 3: Run Individual Scripts Directly

**DEM ingestion:**
```bash
python scripts/dem_ingest.py --source SRTM
```

**Satellite ingestion:**
```bash
python scripts/satellite_ingest.py --file path/to/satellite.jp2
```

**OSM ingestion:**
```bash
python scripts/osm_ingest.py --place "Mumbai City, Maharashtra, India"
```

### Command Line Arguments

#### Main Script (`ingest.py`)
- `--place` - Place name for OSM data (default: "Mumbai City, Maharashtra, India")
- `--dem-file` - Path to DEM file (optional, will auto-detect if not provided)
- `--satellite-file` - Path to satellite file (optional, will auto-detect if not provided)
- `--dem-only` - Ingest DEM only
- `--satellite-only` - Ingest satellite only
- `--osm-only` - Ingest OSM only

#### DEM Script (`dem_ingest.py`)
- `--file` - Path to DEM file (optional)
- `--source` - Data source: SRTM or Copernicus (default: SRTM)

#### Satellite Script (`satellite_ingest.py`)
- `--file` - Path to satellite file (optional)

#### OSM Script (`osm_ingest.py`)
- `--place` - Place name (required)
- `--skip-buildings` - Skip building ingestion
- `--skip-roads` - Skip road ingestion
- `--skip-water` - Skip water feature ingestion

### Example Commands

**Full ingestion:**
```bash
cd geo_spatial
python scripts/ingest.py --place "Mumbai City, Maharashtra, India"
```

**Custom place:**
```bash
python scripts/ingest.py --place "New York City, New York, USA"
```

**With specific files:**
```bash
python scripts/ingest.py --place "Mumbai City, Maharashtra, India" --dem-file data/raw/dem/custom_dem.tif --satellite-file data/raw/satellite/custom_satellite.jp2
```

### Output

After running, check:
- `data/raw/dem/` - DEM files and metadata
- `data/raw/satellite/` - Satellite files and metadata
- `data/raw/osm/` - OSM GeoJSON files and metadata
- `data/raw/metadata.json` - Consolidated metadata for all files

### Troubleshooting

**If dependencies are missing:**
```bash
pip install -r requirements.txt
```

**If OSM download fails:**
- Check internet connection
- Verify place name is correct
- Try a different place name

**If file not found:**
- Ensure raw data files are in the correct directories
- Check file paths are correct
- Verify file formats are supported (.tif, .jp2, .geojson)

---
# 🌍 CRS Handling & Scale Normalization (Phase 1)

> **Engine-safe geospatial preprocessing pipeline**  
> DEM • Satellite • OpenStreetMap  
> **1 unit = 1 meter, guaranteed**

---

## 📌 Overview

This repository implements **CRS detection, reprojection, and scale normalization** for all geospatial datasets used in **Phase 1** of the project.

The goal is to convert raw geospatial data (degrees, mixed CRSs) into a **single, consistent, meter-based Cartesian coordinate system** that is safe for:

- Game engines (Unity, Unreal, Three.js)
- Physics & simulation engines
- ML pipelines
- Accurate spatial analysis

---

## ❓ Why CRS & Scale Normalization Matters

Most geospatial data comes in **latitude/longitude (EPSG:4326)**:

- Units are **degrees**, not meters
- X and Y scales are unequal
- Distance, slope, and alignment are wrong

Most engines assume:

- Flat Cartesian space
- Uniform metric units

### ❌ Without Normalization
- Buildings float above terrain  
- Roads don’t align with DEM  
- Distances are wrong  
- Physics breaks  

### ✅ With Normalization
- DEM, satellite, roads, buildings align perfectly  
- Distances are correct  
- Ready for engines & simulations  

---

## 🧩 Supported Data Types

| Data | Format | Library |
|----|------|--------|
| DEM | GeoTIFF (`.tif`) | rasterio |
| Satellite Imagery | GeoTIFF (`.tif`) | rasterio |
| OpenStreetMap | GeoJSON / GeoDataFrame | geopandas |

---

## 🧠 Architecture Overview

The pipeline is split into **two strict stages**:

1. **CRS Detection & Reprojection**  
2. **Scale Normalization (UTM, meters)**  

Raw data is **never modified**.

---

# 🧭 PART 1 — CRS Handling

## 📄 Module: `scripts/crs_handler.py`

Centralized, reusable CRS logic used by **all ingestion scripts**.

### Responsibilities
- Detect CRS from metadata
- Log original CRS
- Reproject **only if required**
- Save results in `data/processed/`

---

### 🛰️ Raster CRS Handling (DEM & Satellite)

```python
handle_raster_crs(input_path, output_path)

```

**Responsibilities**

- ✔ Reads raster CRS  
- ✔ Logs original CRS  
- ✔ Reprojects only if required  
- ✔ Uses nearest-neighbor resampling  
- ✔ Preserves original pixel values  

**Libraries Used**

- `rasterio`
- `rasterio.warp`

---

### 🗺️ Vector CRS Handling (OSM)

**Function**

handle_vector_crs(input_path, output_path)

---
**Responsibilities**

- ✔ Reads vector CRS  
- ✔ Reprojects using `GeoDataFrame.to_crs()`  
- ✔ Preserves topology  
- ✔ Outputs GeoJSON  

**Library Used**

- `geopandas`

---

**At this stage**
- ✔ CRS is consistent across datasets  
- ❌ Units may still be in degrees  

---

# 📐 PART 2 — Scale Normalization (Engine-Safe)

## 🎯 Goal

Ensure:

> **1 unit = 1 meter**

All datasets are converted to a **local UTM projection** so they are safe for engines, simulations, and physics systems.

---

## 🚫 Rules (DO NOT BREAK)

- **Internal CRS:** Local UTM (meters)  
- **Engine CRS:** Cartesian meters  
- **No latitude/longitude past this stage**  

---

## 🛠️ Tools Used

- **GDAL / rasterio** — Raster reprojection  
- **pyproj** — UTM zone detection  
- **geopandas** — Vector reprojection  

---

## 📄 Module Breakdown

### `utm_utils.py`

Determines the correct **local UTM CRS** based on longitude.

**Example**
- Mumbai → EPSG:32643

---

### `normalize_raster_utm.py`

Handles **DEM and Satellite raster normalization**.

**Responsibilities**
- ✔ Converts degrees → meters  
- ✔ Produces square-meter pixels  
- ✔ Aligns rasters spatially  

**Input**
- `data/processed/dem/*.tif`
- `data/processed/satellite/*.tif`

**Output**

- `data/normalized/dem_utm.tif`
- `data/normalized/satellite_utm.tif`

---

### `normalize_vector_utm.py`

Handles **OSM vector normalization** (buildings, roads).

**Responsibilities**
- ✔ Converts geometry units to meters  
- ✔ Preserves topology  

**Input**
- `data/processed/osm/*.geojson`

**Output**
- `data/normalized/buildings_utm.geojson`
- `data/normalized/roads_utm.geojson`

---

## 🧠 Conceptual Example
### Before (Geographic CRS)
- (72.8395, 18.9336)
- Units: degrees

### After (UTM Projected CRS)
- (379245.27, 2095618.92)
- Units: meters

---

## ▶️ How to Run Locally

### 1️⃣ Activate Virtual Environment

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

---

### 2️⃣ Normalize Rasters (DEM + Satellite)
python -m scripts.normalization.normalize_raster_utm

Expected Output
- DEM → UTM
- Satellite → UTM

---

### 3️⃣ Normalize Vectors (Buildings + Roads)
python -m scripts.normalization.normalize_vector_utm

Expected Output
- Buildings → UTM
- Roads → UTM

----

## Guarantees

- ✔ Same CRS
- ✔ Units in meters
- ✔ Perfect spatial alignment
- ✔ Ready for engines, simulations & ML

## 🏁 Status

- ✔ CRS detection completed
- ✔ Scale normalization completed
- ✔ Engine-safe geospatial pipeline ready
