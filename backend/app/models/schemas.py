"""
Pydantic v2 request / response schemas for the AWG Climate Suitability Analyzer.

All monetary or scientific values carry SI or commonly used meteorological
units noted in the field descriptions.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class LocationRequest(BaseModel):
    """Body for endpoints that require a geographic location."""

    city: str = Field(..., description="City name to look up", examples=["Singapore"])
    country: Optional[str] = Field(
        None,
        description="Optional country name or ISO code to disambiguate the city",
        examples=["Singapore"],
    )


class WeatherInputRequest(BaseModel):
    """
    Direct weather observations used by the /api/predict endpoint.

    Allows callers to supply their own sensor readings without triggering a
    live API fetch.
    """

    temperature: float = Field(..., description="Dry-bulb temperature in °C")
    humidity: float = Field(..., description="Relative humidity in %")
    pressure: float = Field(1013.25, description="Atmospheric pressure in hPa")
    wind_speed: float = Field(0.0, description="Wind speed in km/h")
    altitude: float = Field(0.0, description="Site altitude in metres above sea level")


# ---------------------------------------------------------------------------
# Core data schemas
# ---------------------------------------------------------------------------


class WeatherData(BaseModel):
    """Current or snapshot meteorological conditions for a location."""

    temperature: float = Field(..., description="Dry-bulb temperature (°C)")
    humidity: float = Field(..., description="Relative humidity (%)")
    pressure: float = Field(..., description="Mean sea-level pressure (hPa)")
    wind_speed: float = Field(..., description="Wind speed at 10 m (km/h)")
    dew_point: float = Field(..., description="Dew-point temperature (°C)")
    absolute_humidity: float = Field(..., description="Absolute humidity (g/m³)")
    altitude: float = Field(0.0, description="Site elevation (m ASL)")


class PsychrometricProperties(BaseModel):
    """Thermodynamic properties of the moist air parcel at the location."""

    absolute_humidity: float = Field(..., description="Absolute humidity (g/m³)")
    dew_point: float = Field(..., description="Dew-point temperature (°C)")
    wet_bulb_temp: float = Field(..., description="Wet-bulb temperature (°C)")
    specific_humidity: float = Field(
        ..., description="Specific humidity (g water vapour / kg moist air)"
    )
    air_density: float = Field(..., description="Moist air density (kg/m³)")


class AWGPrediction(BaseModel):
    """Machine-learning prediction result for AWG water yield."""

    water_output_liters_per_day: float = Field(
        ..., description="Predicted water output (L/day)"
    )
    suitability_score: float = Field(
        ..., description="Overall suitability score 0–100"
    )
    system_recommendation: str = Field(
        ..., description="Recommended AWG system class (Small / Medium / Large)"
    )
    confidence: float = Field(
        ..., description="Model confidence 0–1 (1 = highest confidence)"
    )


class ForecastDay(BaseModel):
    """Single day in a multi-day forecast."""

    date: str = Field(..., description="ISO-8601 date string (YYYY-MM-DD)")
    temperature: float = Field(..., description="Mean temperature for the day (°C)")
    humidity: float = Field(..., description="Mean relative humidity for the day (%)")
    pressure: float = Field(..., description="Mean pressure for the day (hPa)")
    predicted_output: float = Field(
        ..., description="Predicted water output for the day (L/day)"
    )
    suitability_score: float = Field(
        ..., description="Suitability score for the day (0–100)"
    )


# ---------------------------------------------------------------------------
# Composite response schemas
# ---------------------------------------------------------------------------


class AnalysisResponse(BaseModel):
    """
    Full AWG suitability analysis result returned by POST /api/analyze.

    Aggregates geocoding, current weather, psychrometric calculations, ML
    prediction, and a 7-day forecast into a single response object.
    """

    model_config = {"protected_namespaces": ()}

    location: str = Field(..., description="Resolved location name")
    coordinates: dict = Field(
        ..., description='{"latitude": float, "longitude": float}'
    )
    current_weather: WeatherData
    psychrometric_props: PsychrometricProperties
    awg_prediction: AWGPrediction
    forecast: List[ForecastDay] = Field(
        default_factory=list, description="7-day daily forecast"
    )
    model_trained: bool = Field(
        ..., description="Whether the ML model was trained before this prediction"
    )


class WeatherResponse(BaseModel):
    """Lightweight current-weather response (GET /api/weather/{city})."""

    location: str
    coordinates: dict
    weather: WeatherData
    psychrometric_props: PsychrometricProperties


class SuitabilityResponse(BaseModel):
    """Suitability-only response (GET /api/suitability/{city})."""

    location: str
    suitability_score: float
    weather_summary: dict


class ForecastResponse(BaseModel):
    """7-day forecast response (GET /api/forecast/{city})."""

    location: str
    coordinates: dict
    forecast: List[ForecastDay]


class TrainResponse(BaseModel):
    """Response returned after a successful model training run."""

    model_config = {"protected_namespaces": ()}

    message: str
    metrics: dict
    model_trained: bool


class PredictResponse(BaseModel):
    """Response for POST /api/predict (direct weather input)."""

    awg_prediction: AWGPrediction
    psychrometric_props: PsychrometricProperties
