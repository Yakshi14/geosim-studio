"""
GeoSim Features Pipeline Runner
Fixed version with correct import paths with CLI support
"""

import sys
import os
from pathlib import Path
import click

# Fix import paths - go up two levels to reach project root
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Now import from the correct locations
try:
    from features_Enrichment_Engine.features.enrichment_engine import FeatureEnricher
    from features_Enrichment_Engine.validation.validation_engine import ValidationEngine
    from features_Enrichment_Engine.schema.feature_schemas import export_schemas_to_json
except ModuleNotFoundError:
    # Alternative: try relative imports
    sys.path.insert(0, str(current_dir.parent))
    from features.enrichment_engine import FeatureEnricher
    from validation.validation_engine import ValidationEngine
    from schema.feature_schemas import export_schemas_to_json

import geopandas as gpd
import json
import subprocess

# Create Click group
@click.group()
def cli():
    """GeoSim Feature Enrichment & Validation Pipeline"""
    pass


class GeoSimPipeline:
    """Main pipeline class for feature enrichment and validation"""
    
    def __init__(self, dem_path=None):
        """
        Initialize the pipeline
        
        Args:
            dem_path: Optional path to DEM file for height estimation
        """
        self.dem_path = dem_path
        self.enricher = FeatureEnricher(dem_path=dem_path)
        
    def enrich_features(self, buildings_path, roads_path, water_path, output_dir):
        """
        Enrich building, road, and water features with simulation attributes
        
        Args:
            buildings_path: Path to clean buildings GeoJSON
            roads_path: Path to clean roads GeoJSON
            water_path: Path to clean water GeoJSON
            output_dir: Output directory for enriched features
            
        Returns:
            Tuple of (buildings, roads, water)
        """
        click.echo("🔧 Starting feature enrichment...")
        
        try:
            # Load data
            click.echo(f"  ├─ Loading buildings from {buildings_path}")
            buildings_gdf = gpd.read_file(buildings_path)
            click.echo(f"     └─ Loaded {len(buildings_gdf)} buildings")
            
            click.echo(f"  ├─ Loading roads from {roads_path}")
            roads_gdf = gpd.read_file(roads_path)
            click.echo(f"     └─ Loaded {len(roads_gdf)} roads")
            
            click.echo(f"  ├─ Loading water from {water_path}")
            water_gdf = gpd.read_file(water_path)
            click.echo(f"     └─ Loaded {len(water_gdf)} water bodies")
            
            # Enrich buildings
            click.echo("  ├─ Enriching buildings...")
            buildings_enriched = self.enricher.enrich_buildings(buildings_gdf)
            click.echo(f"     └─ Added: height_m, usage_type, lod_class, confidence")
            
            # Enrich roads
            click.echo("  ├─ Enriching roads...")
            roads_enriched = self.enricher.enrich_roads(roads_gdf)
            click.echo(f"     └─ Added: width_m, road_type, nav_weight, speed_limit_kmh")
            
            # Enrich water
            click.echo("  ├─ Enriching water...")
            water_enriched = self.enricher.enrich_water(water_gdf)
            click.echo(f"     └─ Added: water_type, depth_m, flow_direction, confidence")
            
            # Save
            click.echo(f"  ├─ Saving to {output_dir}")
            self.enricher.save_enriched_data(buildings_enriched, roads_enriched, water_enriched, output_dir)
            
            click.echo("✅ Feature enrichment complete!")
            
            # Print statistics
            self._print_enrichment_stats(buildings_enriched, roads_enriched, water_enriched)
            
            return buildings_enriched, roads_enriched, water_enriched
            
        except Exception as e:
            click.echo(f"❌ Error during enrichment: {e}", err=True)
            raise
    
    def _print_enrichment_stats(self, buildings_enriched, roads_enriched, water_enriched):
        """Print enrichment statistics"""
        click.echo("\n📊 Statistics:")
        click.echo(f"  Buildings:")
        click.echo(f"    - Total: {len(buildings_enriched)}")
        click.echo(f"    - Avg confidence: {buildings_enriched['confidence'].mean():.2f}")
        click.echo(f"    - Usage distribution:")
        for usage, count in buildings_enriched['usage_type'].value_counts().head(5).items():
            click.echo(f"      · {usage}: {count}")
        
        click.echo(f"\n  Roads:")
        click.echo(f"    - Total: {len(roads_enriched)}")
        click.echo(f"    - Total length: {roads_enriched['length_m'].sum()/1000:.1f} km")
        click.echo(f"    - Avg confidence: {roads_enriched['confidence'].mean():.2f}")
        click.echo(f"    - Type distribution:")
        for road_type, count in roads_enriched['road_type'].value_counts().items():
            click.echo(f"      · {road_type}: {count}")
        
        click.echo(f"\n  Water:")
        click.echo(f"    - Total: {len(water_enriched)}")
        click.echo(f"    - Total surface area: {water_enriched['surface_area_m2'].sum()/10000:.2f} hectares")
        click.echo(f"    - Avg confidence: {water_enriched['confidence'].mean():.2f}")
        click.echo(f"    - Type distribution:")
        for water_type, count in water_enriched['water_type'].value_counts().items():
            click.echo(f"      · {water_type}: {count}")
    
    def validate_features(self, data_dir, output_path=None, min_confidence=0.6, min_ai_confidence=0.8):
        """
        Validate Phase 1 outputs for export safety
        
        Args:
            data_dir: Root data directory to validate
            output_path: Output path for validation report
            min_confidence: Minimum confidence threshold
            min_ai_confidence: Minimum AI confidence threshold
            
        Returns:
            Validation results dictionary
        """
        click.echo("🔍 Starting Phase 1 validation...")
        
        try:
            # Configure validator
            config = {
                'min_confidence': min_confidence,
                'min_ai_confidence': min_ai_confidence,
            }
            
            validator = ValidationEngine(config=config)
            
            # Run validation
            results = validator.validate_all(data_dir)
            
            # Save report
            if output_path is None:
                output_path = Path(data_dir) / 'validated/validation_report.json'
            validator.save_report(output_path)
            
            # Print summary
            validator.print_summary()
            
            return results
            
        except Exception as e:
            click.echo(f"❌ Error during validation: {e}", err=True)
            raise
    
    def show_stats(self, buildings_path, roads_path, water_path=None):
        """
        Display detailed statistics for enriched features
        
        Args:
            buildings_path: Path to enriched buildings GeoJSON
            roads_path: Path to enriched roads GeoJSON
            water_path: Path to enriched water GeoJSON (optional)
        """
        click.echo("📊 Feature Statistics\n")
        
        try:
            # Buildings
            click.echo("🏢 BUILDINGS")
            click.echo("="*60)
            buildings_gdf = gpd.read_file(buildings_path)
            
            click.echo(f"Total features: {len(buildings_gdf)}")
            click.echo(f"\nHeight Statistics:")
            click.echo(f"  - Mean: {buildings_gdf['height_m'].mean():.1f} m")
            click.echo(f"  - Median: {buildings_gdf['height_m'].median():.1f} m")
            click.echo(f"  - Min: {buildings_gdf['height_m'].min():.1f} m")
            click.echo(f"  - Max: {buildings_gdf['height_m'].max():.1f} m")
            
            click.echo(f"\nArea Statistics:")
            click.echo(f"  - Mean: {buildings_gdf['footprint_area_m2'].mean():.1f} m²")
            click.echo(f"  - Total: {buildings_gdf['footprint_area_m2'].sum():.1f} m²")
            
            click.echo(f"\nConfidence Distribution:")
            click.echo(f"  - Mean: {buildings_gdf['confidence'].mean():.2f}")
            click.echo(f"  - High (>0.8): {(buildings_gdf['confidence'] > 0.8).sum()}")
            click.echo(f"  - Medium (0.6-0.8): {((buildings_gdf['confidence'] >= 0.6) & (buildings_gdf['confidence'] <= 0.8)).sum()}")
            click.echo(f"  - Low (<0.6): {(buildings_gdf['confidence'] < 0.6).sum()}")
            
            click.echo(f"\nUsage Type Distribution:")
            for usage, count in buildings_gdf['usage_type'].value_counts().items():
                pct = (count / len(buildings_gdf)) * 100
                click.echo(f"  - {usage}: {count} ({pct:.1f}%)")
            
            click.echo(f"\nLOD Class Distribution:")
            for lod, count in buildings_gdf['lod_class'].value_counts().sort_index().items():
                pct = (count / len(buildings_gdf)) * 100
                click.echo(f"  - LOD {lod}: {count} ({pct:.1f}%)")
            
            # Roads
            click.echo("\n\n🛣️  ROADS")
            click.echo("="*60)
            roads_gdf = gpd.read_file(roads_path)
            
            click.echo(f"Total features: {len(roads_gdf)}")
            click.echo(f"Total length: {roads_gdf['length_m'].sum()/1000:.1f} km")
            
            click.echo(f"\nWidth Statistics:")
            click.echo(f"  - Mean: {roads_gdf['width_m'].mean():.1f} m")
            click.echo(f"  - Median: {roads_gdf['width_m'].median():.1f} m")
            click.echo(f"  - Min: {roads_gdf['width_m'].min():.1f} m")
            click.echo(f"  - Max: {roads_gdf['width_m'].max():.1f} m")
            
            click.echo(f"\nConfidence Distribution:")
            click.echo(f"  - Mean: {roads_gdf['confidence'].mean():.2f}")
            click.echo(f"  - High (>0.8): {(roads_gdf['confidence'] > 0.8).sum()}")
            click.echo(f"  - Medium (0.6-0.8): {((roads_gdf['confidence'] >= 0.6) & (roads_gdf['confidence'] <= 0.8)).sum()}")
            click.echo(f"  - Low (<0.6): {(roads_gdf['confidence'] < 0.6).sum()}")
            
            click.echo(f"\nRoad Type Distribution:")
            for road_type, count in roads_gdf['road_type'].value_counts().items():
                pct = (count / len(roads_gdf)) * 100
                length_km = roads_gdf[roads_gdf['road_type'] == road_type]['length_m'].sum() / 1000
                click.echo(f"  - {road_type}: {count} ({pct:.1f}%), {length_km:.1f} km")
            
            click.echo(f"\nSpeed Limit Distribution:")
            for speed, count in roads_gdf['speed_limit_kmh'].value_counts().sort_index().items():
                pct = (count / len(roads_gdf)) * 100
                click.echo(f"  - {speed} km/h: {count} ({pct:.1f}%)")
            
            click.echo(f"\nLanes Distribution:")
            for lanes, count in roads_gdf['lanes'].value_counts().sort_index().items():
                pct = (count / len(roads_gdf)) * 100
                click.echo(f"  - {lanes} lane(s): {count} ({pct:.1f}%)")
            
            # Water
            if water_path:
                click.echo("\n\n🌊 WATER")
                click.echo("="*60)
                water_gdf = gpd.read_file(water_path)
                
                click.echo(f"Total features: {len(water_gdf)}")
                click.echo(f"Total surface area: {water_gdf['surface_area_m2'].sum()/10000:.2f} hectares")
                
                click.echo(f"\nDepth Statistics:")
                click.echo(f"  - Mean: {water_gdf['depth_m'].mean():.1f} m")
                click.echo(f"  - Median: {water_gdf['depth_m'].median():.1f} m")
                click.echo(f"  - Min: {water_gdf['depth_m'].min():.1f} m")
                click.echo(f"  - Max: {water_gdf['depth_m'].max():.1f} m")
                
                click.echo(f"\nSurface Area Statistics:")
                click.echo(f"  - Mean: {water_gdf['surface_area_m2'].mean():.1f} m²")
                click.echo(f"  - Total: {water_gdf['surface_area_m2'].sum():.1f} m²")
                
                click.echo(f"\nConfidence Distribution:")
                click.echo(f"  - Mean: {water_gdf['confidence'].mean():.2f}")
                click.echo(f"  - High (>0.8): {(water_gdf['confidence'] > 0.8).sum()}")
                click.echo(f"  - Medium (0.6-0.8): {((water_gdf['confidence'] >= 0.6) & (water_gdf['confidence'] <= 0.8)).sum()}")
                click.echo(f"  - Low (<0.6): {(water_gdf['confidence'] < 0.6).sum()}")
                
                click.echo(f"\nWater Type Distribution:")
                for water_type, count in water_gdf['water_type'].value_counts().items():
                    pct = (count / len(water_gdf)) * 100
                    area_hectares = water_gdf[water_gdf['water_type'] == water_type]['surface_area_m2'].sum() / 10000
                    click.echo(f"  - {water_type}: {count} ({pct:.1f}%), {area_hectares:.2f} ha")
                
                click.echo(f"\nFlow Direction Distribution:")
                for flow, count in water_gdf['flow_direction'].value_counts().items():
                    pct = (count / len(water_gdf)) * 100
                    click.echo(f"  - {flow}: {count} ({pct:.1f}%)")
            
        except Exception as e:
            click.echo(f"❌ Error showing stats: {e}", err=True)
            raise
    
    def export_schemas(self, output_path='schemas/feature_schemas.json'):
        """
        Export schema definitions to JSON
        
        Args:
            output_path: Output path for schema JSON
        """
        try:
            export_schemas_to_json(output_path)
            click.echo(f"✅ Schemas exported to {output_path}")
        except Exception as e:
            click.echo(f"❌ Error exporting schemas: {e}", err=True)
            raise
    
    def run_complete_pipeline(self, buildings_path, roads_path, water_path, output_dir, 
                             validate=True, min_confidence=0.6, min_ai_confidence=0.8):
        """
        Run complete enrichment and validation pipeline
        
        Args:
            buildings_path: Path to clean buildings GeoJSON
            roads_path: Path to clean roads GeoJSON
            water_path: Path to clean water GeoJSON
            output_dir: Output directory
            validate: Whether to run validation after enrichment
            min_confidence: Minimum confidence threshold
            min_ai_confidence: Minimum AI confidence threshold
            
        Returns:
            Tuple of (enrichment_results, validation_results)
        """
        click.echo("🚀 Starting complete feature pipeline...\n")
        
        #Enrichment
        click.echo("STEP 1: Feature Enrichment")
        click.echo("-"*60)
        buildings_enriched, roads_enriched, water_enriched = self.enrich_features(
            buildings_path, roads_path, water_path, output_dir
        )
        
        validation_results = None
        
        #Validation
        if validate:
            click.echo("\n\nSTEP 2: Validation")
            click.echo("-"*60)

            data_dir = Path(output_dir).parent
            
            validation_results = self.validate_features(
                str(data_dir), 
                output_path=None,
                min_confidence=min_confidence,
                min_ai_confidence=min_ai_confidence
            )
        
        click.echo("\n\n✅ Pipeline complete!")
        
        return (buildings_enriched, roads_enriched), validation_results


# CLI Commands

@cli.command()
@click.option('-b', '--buildings', 'buildings_path', required=True, 
              type=click.Path(exists=True), help='Path to clean buildings GeoJSON')
@click.option('-r', '--roads', 'roads_path', required=True, 
              type=click.Path(exists=True), help='Path to clean roads GeoJSON')
@click.option('-w', '--water', 'water_path', required=True,
              type=click.Path(exists=True), help='Path to clean water GeoJSON')
@click.option('-d', '--dem', 'dem_path', type=click.Path(exists=True), 
              help='Path to DEM file for height estimation (optional)')
@click.option('-o', '--output-dir', 'output_dir', default='./data/features',
              type=click.Path(), help='Output directory for enriched features')
@click.option('--no-validate', is_flag=True, help='Skip validation step')
@click.option('--min-confidence', default=0.6, type=float,
              help='Minimum confidence threshold for validation')
@click.option('--min-ai-confidence', default=0.8, type=float,
              help='Minimum AI confidence threshold for validation')
def enrich(buildings_path, roads_path, water_path, dem_path, output_dir, 
           no_validate, min_confidence, min_ai_confidence):
    """
    Enrich features with simulation attributes
    """
    click.echo("="*70)
    click.echo("GeoSim Feature Enrichment Pipeline")
    click.echo("="*70)
    
    pipeline = GeoSimPipeline(dem_path=dem_path)
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    results = pipeline.run_complete_pipeline(
        buildings_path=buildings_path,
        roads_path=roads_path,
        water_path=water_path,
        output_dir=output_dir,
        validate=not no_validate,
        min_confidence=min_confidence,
        min_ai_confidence=min_ai_confidence
    )
    
    click.echo("\n✅ Enrichment complete!")


@cli.command()
@click.option('-b', '--buildings', 'buildings_path', required=True,
              type=click.Path(exists=True), help='Path to enriched buildings GeoJSON')
@click.option('-r', '--roads', 'roads_path', required=True,
              type=click.Path(exists=True), help='Path to enriched roads GeoJSON')
@click.option('-w', '--water', 'water_path', type=click.Path(exists=True),
              help='Path to enriched water GeoJSON (optional)')
def stats(buildings_path, roads_path, water_path):
    """
    Display detailed statistics for enriched features
    """
    pipeline = GeoSimPipeline()
    pipeline.show_stats(buildings_path, roads_path, water_path)


@cli.command()
@click.option('-d', '--data-dir', 'data_dir', required=True,
              type=click.Path(exists=True), help='Root data directory to validate')
@click.option('-o', '--output', 'output_path', type=click.Path(),
              help='Output path for validation report')
@click.option('--min-confidence', default=0.6, type=float,
              help='Minimum confidence threshold')
@click.option('--min-ai-confidence', default=0.8, type=float,
              help='Minimum AI confidence threshold')
def validate(data_dir, output_path, min_confidence, min_ai_confidence):
    """
    Validate enriched features for export safety
    """
    pipeline = GeoSimPipeline()
    pipeline.validate_features(
        data_dir=data_dir,
        output_path=output_path,
        min_confidence=min_confidence,
        min_ai_confidence=min_ai_confidence
    )


@cli.command()
@click.option('-o', '--output', 'output_path', default='./schemas/feature_schemas.json',
              type=click.Path(), help='Output path for schema JSON')
def export_schemas(output_path):
    """
    Export feature schema definitions to JSON
    """
    pipeline = GeoSimPipeline()
    pipeline.export_schemas(output_path)


@cli.command()
@click.option('-b', '--buildings', 'buildings_path', required=True,
              type=click.Path(exists=True), help='Path to clean buildings GeoJSON')
@click.option('-r', '--roads', 'roads_path', required=True,
              type=click.Path(exists=True), help='Path to clean roads GeoJSON')
@click.option('-w', '--water', 'water_path', required=True,
              type=click.Path(exists=True), help='Path to clean water GeoJSON')
@click.option('-d', '--dem', 'dem_path', type=click.Path(exists=True),
              help='Path to DEM file for height estimation (optional)')
@click.option('-o', '--output-dir', 'output_dir', default='./data/features',
              type=click.Path(), help='Output directory for enriched features')
def run_all(buildings_path, roads_path, water_path, dem_path, output_dir):
    """
    Run the complete GeoSim pipeline (enrichment, validation, and statistics)
    """
    click.echo("Starting complete GeoSim pipeline...")
    
    #Enrichment
    pipeline = GeoSimPipeline(dem_path=dem_path)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    (buildings_enriched, roads_enriched), _ = pipeline.run_complete_pipeline(
        buildings_path=buildings_path,
        roads_path=roads_path,
        water_path=water_path,
        output_dir=output_dir,
        validate=True
    )
    
    #Show statistics
    click.echo("\n\n" + "="*70)
    click.echo("FINAL STATISTICS")
    click.echo("="*70)

    buildings_enriched_path = Path(output_dir) / 'buildings.geojson'
    roads_enriched_path = Path(output_dir) / 'roads.geojson'
    water_enriched_path = Path(output_dir) / 'water.geojson'
    
    if water_enriched_path.exists():
        pipeline.show_stats(
            str(buildings_enriched_path),
            str(roads_enriched_path),
            str(water_enriched_path)
        )
    else:
        pipeline.show_stats(
            str(buildings_enriched_path),
            str(roads_enriched_path)
        )
    
    click.echo("\n✅ Complete pipeline finished successfully!")


@cli.command()
@click.option('-f', '--file', 'batch_file', default='geosim_features.bat',
              type=click.Path(), help='Output batch file name')
@click.option('--python-path', default='python',
              help='Python executable path to use in batch file')
def create_bat(batch_file, python_path):
    """
    Create a Windows batch file for easy CLI usage
    """
    script_path = Path(__file__).absolute()
    
    batch_content = f"""@echo off
echo ========================================
echo GeoSim Feature Pipeline Batch Runner
echo ========================================
echo.

REM Check if Python is available
{python_path} --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python not found!
    echo Please install Python or update your PATH.
    echo You can specify Python path with --python-path option.
    pause
    exit /b 1
)

REM Display help if no arguments
if "%1"=="" (
    echo Usage:
    echo   {Path(batch_file).name} [COMMAND] [OPTIONS]
    echo.
    echo Available commands:
    echo   enrich    - Enrich features with simulation attributes
    echo   stats     - Display detailed statistics
    echo   validate  - Validate enriched features
    echo   run-all   - Run complete pipeline
    echo.
    echo For help on a specific command:
    echo   {Path(batch_file).name} enrich --help
    pause
    exit /b 0
)

REM Run the Python script with all arguments
{python_path} "{script_path}" %*
if %errorlevel% neq 0 (
    echo.
    echo ❌ Command failed with error code %errorlevel%
    pause
    exit /b %errorlevel%
)
"""
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    os.chmod(batch_file, 0o755)
    
    click.echo(f"✅ Batch file created: {batch_file}")
    click.echo("\nUsage examples:")
    click.echo(f"  {batch_file} enrich -b buildings.geojson -r roads.geojson -w water.geojson")
    click.echo(f"  {batch_file} stats -b buildings.geojson -r roads.geojson -w water.geojson")
    click.echo(f"  {batch_file} --help")


@cli.command()
@click.option('-p', '--preset', default='default',
              type=click.Choice(['default', 'small', 'large', 'custom']),
              help='Preset configuration')
@click.option('-n', '--name', default='run_geosim',
              help='Name for the generated script')
def create_preset(preset, name):
    """
    Create preset run scripts for common scenarios
    """
    scripts_dir = Path('scripts')
    scripts_dir.mkdir(exist_ok=True)
    
    presets = {
        'default': {
            'description': 'Default pipeline with all features',
            'command': 'enrich',
            'options': '-b data/clean/buildings.geojson -r data/clean/roads.geojson -w data/clean/water.geojson -o data/features'
        }
    }
    
    if preset in presets:
        preset_info = presets[preset]

        batch_file = scripts_dir / f'{name}.bat'
        with open(batch_file, 'w') as f:
            f.write(f"""@echo off
echo Running GeoSim {preset} preset...
echo {preset_info['description']}
echo.
python "{Path(__file__).absolute()}" {preset_info['command']} {preset_info['options']}
if %errorlevel% neq 0 (
    echo.
    echo ❌ Pipeline failed!
    pause
    exit /b %errorlevel%
)
echo.
echo ✅ completed successfully!
pause
""")
        

        shell_file = scripts_dir / f'{name}.sh'
        with open(shell_file, 'w') as f:
            f.write(f"""#!/bin/bash
echo "Running GeoSim {preset} preset..."
echo "{preset_info['description']}"
echo ""
python3 "{Path(__file__).absolute()}" {preset_info['command']} {preset_info['options']}
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Pipeline failed!"
    exit 1
fi
echo ""
echo "✅completed successfully!"
""")
        
        os.chmod(shell_file, 0o755)
        
        click.echo(f"✅ Created preset scripts:")
        click.echo(f"  • {batch_file} (Windows)")
        click.echo(f"  • {shell_file} (Unix/Linux/Mac)")
        click.echo(f"\nTo run: {batch_file}  OR  ./{shell_file}")
    
    elif preset == 'custom':
        click.echo("Create your custom preset:")
        click.echo("1. Edit the 'presets' dictionary in the code")
        click.echo("2. Add your custom configuration")
        click.echo("3. Run: python geosim_features.py create-preset --preset custom")


@cli.command()
def install():
    """
    Set up the GeoSim CLI environment
    """
    click.echo("Setting up GeoSim CLI environment...")
    
    # Create batch file in current directory
    batch_file = 'geosim_features.bat'
    script_path = Path(__file__).absolute()
    
    with open(batch_file, 'w') as f:
        f.write(f"""@echo off
REM GeoSim CLI Wrapper
python "{script_path}" %*
""")
    
    os.chmod(batch_file, 0o755)
    
    # Create alias script for Unix/Linux
    shell_file = 'geosim'
    with open(shell_file, 'w') as f:
        f.write(f"""#!/bin/bash
python3 "{script_path}" "$@"
""")
    
    os.chmod(shell_file, 0o755)
    
    click.echo("✅ Installation complete!")
    click.echo("\nYou can now use:")
    click.echo(f"  • {batch_file} [command] [options]  (Windows)")
    click.echo(f"  • ./{shell_file} [command] [options]  (Unix/Linux/Mac)")
    click.echo("\nOr add the directory to your PATH for global access.")


def main():
    """Legacy main function for backward compatibility"""
    print("="*70)
    print("GeoSim Feature Enrichment & Validation Pipeline")
    print("="*70)
    
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent
    

    BUILDINGS_PATH = str(project_root / "data" / "clean" / "buildings.geojson")
    ROADS_PATH = str(project_root / "data" / "clean" / "roads.geojson")
    WATER_PATH = str(project_root / "data" / "clean" / "water.geojson")
    DEM_PATH = None  # Optional: str(project_root / "data" / "terrain" / "dem.tif")
    OUTPUT_DIR = str(project_root / "data" / "features")
    
    print(f"\n📁 Project root: {project_root}")
    print(f"📂 Looking for data in: {project_root / 'data' / 'clean'}")
    
    # Initialize pipeline
    pipeline = GeoSimPipeline(dem_path=DEM_PATH)
    
    try:
        # Run complete pipeline (enrichment + validation)
        results = pipeline.run_complete_pipeline(
            buildings_path=BUILDINGS_PATH,
            roads_path=ROADS_PATH,
            water_path=WATER_PATH,
            output_dir=OUTPUT_DIR,
            validate=True,
            min_confidence=0.6,
            min_ai_confidence=0.8
        )
        print("\n✅ All operations completed successfully!")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        print("\nPlease ensure your data files exist at:")
        print(f"  • {BUILDINGS_PATH}")
        print(f"  • {ROADS_PATH}")
        print(f"  • {WATER_PATH}")
        print("\nCurrent directory structure:")
        print(f"  Script location: {Path(__file__).absolute()}")
        print(f"  Project root: {project_root}")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    # Check if arguments were passed (CLI mode)
    if len(sys.argv) > 1:
        cli()
    else:
        # No arguments, run legacy main
        sys.exit(main())
