# Tab name for the player reference list
PLAYERS_TAB = "Players"

# Column in the Players tab where display names live e.g. "Ruby (R)"
PLAYERS_NAME_COLUMN = "A"
TEAMS_COLUMN = "C"

# Per-game config: tab name, and which column each round's placements go in
# Kills section start cell is also defined per game where applicable
GAME_CONFIG = {
    "Sky Battle": {
        "tab": "SKB",
        "placement_columns": {
            1: "A",
            2: "C",
            3: "E",
        },
        "placement_start_row": 1,
        "kills_name_column": "G",
        "kills_start_cell": "H", 
        "kills_round_offset": 2, 
    },
    "Hole in the Wall": {
        "tab": "HITW",
        "placement_columns": {
            1: "A",
            2: "C",
            3: "E",
        },
        "placement_start_row": 1,
    },
    "TGTTOS": {
        "tab": "TGTTOS",
        "placement_columns": {
            1: "A",
            2: "B",
            3: "C",
            4: "D",
            5: "E",
            6: "F",
        },
        "placement_start_row": 1,
        "team_bonus_start_cell": "I",
        "team_finish_requirement": 1,
    },
    "Rocket Spleef Rush": {
        "tab": "RSR",
        "placement_columns": {
            1: "A",
            2: "C",
            3: "E",
        },
        "placement_start_row": 1,
        "kills_name_column": "G",
        "kills_start_cell": "H1",
        "kills_round_offset": 2,
    },
}