import os
import json

from fastapi import HTTPException
from models import UnicodeConfig  # Import the new model

UNICODES_FILE = os.path.join(os.path.dirname(__file__), "unicodes.json")

def load_unicodes():
    # Fallback to defaults if the file is accidentally deleted
    if not os.path.exists(UNICODES_FILE):
        default = {
            "global": {"levelIcon": "\uE002"},
            "games": {
                "Sky Battle": {"eventChar": "\uE151", "deathChar": "\uE2E7"},
                "Hole in the Wall": {"eventChar": "\uE146", "deathChar": "\uE2E7"},
                "TGTTOS": {"eventChar": "\uE156", "placementChar": "\uE000"},
                "Rocket Spleef Rush": {"eventChar": "\uE14F", "deathChar": "\uE2E7"}
            }
        }
        with open(UNICODES_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
        return default
        
    with open(UNICODES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
      
def update_unicodes(config: UnicodeConfig):
     try:
        with open(UNICODES_FILE, "w", encoding="utf-8") as f:
            # Use dict() to extract parameters and ensure_ascii=False to preserve readable unicode formatting inside the JSON file
            json.dump(config.dict(), f, indent=4, ensure_ascii=False)
        return {"status": "ok"}
     except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))