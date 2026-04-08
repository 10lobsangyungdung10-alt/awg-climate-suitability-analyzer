"""
API route definitions for the AWG Climate Suitability Analyzer.

All routes are registered on the ``router`` APIRouter and included in the
main FastAPI application via ``app.include_router(router)``.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, status

from app.models.ml_model import awg_model
from app.models.schemas import (
    AnalysisResponse,
    AWGPrediction,
    ForecastResponse,
    LocationRequest,
    PredictResponse,
    SuitabilityResponse,
    TrainResponse,
    WeatherInputRequest,
    WeatherResponse,
)
from app.services import geocoding_service, weather_service
from app.services.awg_analyzer import awg_analyzer
from app.services.psychrometric_service import (
    calculate_absolute_humidity,
    calculate_dew_point,
    get_all_psychrometric_properties,
)
from app.models.schemas import WeatherData
from app.utils.constants import STANDARD_PRESSURE_HPA

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["AWG Analysis"])


# ---------------------------------------------------------------------------
# POST /api/analyze  — full analysis
# ---------------------------------------------------------------------------


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Full AWG suitability analysis",
    description=(
        "Run the complete AWG analysis pipeline for the given location: "
        "geocoding → current weather → psychrometrics → ML prediction → 7-day forecast."
    ),
)
async def analyze(request: LocationRequest) -> AnalysisResponse:
    """
    Perform a full AWG suitability analysis for a city.

    Parameters
    ----------
    request:
        ``{"city": "...", "country": "..."}``
    """
    return await awg_analyzer.analyze_location(request.city, request.country)


# ---------------------------------------------------------------------------
# GET /api/weather/{city}  — current weather
# ---------------------------------------------------------------------------


@router.get(
    "/weather/{city}",
    response_model=WeatherResponse,
    summary="Current weather for a city",
)
async def get_weather(
    city: str,
    country: Optional[str] = Query(None, description="Optional country hint"),
) -> WeatherResponse:
    """Return current weather observations and psychrometric properties for *city*."""
    location_info = await geocoding_service.get_coordinates(city, country)
    lat = location_info["latitude"]
    lon = location_info["longitude"]
    elevation = location_info.get("elevation", 0.0)
    location_name = f"{location_info['name']}, {location_info['country']}".strip(", ")

    raw = await weather_service.get_current_weather(lat, lon, elevation)

    temperature = raw["temperature"]
    humidity = raw["humidity"]
    pressure = raw["pressure"]
    wind_speed = raw["wind_speed"]

    weather = WeatherData(
        temperature=temperature,
        humidity=humidity,
        pressure=pressure,
        wind_speed=wind_speed,
        dew_point=calculate_dew_point(temperature, humidity),
        absolute_humidity=calculate_absolute_humidity(temperature, humidity),
        altitude=elevation,
    )
    psychro = get_all_psychrometric_properties(temperature, humidity, pressure)

    return WeatherResponse(
        location=location_name,
        coordinates={"latitude": lat, "longitude": lon},
        weather=weather,
        psychrometric_props=psychro,
    )


# ---------------------------------------------------------------------------
# POST /api/predict  — predict from supplied weather data
# ---------------------------------------------------------------------------


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Predict AWG water output from weather data",
)
async def predict(request: WeatherInputRequest) -> PredictResponse:
    """
    Predict water output and suitability directly from supplied weather readings.

    No geocoding or live API call is made — the caller provides the sensor
    values directly.
    """
    temperature = request.temperature
    humidity = request.humidity
    pressure = request.pressure
    wind_speed = request.wind_speed

    psychro = get_all_psychrometric_properties(temperature, humidity, pressure)
    weather = WeatherData(
        temperature=temperature,
        humidity=humidity,
        pressure=pressure,
        wind_speed=wind_speed,
        dew_point=psychro.dew_point,
        absolute_humidity=psychro.absolute_humidity,
        altitude=request.altitude,
    )

    features = {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
        "wind_speed": wind_speed,
        "dew_point": psychro.dew_point,
        "absolute_humidity": psychro.absolute_humidity,
        "month": float(date.today().month),
        "hour": 12.0,
        "temp_rh_interaction": temperature * humidity,
        "pressure_adjusted": pressure / STANDARD_PRESSURE_HPA,
    }

    water_output, confidence = awg_model.predict(features)
    suitability_score = awg_analyzer.calculate_suitability_score(weather, psychro)
    system_recommendation = awg_analyzer.recommend_system(water_output)

    return PredictResponse(
        awg_prediction=AWGPrediction(
            water_output_liters_per_day=water_output,
            suitability_score=suitability_score,
            system_recommendation=system_recommendation,
            confidence=confidence,
        ),
        psychrometric_props=psychro,
    )


# ---------------------------------------------------------------------------
# GET /api/suitability/{city}  — suitability score only
# ---------------------------------------------------------------------------


@router.get(
    "/suitability/{city}",
    response_model=SuitabilityResponse,
    summary="AWG suitability score for a city",
)
async def get_suitability(
    city: str,
    country: Optional[str] = Query(None, description="Optional country hint"),
) -> SuitabilityResponse:
    """Return the composite AWG suitability score for *city*."""
    location_info = await geocoding_service.get_coordinates(city, country)
    lat = location_info["latitude"]
    lon = location_info["longitude"]
    elevation = location_info.get("elevation", 0.0)
    location_name = f"{location_info['name']}, {location_info['country']}".strip(", ")

    raw = await weather_service.get_current_weather(lat, lon, elevation)

    temperature = raw["temperature"]
    humidity = raw["humidity"]
    pressure = raw["pressure"]
    wind_speed = raw["wind_speed"]

    weather = WeatherData(
        temperature=temperature,
        humidity=humidity,
        pressure=pressure,
        wind_speed=wind_speed,
        dew_point=calculate_dew_point(temperature, humidity),
        absolute_humidity=calculate_absolute_humidity(temperature, humidity),
        altitude=elevation,
    )
    psychro = get_all_psychrometric_properties(temperature, humidity, pressure)
    score = awg_analyzer.calculate_suitability_score(weather, psychro)

    return SuitabilityResponse(
        location=location_name,
        suitability_score=score,
        weather_summary={
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "dew_point": psychro.dew_point,
        },
    )


# ---------------------------------------------------------------------------
# POST /api/train-model  — train ML model with historical data
# ---------------------------------------------------------------------------


@router.post(
    "/train-model",
    response_model=TrainResponse,
    summary="Train the AWG ML model",
    description=(
        "Fetches ~1 year of historical weather data for the given location and "
        "trains the Gradient Boosting model.  Falls back to synthetic data if "
        "insufficient observations are available."
    ),
)
async def train_model(request: LocationRequest) -> TrainResponse:
    """Train (or re-train) the ML model for the specified location."""
    location_info = await geocoding_service.get_coordinates(request.city, request.country)
    lat = location_info["latitude"]
    lon = location_info["longitude"]

    # Fetch ~1 year of historical data
    end_date = date.today() - timedelta(days=6)  # archive has ~5-day lag
    start_date = end_date - timedelta(days=365)

    try:
        historical_raw = await weather_service.get_historical_weather(
            lat, lon,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        daily = historical_raw.get("daily", {})
        times = daily.get("time", [])

        if times:
            rows = []
            for i, t in enumerate(times):
                temp = daily.get("temperature_2m_mean", [None])[i] or 25.0
                hum = daily.get("relativehumidity_2m_mean", [None])[i] or 60.0
                pres = daily.get("pressure_msl_mean", [None])[i] or 1013.25
                wind = daily.get("windspeed_10m_mean", [None])[i] or 0.0
                parsed = date.fromisoformat(str(t))
                rows.append(
                    {
                        "temperature": temp,
                        "humidity": hum,
                        "pressure": pres,
                        "wind_speed": wind,
                        "month": float(parsed.month),
                        "hour": 12.0,
                    }
                )
            df = pd.DataFrame(rows)
        else:
            df = pd.DataFrame()
    except Exception as exc:
        logger.warning("Historical fetch failed (%s) — using synthetic data.", exc)
        df = pd.DataFrame()

    # Add physics-based target column
    if not df.empty:
        df["water_output"] = df.apply(
            lambda row: awg_model.physics_water_output(
                row["temperature"], row["humidity"], row["pressure"], row["wind_speed"]
            ),
            axis=1,
        )

    metrics = awg_model.train(df)

    # Persist the newly trained model
    from app.config import settings  # local import to avoid circular issues at module load
    try:
        awg_model.save(settings.model_path_resolved)
    except Exception as exc:
        logger.warning("Could not persist model: %s", exc)

    return TrainResponse(
        message="Model trained successfully.",
        metrics=metrics,
        model_trained=awg_model.is_trained,
    )


# ---------------------------------------------------------------------------
# GET /api/forecast/{city}  — 7-day forecast with predictions
# ---------------------------------------------------------------------------


@router.get(
    "/forecast/{city}",
    response_model=ForecastResponse,
    summary="7-day AWG forecast for a city",
)
async def get_forecast(
    city: str,
    country: Optional[str] = Query(None, description="Optional country hint"),
) -> ForecastResponse:
    """Return a 7-day daily forecast with AWG water-output predictions."""
    location_info = await geocoding_service.get_coordinates(city, country)
    lat = location_info["latitude"]
    lon = location_info["longitude"]
    elevation = location_info.get("elevation", 0.0)
    location_name = f"{location_info['name']}, {location_info['country']}".strip(", ")

    forecast = await awg_analyzer.build_forecast(lat, lon, elevation)

    return ForecastResponse(
        location=location_name,
        coordinates={"latitude": lat, "longitude": lon},
        forecast=forecast,
    )
