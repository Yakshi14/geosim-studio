from buildings import enrich_buildings
from roads import enrich_roads

def run_feature_enrichment():
    print("\n=== MODULE 5: FEATURE ENRICHMENT ===")

    enrich_buildings()
    enrich_roads()

    print("✅ Module 5 completed.")

if __name__ == "__main__":
    run_feature_enrichment()
