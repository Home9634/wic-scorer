from fastapi import FastAPI, HTTPException
from models import GameUpdateRequest
from sheet import write_placements, write_kills
import re
def extract_sheet_id(url: str) -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError(f"Invalid sheet URL: {url}")
    return match.group(1)

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/update")
def update_game(req: GameUpdateRequest):
    try:
        print(req)
        sheet_id = extract_sheet_id(req.sheetUrl)
        
        placements = [{"raw_username": p.raw_username, "place": p.place}
                      for p in req.placements]
        write_placements(req.game, req.round, placements, sheet_id)

        if req.kills:
            kills = [{"raw_username": k.raw_username, "kills": k.kills}
                     for k in req.kills]
            write_kills(req.game, req.round, kills, sheet_id)
    
        return {"status": "ok", "game": req.game, "round": req.round}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))