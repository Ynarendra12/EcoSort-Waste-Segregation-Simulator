"""Global constants for EcoSort."""

WIDTH, HEIGHT = 960, 600
FPS = 60
TITLE = "EcoSort - Interactive Waste Segregation Simulator"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
INK = (35, 35, 50)

POINTS_CORRECT = 10
PENALTY_WRONG = 5

# The three dustbins used in every level
BIN_INFO = {
    "wet": {
        "label": "WET",
        "desc": "Food waste, peels",
        "color": (46, 160, 67),
        "dark": (30, 112, 46),
    },
    "dry": {
        "label": "DRY",
        "desc": "Paper, wrappers",
        "color": (52, 120, 220),
        "dark": (34, 82, 160),
    },
    "recycle": {
        "label": "RECYCLE",
        "desc": "Bottles, cartons",
        "color": (225, 62, 62),
        "dark": (158, 40, 40),
    },
}
BIN_ORDER = ["wet", "dry", "recycle"]
