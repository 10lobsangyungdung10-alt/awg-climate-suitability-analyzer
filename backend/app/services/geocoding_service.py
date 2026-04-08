"""
Geocoding service using the Open-Meteo Geocoding API.

No API key is required.  Documentation:
  https://open-meteo.com/en/docs/geocoding-api
"""

from __future__ import annotations

from typing import Optional

import httpx
from fastapi import HTTPException, status

from app.utils.constants import OPEN_METEO_GEOCODING_URL


async def get_coordinates(city: str, country: Optional[str] = None) -> dict:
    """
    Resolve a city name to geographic coordinates.

    Parameters
    ----------
    city:
        The city name to look up (e.g. ``"Singapore"``).
    country:
        Optional country name or ISO code used to disambiguate results.

    Returns
    -------
    dict
        ``{"latitude": float, "longitude": float, "name": str,
           "country": str, "elevation": float}``

    Raises
    ------
    HTTPException
        404 when the city cannot be found.
        502 when the upstream geocoding API is unreachable.
    """
    params: dict = {"name": city, "count": 5, "language": "en", "format": "json"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPEN_METEO_GEOCODING_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Geocoding API timed out — please try again later.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Geocoding API returned an error: {exc.response.status_code}",
        ) from exc

    results = data.get("results")
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City '{city}' could not be found. Please check the spelling.",
        )

    # If a country hint was supplied, try to find a matching result.
    best = results[0]
    if country:
        country_lower = country.lower()
        for result in results:
            if country_lower in (result.get("country", "") or "").lower() or country_lower in (
                result.get("country_code", "") or ""
            ).lower():
                best = result
                break

    return {
        "latitude": best["latitude"],
        "longitude": best["longitude"],
        "name": best.get("name", city),
        "country": best.get("country", ""),
        "elevation": best.get("elevation", 0.0),
    }
