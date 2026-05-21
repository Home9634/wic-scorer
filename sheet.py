from collections import defaultdict
import re

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from uvicorn import config
from config import PLAYERS_TAB, PLAYERS_NAME_COLUMN, PLAYERS_USERNAME_COLUMN, GAME_CONFIG, TEAMS_COLUMN

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_service():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return build("sheets", "v4", credentials=creds).spreadsheets()

def load_player_map(sheet_id: str) -> dict[str, str]:
    """
    Reads the Players tab columns A (display names) and D (usernames) and builds a mapping of
    raw lowercase username -> sheet display name e.g. "home9634" -> "Home9634 (O)"
    """
    service = get_service()
    
    # Read both columns A and D
    result = service.values().get(
        spreadsheetId=sheet_id,
        range=f"{PLAYERS_TAB}!A:D",
        valueRenderOption="FORMATTED_VALUE"
    ).execute()

    player_map = {}
    for row in result.get("values", []):
        # Column A is index 0 (display name), Column D is index 3 (username)
        display_name = row[0].strip() if len(row) > 0 else None
        username = row[3].strip() if len(row) > 3 else None
        
        if username:
            # Use the username from column D
            player_map[username.lower()] = display_name or username

    return player_map


def add_missing_skb_winners(placements: list[dict], sheet_id: str) -> list[dict]:
    """
    For Sky Battle, the payload may omit players who survived to the end.
    Any player present in the Players tab but missing from placements is treated
    as tied for first place.
    """
    player_map = load_player_map(sheet_id)
    all_players = set(player_map.keys())
    reported_players = {
        p["raw_username"].strip().lower()
        for p in placements
        if p.get("raw_username")
    }

    missing_players = sorted(all_players - reported_players)
    if not missing_players:
        return placements

    augmented = list(placements)
    for raw_username in missing_players:
        augmented.append({"raw_username": raw_username, "place": 1})

    return augmented

def load_teams(sheet_id: str) -> dict[str, str]:
    """
    Reads Players tab column C and builds a map of
    team_letter -> team_name e.g. "R" -> "Crimson Cardinals (R)"
    """
    service = get_service()
    result = service.values().get(
        spreadsheetId=sheet_id,
        range=f"{PLAYERS_TAB}!{TEAMS_COLUMN}:{TEAMS_COLUMN}",
        valueRenderOption="FORMATTED_VALUE"
    ).execute()

    teams = {}
    for row in result.get("values", []):
        if not row:
            continue
        name = row[0].strip()
        # Extract letter from e.g. "Crimson Cardinals (R)" -> "R"
        match = re.search(r'\((\w+)\)$', name)
        if match:
            teams[match.group(1)] = name
    return teams


def calculate_team_bonuses(round: int, placements: list[dict], sheet_id: str):
    """
    Determines top 4 team finishes for a TGTTOS round and writes them to the sheet.
    placements is sorted by place ascending, each entry has raw_username and place.
    DNFs are excluded since they won't be in the placements list.
    """
    config = GAME_CONFIG.get("TGTTOS")
    if not config or "team_bonus_start_cell" not in config:
        return

    requirement = config["team_finish_requirement"]
    tab = config["tab"]
    bonus_col = config["team_bonus_start_cell"]  # e.g. "I1"
    bonus_start_row = int(config["placement_start_row"])          # e.g. 1

    # Offset column for this round — round 1 = I, round 2 = J, etc.
    round_col = chr(ord(bonus_col) + round - 1)

    player_map = load_player_map(sheet_id)
    teams = load_teams(sheet_id)

    # Build reverse map: display_name -> team_letter
    # e.g. "Home9634 (O)" -> "O"
    def get_team_letter(raw_username: str) -> str | None:
        display = player_map.get(raw_username.lower())
        if not display:
            return None
        match = re.search(r'\((\w+)\)$', display)
        return match.group(1) if match else None

    # Walk placements in order — track how many from each team have finished
    team_finish_counts: dict[str, int] = defaultdict(int)
    team_finish_order: list[str] = []  # teams in the order they hit the threshold

    for p in sorted(placements, key=lambda x: x["place"]):
        letter = get_team_letter(p["raw_username"])
        if not letter:
            continue

        team_finish_counts[letter] += 1

        if team_finish_counts[letter] == requirement:
            # This team just hit the threshold
            if letter not in team_finish_order:
                team_finish_order.append(letter)

        if len(team_finish_order) == 4:
            break  # Only need top 4

    # Write top 4 team names to sheet
    service = get_service()
    values = []
    for letter in team_finish_order[:4]:
        team_display = teams.get(letter, f"? ({letter})")
        values.append([team_display])

    if not values:
        return

    range_name = f"{tab}!{round_col}{bonus_start_row}:{round_col}{bonus_start_row + len(values) - 1}"
    service.values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": values}
    ).execute()

def write_placements(game: str, round: int, placements: list[dict], sheet_id: str):
    """
    Writes a list of {raw_username, place} to the correct column in the sheet.
    Placements are sorted by place, written top to bottom.
    """
    config = GAME_CONFIG.get(game)
    if not config:
        raise ValueError(f"Unknown game: {game}")

    col = config["placement_columns"].get(round)
    if not col:
        raise ValueError(f"No column configured for {game} round {round}")

    start_row = config["placement_start_row"]
    tab = config["tab"]
    player_map = load_player_map(sheet_id)

    # if game == "Sky Battle":
    #     placements = add_missing_skb_winners(placements, sheet_id)

    # Sort by place ascending
    sorted_placements = sorted(placements, key=lambda p: p["place"])

    # Build column values — one display name per row
    values = []
    for p in sorted_placements:
        display_name = player_map.get(p["raw_username"].lower())
        if display_name:
            values.append([display_name])
        else:
            # Fall back to raw name if not found in sheet — visible as a warning
            values.append([f"? {p['raw_username']}"])

    range_name = f"{tab}!{col}{start_row}:{col}{start_row + len(values) - 1}"
    service = get_service()
    service.values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": values}
    ).execute()
    
    if game == "TGTTOS":
        calculate_team_bonuses(round, placements, sheet_id)
    
    # Handle tied winners for SKB/HITW — copy first-place score down to tied winners
    winners = [p for p in sorted_placements if p["place"] == 1]
    if game in {"Sky Battle", "Hole in the Wall"} and len(winners) > 1:
        score_col = chr(ord(col) + 1)  # column to the right of placement col
        first_score_cell = f"{score_col}{start_row}"

        # Write =B1 style formula into each subsequent winner's score cell
        for i in range(1, len(winners)):
            tied_score_cell = f"{tab}!{score_col}{start_row + i}"
            service.values().update(
                spreadsheetId=sheet_id,
                range=tied_score_cell,
                valueInputOption="USER_ENTERED",  # needed for formulas
                body={"values": [[f"={tab}!{first_score_cell}"]]}
            ).execute()

def write_kills(game: str, round: int, kills: list[dict], sheet_id: str):
    config = GAME_CONFIG.get(game)
    if not config or "kills_name_column" not in config:
        return

    player_map = load_player_map(sheet_id)
    tab = config["tab"]
    kills_name_column = config["kills_name_column"]
    offset = config["kills_round_offset"]  # e.g. 2 means I for round 1, J for round 2...
    service = get_service()

    # Calculate the kills column for this round dynamically
    # kills_name_column is e.g. "G" (ASCII 71), offset 2 = "I", round adds on top
    base_col_index = ord(kills_name_column) + offset  # e.g. ord("G") + 2 = 73 = "I"
    kills_col = chr(base_col_index + round - 1)       # round 1 = I, round 2 = J, round 3 = K

    # Read name column to find row positions
    name_range = f"{tab}!{kills_name_column}:{kills_name_column}"
    result = service.values().get(
        spreadsheetId=sheet_id,
        range=name_range,
        valueRenderOption="FORMATTED_VALUE"
    ).execute()

    name_to_row = {}
    for i, row in enumerate(result.get("values", []), start=1):
        if row:
            name_to_row[row[0].strip()] = i

    for k in kills:
        display_name = player_map.get(k["raw_username"].lower())
        if not display_name:
            print(f"[WicMiddleware] No sheet name found for {k['raw_username']}")
            continue

        row = name_to_row.get(display_name)
        if not row:
            print(f"[WicMiddleware] {display_name} not found in kills name column")
            continue

        cell = f"{tab}!{kills_col}{row}"
        service.values().update(
            spreadsheetId=sheet_id,
            range=cell,
            valueInputOption="RAW",
            body={"values": [[k["kills"]]]}
        ).execute()