from pydantic import BaseModel
from typing import Optional

class PlayerPlacement(BaseModel):
    raw_username: str
    place: int

class PlayerKill(BaseModel):
    raw_username: str
    kills: int

class GameUpdateRequest(BaseModel):
    game: str          # "Sky Battle", "Hole in the Wall", "TGTTOS"
    round: int         # 1, 2, 3...
    placements: list[PlayerPlacement]
    kills: Optional[list[PlayerKill]] = None  # SKB only
    sheetUrl: str      # Full URL of the Google Sheet to update
    
class UnicodeConfig(BaseModel):
    global_config: dict[str, str]
    games: dict[str, dict[str, str]]