"""
Weather data service using the Open-Meteo forecast and archive APIs.

No API key is required.  Documentation:
  https://open-meteo.com/en/docs
  https://open-meteo.com/en/docs/historical-weather-api
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.utils.constants import OPEN_METEO_ARCHIVE_URL, OPEN_METEO_FORECAST_URL


# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------


async def _get(url: str, params: dict) -> dict[str, Any]:
    """
    Execute an async GET request and return the parsed JSON body.

    Raises
    ------
    HTTPException
        502 on timeout or upstream HTTP error.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Weather API timed out — please try again.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Weather API error: {exc.response.status_code}",
        ) from exc


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def get_current_weather(
    lat: float, lon: float, elevation: float = 0.0
) -> dict[str, Any]:
    """
    Fetch current meteorological conditions from Open-Meteo.

    Parameters
    ----------
    lat, lon:
        WGS-84 coordinates.
    elevation:
        Site elevation in metres (passed to Open-Meteo for altitude correction).

    Returns
    -------
    dict
        Flat mapping of current weather variables.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,"
            "relativehumidity_2m,"
            "apparent_temperature,"
            "pressure_msl,"
            "windspeed_10m,"
            "precipitation,"
            "weathercode"
        ),
        "timezone": "auto",
        "forecast_days": 1,
    }
    if elevation:
        params["elevation"] = elevation

    data = await _get(OPEN_METEO_FORECAST_URL, params)
    current = data.get("current", {})
    units = data.get("current_units", {})

    return {
        "temperature": current.get("temperature_2m", 0.0),
        "humidity": current.get("relativehumidity_2m", 0.0),
        "pressure": current.get("pressure_msl", 1013.25),
        "wind_speed": current.get("windspeed_10m", 0.0),
        "precipitation": current.get("precipitation", 0.0),
        "apparent_temperature": current.get("apparent_temperature", 0.0),
        "weather_code": current.get("weathercode", 0),
        "units": units,
    }


async def get_historical_weather(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """
    Fetch daily historical weather from the Open-Meteo archive.

    Parameters
    ----------
    lat, lon:
        WGS-84 coordinates.
    start_date, end_date:
        ISO-8601 date strings (``"YYYY-MM-DD"``).

    Returns
    -------
    dict
        Raw Open-Meteo archive response including a ``daily`` key with
        parallel arrays for each requested variable.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": (
            "temperature_2m_mean,"
            "relativehumidity_2m_mean,"
            "pressure_msl_mean,"
            "windspeed_10m_mean,"
            "precipitation_sum"
        ),
        "timezone": "auto",
    }
    return await _get(OPEN_METEO_ARCHIVE_URL, params)


async def get_forecast(
    lat: float, lon: float, elevation: float = 0.0
) -> dict[str, Any]:
    """
    Fetch a 7-day daily forecast from Open-Meteo.

    Parameters
    ----------
    lat, lon:
        WGS-84 coordinates.
    elevation:
        Site elevation in metres.

    Returns
    -------
    dict
        Open-Meteo forecast response with a ``daily`` key containing
        parallel arrays for each requested variable.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": (
            "temperature_2m_mean,"
            "relativehumidity_2m_mean,"
            "pressure_msl_mean,"
            "windspeed_10m_mean,"
            "precipitation_sum,"
            "temperature_2m_max,"
            "temperature_2m_min"
        ),
        "timezone": "auto",
        "forecast_days": 7,
    }
    if elevation:
        params["elevation"] = elevation

    return await _get(OPEN_METEO_FORECAST_URL, params)
