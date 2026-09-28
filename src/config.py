"""Project configuration: paths, reference mappings and thresholds.

Reference data below is taken directly from the project brief
("Factories Co-ordinates" and "Products and Factories Correlation" tables).
"""
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_CSV = DATA_DIR / "Nassau_Candy_Distributor.csv"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_CSV = PROCESSED_DIR / "nassau_candy_clean.csv"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# --------------------------------------------------------------------------- #
# Factory reference data (from the project brief)
# --------------------------------------------------------------------------- #
FACTORIES = {
    "Lot's O' Nuts":    {"latitude": 32.881893, "longitude": -111.768036},
    "Wicked Choccy's":  {"latitude": 32.076176, "longitude": -81.088371},
    "Sugar Shack":      {"latitude": 48.119140, "longitude": -96.181150},
    "Secret Factory":   {"latitude": 41.446333, "longitude": -90.565487},
    "The Other Factory": {"latitude": 35.117500, "longitude": -89.971107},
}

# Product -> Factory correlation table (from the project brief).
# NOTE: "Wonka Bar -Scrumdiddlyumptious" appears with a missing space in the
# raw file; labels are standardised during cleaning BEFORE this map is applied.
PRODUCT_FACTORY = {
    # Chocolate
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows":         "Lot's O' Nuts",
    "Wonka Bar - Scrumdiddlyumptious":   "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate":        "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    # Sugar
    "Laffy Taffy":                       "Sugar Shack",
    "SweeTARTS":                         "Sugar Shack",
    "Nerds":                             "Sugar Shack",
    "Fun Dip":                           "Sugar Shack",
    "Fizzy Lifting Drinks":              "Sugar Shack",  # per brief (Division=Other in brief, Sugar in data)
    "Everlasting Gobstopper":            "Secret Factory",
    "Hair Toffee":                       "The Other Factory",
    # Other
    "Lickable Wallpaper":                "Secret Factory",
    "Wonka Gum":                         "Secret Factory",
    "Kazookles":                         "The Other Factory",
}

# Known label corrections applied during standardisation.
PRODUCT_LABEL_FIXES = {
    "Wonka Bar -Scrumdiddlyumptious": "Wonka Bar - Scrumdiddlyumptious",
}

# --------------------------------------------------------------------------- #
# Analytical thresholds
# --------------------------------------------------------------------------- #
# Tolerance for the accounting identity Sales - Cost = Gross Profit (USD).
IDENTITY_TOL = 0.02

# Margin-risk flag bands (used as defaults; the dashboard slider overrides the
# "at_risk" boundary interactively).
MARGIN_BANDS = {
    "healthy_low": 60.0,   # >= 60%  -> Healthy
    "acceptable_low": 40.0  # >= 40%  -> Acceptable; below at_risk threshold -> Critical
}
AT_RISK_MARGIN = 25.0      # default margin-risk threshold (%) for the slider

# Diagnostic action rules (evaluated in order, first match wins)
DISCONTINUATION_MARGIN = 20.0   # margin% below this AND low profit -> discontinuation review
REPRICE_COST_RATIO = 45.0       # cost/sales % above this -> pricing/cost action
PARETO_TARGET = 0.80            # cumulative-share target for Pareto analysis
