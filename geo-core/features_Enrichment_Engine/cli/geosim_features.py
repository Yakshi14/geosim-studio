"""
CLI tool for feature enrichment and validation
Part of the geosim Phase 1 pipeline
"""

import click
import geopandas as gpd
from pathlib import Path
import sys
import json

# Import our modules
sys.path.append(str(Path(__file__).parent.parent))
from features.enrichment_engine import FeatureEnricher
from validation.validation_engine import ValidationEngine
from schemas.feature_schemas import export_schemas_to_json


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    GeoSim Feature Enrichment & Validation CLI
    
    Phase 1: Convert GIS features into simulation primitives
    """
    pass


@cli.command()
@click.option('--buildings', '-b', required=True, type=click.Path(exists=True),
              help='Path to clean buildings GeoJSON')
@click.option('--roads', '-r', required=True, type=click.Path(exists=True),
              help='Path to clean roads GeoJSON')
@click.option('--dem', '-d', type=click.Path(exists=True),
              help='Path to DEM file for height estimation (optional)')
@click.option('--output', '-o', required=True, type=click.Path(),
              help='Output directory for enriched features')
def enrich(buildings, roads, dem, output):
    """
    Enrich building and road features with simulation attributes
    
    Example:
        geosim-features enrich -b buildings.geojson -r roads.geojson -o data/features/
    """
    click.echo("🔧 Starting feature enrichment...")
    
    try:
        # Initialize enricher
        enricher = FeatureEnricher(dem_path=dem)
        
        # Load data
        click.echo(f"  ├─ Loading buildings from {buildings}")
        buildings_gdf = gpd.read_file(buildings)
        click.echo(f"     └─ Loaded {len(buildings_gdf)} buildings")
        
        click.echo(f"  ├─ Loading roads from {roads}")
        roads_gdf = gpd.read_file(roads)
        click.echo(f"     └─ Loaded {len(roads_gdf)} roads")
        
        # Enrich buildings
        click.echo("  ├─ Enriching buildings...")
        buildings_enriched = enricher.enrich_buildings(buildings_gdf)
        click.echo(f"     └─ Added: height_m, usage_type, lod_class, confidence")
        
        # Enrich roads
        click.echo("  ├─ Enriching roads...")
        roads_enriched = enricher.enrich_roads(roads_gdf)
        click.echo(f"     └─ Added: width_m, road_type, nav_weight, speed_limit_kmh")
        
        # Save
        click.echo(f"  ├─ Saving to {output}")
        enricher.save_enriched_data(buildings_enriched, roads_enriched, output)
        
        click.echo("✅ Feature enrichment complete!")
        
        # Print statistics
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
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--data-dir', '-d', required=True, type=click.Path(exists=True),
              help='Root data directory to validate')
@click.option('--output', '-o', type=click.Path(),
              help='Output path for validation report (default: data/validated/validation_report.json)')
@click.option('--min-confidence', type=float, default=0.6,
              help='Minimum confidence threshold (default: 0.6)')
@click.option('--min-ai-confidence', type=float, default=0.8,
              help='Minimum AI confidence threshold (default: 0.8)')
def validate(data_dir, output, min_confidence, min_ai_confidence):
    """
    Validate Phase 1 outputs for export safety
    
    Example:
        geosim-features validate -d data/ -o data/validated/report.json
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
        output_path = output or Path(data_dir) / 'validated/validation_report.json'
        validator.save_report(output_path)
        
        # Print summary
        validator.print_summary()
        
        # Exit with error code if validation failed
        if not results['passed']:
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--buildings', '-b', required=True, type=click.Path(exists=True),
              help='Path to enriched buildings GeoJSON')
@click.option('--roads', '-r', required=True, type=click.Path(exists=True),
              help='Path to enriched roads GeoJSON')
def stats(buildings, roads):
    """
    Display detailed statistics for enriched features
    
    Example:
        geosim-features stats -b data/features/buildings_enriched.geojson -r data/features/roads_enriched.geojson
    """
    click.echo("📊 Feature Statistics\n")
    
    try:
        # Buildings
        click.echo("🏢 BUILDINGS")
        click.echo("="*60)
        buildings_gdf = gpd.read_file(buildings)
        
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
        roads_gdf = gpd.read_file(roads)
        
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
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(),
              default='schemas/feature_schemas.json',
              help='Output path for schema JSON')
def export_schemas(output):
    """
    Export schema definitions to JSON
    
    Example:
        geosim-features export-schemas -o schemas/schemas.json
    """
    try:
        export_schemas_to_json(output)
        click.echo(f"✅ Schemas exported to {output}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--buildings', '-b', required=True, type=click.Path(exists=True),
              help='Path to clean buildings GeoJSON')
@click.option('--roads', '-r', required=True, type=click.Path(exists=True),
              help='Path to clean roads GeoJSON')
@click.option('--dem', '-d', type=click.Path(exists=True),
              help='Path to DEM file (optional)')
@click.option('--output', '-o', required=True, type=click.Path(),
              help='Output directory')
@click.option('--validate/--no-validate', default=True,
              help='Run validation after enrichment')
def pipeline(buildings, roads, dem, output, validate):
    """
    Run complete enrichment and validation pipeline
    
    Example:
        geosim-features pipeline -b buildings.geojson -r roads.geojson -o data/features/
    """
    click.echo("🚀 Starting complete feature pipeline...\n")
    
    # Step 1: Enrichment
    click.echo("STEP 1: Feature Enrichment")
    click.echo("-"*60)
    ctx = click.get_current_context()
    ctx.invoke(enrich, buildings=buildings, roads=roads, dem=dem, output=output)
    
    # Step 2: Validation (if enabled)
    if validate:
        click.echo("\n\nSTEP 2: Validation")
        click.echo("-"*60)
        
        # Determine data directory (parent of output)
        data_dir = Path(output).parent
        
        ctx.invoke(validate, data_dir=str(data_dir), output=None, 
                  min_confidence=0.6, min_ai_confidence=0.8)
    
    click.echo("\n\n✅ Pipeline complete!")


if __name__ == '__main__':
    cli()