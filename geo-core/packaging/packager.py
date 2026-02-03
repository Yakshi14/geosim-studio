import os
import json
from datetime import datetime

def run_packaging():
    base_path=os.getcwd()
    output_path=os.path.join(base_path, "data/phase1_output")
    os.makedirs(output_path, exist_ok=True)

    metadata = {
        "project":"Simulation-Safe Geospatial Foundation",
        "phase":"Phase 1: Integration",
        "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(os.path.join(output_path,"metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    print("\n complete")

if __name__ == "__main__":
    run_packaging()