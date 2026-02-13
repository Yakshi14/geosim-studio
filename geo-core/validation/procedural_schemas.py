from pydantic import BaseModel,Field
from typing import List,Optional


class RoadSegment(BaseModel):
    road_id:str
    nodes:List[int]
    speed_limit:int=Field(gt=0,le=120)
    surface_type:Optional[str]="asphalt"


def run_validation_check():
    print("module 24:initializing procedural validation...")

    test_data = {
        "road_id":"R-101",
        "nodes":[1001,1002,1003],
        "speed_limit":60,
        "surface_type":"gravel"
    }

    try:
        validated_road=RoadSegment(**test_data)
        print(f"✅ Validation Successful:Road{validated_road.road_id} is compliant.")
        return True
    except Exception as e:
        print(f"validation failed:{e}")
        return False


if __name__ == "__main__":
    run_validation_check()
