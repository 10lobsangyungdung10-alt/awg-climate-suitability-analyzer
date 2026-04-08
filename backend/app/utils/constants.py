"""
Shared constants for the AWG Climate Suitability Analyzer.

Centralizes all magic numbers and configuration values so that they can be
referenced consistently across services and models.
"""

# ---------------------------------------------------------------------------
# Open-Meteo API base URLs
# ---------------------------------------------------------------------------

#: Base URL for forecast / current-weather queries.
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

#: Base URL for historical archive queries.
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

#: Base URL for the geocoding look-up service.
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

# ---------------------------------------------------------------------------
# AWG system specifications
# Each entry describes a commercially available AWG unit class.
# ---------------------------------------------------------------------------

AWG_SYSTEMS: dict[str, dict] = {
    "Small": {
        "capacity_liters_per_day": 10,
        "description": "Suitable for individuals or small households (1-3 people)",
        "min_humidity": 50,          # % RH — lower bound for effective operation
        "power_consumption_kw": 0.3,
        "ideal_temp_range": (20, 35),
    },
    "Medium": {
        "capacity_liters_per_day": 25,
        "description": "Suitable for medium households or small offices (4-10 people)",
        "min_humidity": 55,
        "power_consumption_kw": 0.7,
        "ideal_temp_range": (22, 38),
    },
    "Large": {
        "capacity_liters_per_day": 50,
        "description": "Suitable for large households, offices, or community use (10+ people)",
        "min_humidity": 60,
        "power_consumption_kw": 1.5,
        "ideal_temp_range": (25, 40),
    },
}

# ---------------------------------------------------------------------------
# Temperature operating range (°C)
# ---------------------------------------------------------------------------

#: Below this temperature AWG output degrades significantly.
TEMP_MIN_OPTIMAL: float = 20.0

#: Above this temperature cooling efficiency drops.
TEMP_MAX_OPTIMAL: float = 35.0

#: Hard lower limit — condensation becomes negligible below this point.
TEMP_ABSOLUTE_MIN: float = 5.0

#: Hard upper limit — equipment thermal stress above this point.
TEMP_ABSOLUTE_MAX: float = 50.0

# ---------------------------------------------------------------------------
# Humidity thresholds (% RH)
# ---------------------------------------------------------------------------

HUMIDITY_EXCELLENT: float = 70.0   # ≥70 % is considered excellent for AWG
HUMIDITY_GOOD: float = 55.0        # ≥55 % is considered good
HUMIDITY_FAIR: float = 40.0        # ≥40 % is considered fair
HUMIDITY_POOR: float = 30.0        # <30 % is considered poor / not viable

# ---------------------------------------------------------------------------
# Pressure reference (hPa)
# ---------------------------------------------------------------------------

STANDARD_PRESSURE_HPA: float = 1013.25  # Standard atmosphere in hPa

# ---------------------------------------------------------------------------
# Dew point thresholds (°C) for suitability scoring
# ---------------------------------------------------------------------------

DEW_POINT_EXCELLENT: float = 20.0
DEW_POINT_GOOD: float = 15.0
DEW_POINT_FAIR: float = 10.0

# ---------------------------------------------------------------------------
# ML model feature columns
# Must be kept in sync with AWGMLModel.FEATURE_COLUMNS.
# ---------------------------------------------------------------------------

FEATURE_COLUMNS: list[str] = [
    "temperature",           # °C
    "humidity",              # % RH
    "pressure",              # hPa
    "wind_speed",            # km/h
    "dew_point",             # °C
    "absolute_humidity",     # g/m³
    "month",                 # 1-12
    "hour",                  # 0-23
    "temp_rh_interaction",   # temperature × humidity (engineered feature)
    "pressure_adjusted",     # pressure normalised to sea level equivalent
]

# ---------------------------------------------------------------------------
# Suitability score weights
# Weights must sum to 1.0
# ---------------------------------------------------------------------------

SUITABILITY_WEIGHTS: dict[str, float] = {
    "humidity": 0.40,
    "temperature": 0.30,
    "pressure": 0.15,
    "dew_point": 0.15,
}
