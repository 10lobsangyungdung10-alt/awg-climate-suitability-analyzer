"""
AWG Analyzer — orchestrates the full analysis pipeline.

This service ties together geocoding, weather fetching, psychrometric
calculations, ML prediction, and forecast generation into a single
``analyze_location`` call.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

import pandas as pd

from app.models.ml_model import awg_model
from app.models.schemas import (
    AnalysisResponse,
    AWGPrediction,
    ForecastDay,
    PsychrometricProperties,
    WeatherData,
)
from app.services import geocoding_service, weather_service
from app.services.psychrometric_service import (
    calculate_absolute_humidity,
    calculate_dew_point,
    get_all_psychrometric_properties,
)
from app.utils.constants import (
    AWG_SYSTEMS,
    DEW_POINT_EXCELLENT,
    DEW_POINT_FAIR,
    DEW_POINT_GOOD,
    HUMIDITY_EXCELLENT,
    HUMIDITY_FAIR,
    HUMIDITY_GOOD,
    HUMIDITY_POOR,
    STANDARD_PRESSURE_HPA,
    SUITABILITY_WEIGHTS,
    TEMP_MAX_OPTIMAL,
    TEMP_MIN_OPTIMAL,
)

logger = logging.getLogger(__name__)


class AWGAnalyzer:
    """
    High-level AWG suitability analysis orchestrator.

    All public methods are ``async`` so they can be awaited directly inside
    FastAPI route handlers.
    """

    # ------------------------------------------------------------------
    # Suitability scoring
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_suitability_score(
        weather_data: WeatherData,
        psychrometric_props: PsychrometricProperties,
    ) -> float:
        """
        Calculate a composite AWG suitability score on a 0–100 scale.

        Weights
        -------
        * Humidity    : 40 %
        * Temperature : 30 %
        * Pressure    : 15 %
        * Dew point   : 15 %

        Parameters
        ----------
        weather_data:
            Current weather observations.
        psychrometric_props:
            Derived psychrometric quantities.

        Returns
        -------
        float
            Suitability score between 0 (worst) and 100 (best).
        """
        humidity = weather_data.humidity
        temperature = weather_data.temperature
        pressure = weather_data.pressure
        dew_point = psychrometric_props.dew_point

        # --- Humidity factor (0–100) ---
        if humidity >= HUMIDITY_EXCELLENT:
            humidity_score = 100.0
        elif humidity >= HUMIDITY_GOOD:
            humidity_score = 70.0 + (humidity - HUMIDITY_GOOD) / (
                HUMIDITY_EXCELLENT - HUMIDITY_GOOD
            ) * 30.0
        elif humidity >= HUMIDITY_FAIR:
            humidity_score = 40.0 + (humidity - HUMIDITY_FAIR) / (
                HUMIDITY_GOOD - HUMIDITY_FAIR
            ) * 30.0
        elif humidity >= HUMIDITY_POOR:
            humidity_score = 10.0 + (humidity - HUMIDITY_POOR) / (
                HUMIDITY_FAIR - HUMIDITY_POOR
            ) * 30.0
        else:
            humidity_score = max(0.0, humidity / HUMIDITY_POOR * 10.0)

        # --- Temperature factor (0–100) ---
        if TEMP_MIN_OPTIMAL <= temperature <= TEMP_MAX_OPTIMAL:
            temperature_score = 100.0
        elif temperature < TEMP_MIN_OPTIMAL:
            temperature_score = max(0.0, (temperature - 5.0) / (TEMP_MIN_OPTIMAL - 5.0) * 100.0)
        else:  # above optimal
            temperature_score = max(0.0, (50.0 - temperature) / (50.0 - TEMP_MAX_OPTIMAL) * 100.0)

        # --- Pressure factor (0–100) ---
        pressure_diff = abs(pressure - STANDARD_PRESSURE_HPA)
        pressure_score = max(0.0, 100.0 - (pressure_diff / STANDARD_PRESSURE_HPA) * 500.0)

        # --- Dew-point factor (0–100) ---
        if dew_point >= DEW_POINT_EXCELLENT:
            dew_point_score = 100.0
        elif dew_point >= DEW_POINT_GOOD:
            dew_point_score = 70.0 + (dew_point - DEW_POINT_GOOD) / (
                DEW_POINT_EXCELLENT - DEW_POINT_GOOD
            ) * 30.0
        elif dew_point >= DEW_POINT_FAIR:
            dew_point_score = 30.0 + (dew_point - DEW_POINT_FAIR) / (
                DEW_POINT_GOOD - DEW_POINT_FAIR
            ) * 40.0
        else:
            dew_point_score = max(0.0, (dew_point + 10.0) / (DEW_POINT_FAIR + 10.0) * 30.0)

        weights = SUITABILITY_WEIGHTS
        composite = (
            humidity_score * weights["humidity"]
            + temperature_score * weights["temperature"]
            + pressure_score * weights["pressure"]
            + dew_point_score * weights["dew_point"]
        )
        return round(min(100.0, max(0.0, composite)), 2)

    # ------------------------------------------------------------------
    # System recommendation
    # ------------------------------------------------------------------

    @staticmethod
    def recommend_system(predicted_output: float) -> str:
        """
        Recommend an AWG system class based on predicted daily water output.

        Parameters
        ----------
        predicted_output:
            Predicted water output in L/day.

        Returns
        -------
        str
            One of ``"Small"``, ``"Medium"``, or ``"Large"``.
        """
        if predicted_output >= AWG_SYSTEMS["Large"]["capacity_liters_per_day"]:
            return "Large"
        if predicted_output >= AWG_SYSTEMS["Medium"]["capacity_liters_per_day"]:
            return "Medium"
        return "Small"

    # ------------------------------------------------------------------
    # Feature dict builder (shared by current + forecast predictions)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_feature_dict(
        temperature: float,
        humidity: float,
        pressure: float,
        wind_speed: float,
        month: int,
        hour: int = 12,
    ) -> dict:
        """Build the feature dictionary expected by :class:`~app.models.ml_model.AWGMLModel`."""
        dew_point = calculate_dew_point(temperature, humidity)
        absolute_humidity = calculate_absolute_humidity(temperature, humidity)
        return {
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "dew_point": dew_point,
            "absolute_humidity": absolute_humidity,
            "month": float(month),
            "hour": float(hour),
            "temp_rh_interaction": temperature * humidity,
            "pressure_adjusted": pressure / STANDARD_PRESSURE_HPA,
        }

    # ------------------------------------------------------------------
    # Full analysis pipeline
    # ------------------------------------------------------------------

    async def analyze_location(
        self, city: str, country: Optional[str] = None
    ) -> AnalysisResponse:
        """
        Run the full AWG suitability analysis for a geographic location.

        Steps
        -----
        1. Geocode the city to coordinates.
        2. Fetch current weather from Open-Meteo.
        3. Compute psychrometric properties.
        4. Auto-train the ML model if needed.
        5. Run ML prediction.
        6. Compute suitability score.
        7. Fetch 7-day forecast and generate per-day predictions.

        Parameters
        ----------
        city:
            City name.
        country:
            Optional country hint for disambiguation.

        Returns
        -------
        AnalysisResponse
            Complete analysis result.
        """
        # 1. Geocoding
        location_info = await geocoding_service.get_coordinates(city, country)
        lat = location_info["latitude"]
        lon = location_info["longitude"]
        elevation = location_info.get("elevation", 0.0)
        location_name = f"{location_info['name']}, {location_info['country']}".strip(", ")

        # 2. Current weather
        raw_weather = await weather_service.get_current_weather(lat, lon, elevation)

        temperature = raw_weather["temperature"]
        humidity = raw_weather["humidity"]
        pressure = raw_weather["pressure"]
        wind_speed = raw_weather["wind_speed"]

        dew_point = calculate_dew_point(temperature, humidity)
        absolute_humidity = calculate_absolute_humidity(temperature, humidity)

        current_weather = WeatherData(
            temperature=temperature,
            humidity=humidity,
            pressure=pressure,
            wind_speed=wind_speed,
            dew_point=dew_point,
            absolute_humidity=absolute_humidity,
            altitude=elevation,
        )

        # 3. Psychrometric properties
        psychrometric_props = get_all_psychrometric_properties(temperature, humidity, pressure)

        # 4. Ensure the model is trained
        if not awg_model.is_trained:
            logger.info("Auto-training model with synthetic data …")
            synthetic_df = awg_model.generate_training_data(lat=lat, lon=lon)
            awg_model.train(synthetic_df)
            # Persist the auto-trained model so future requests skip retraining
            from app.config import settings  # deferred to avoid circular import at module load
            try:
                awg_model.save(settings.model_path_resolved)
                logger.info("Auto-trained model persisted to %s", settings.model_path_resolved)
            except Exception as exc:
                logger.warning("Could not persist auto-trained model: %s", exc)

        # 5. ML prediction
        today = date.today()
        features = self._build_feature_dict(
            temperature, humidity, pressure, wind_speed, month=today.month
        )
        water_output, confidence = awg_model.predict(features)

        # 6. Suitability score
        suitability_score = self.calculate_suitability_score(current_weather, psychrometric_props)
        system_recommendation = self.recommend_system(water_output)

        awg_prediction = AWGPrediction(
            water_output_liters_per_day=water_output,
            suitability_score=suitability_score,
            system_recommendation=system_recommendation,
            confidence=confidence,
        )

        # 7. 7-day forecast
        forecast = await self.build_forecast(lat, lon, elevation)

        return AnalysisResponse(
            location=location_name,
            coordinates={"latitude": lat, "longitude": lon},
            current_weather=current_weather,
            psychrometric_props=psychrometric_props,
            awg_prediction=awg_prediction,
            forecast=forecast,
            model_trained=awg_model.is_trained,
        )

    # ------------------------------------------------------------------
    # Forecast helper (public)
    # ------------------------------------------------------------------

    async def build_forecast(
        self, lat: float, lon: float, elevation: float
    ) -> list[ForecastDay]:
        """
        Fetch the 7-day forecast and attach an AWG prediction for each day.

        Returns
        -------
        list[ForecastDay]
            Up to 7 daily entries; empty list if the API call fails.
        """
        try:
            raw_forecast = await weather_service.get_forecast(lat, lon, elevation)
        except Exception as exc:  # pragma: no cover
            logger.warning("Forecast fetch failed: %s", exc)
            return []

        daily = raw_forecast.get("daily", {})
        dates = daily.get("time", [])
        temps = daily.get("temperature_2m_mean", [])
        humidities = daily.get("relativehumidity_2m_mean", [])
        pressures = daily.get("pressure_msl_mean", [])
        wind_speeds = daily.get("windspeed_10m_mean", [])

        forecast_days: list[ForecastDay] = []
        for i, day_date in enumerate(dates):
            temperature = temps[i] if i < len(temps) else 25.0
            humidity = humidities[i] if i < len(humidities) else 60.0
            pressure = pressures[i] if i < len(pressures) else 1013.25
            wind_speed = wind_speeds[i] if i < len(wind_speeds) else 0.0

            # Handle None values from API
            temperature = temperature if temperature is not None else 25.0
            humidity = humidity if humidity is not None else 60.0
            pressure = pressure if pressure is not None else 1013.25
            wind_speed = wind_speed if wind_speed is not None else 0.0

            parsed_date = date.fromisoformat(str(day_date))
            features = self._build_feature_dict(
                temperature, humidity, pressure, wind_speed, month=parsed_date.month
            )
            day_output, _ = awg_model.predict(features)

            psychro = get_all_psychrometric_properties(temperature, humidity, pressure)
            day_weather = WeatherData(
                temperature=temperature,
                humidity=humidity,
                pressure=pressure,
                wind_speed=wind_speed,
                dew_point=psychro.dew_point,
                absolute_humidity=psychro.absolute_humidity,
            )
            day_score = self.calculate_suitability_score(day_weather, psychro)

            forecast_days.append(
                ForecastDay(
                    date=str(day_date),
                    temperature=round(temperature, 2),
                    humidity=round(humidity, 2),
                    pressure=round(pressure, 2),
                    predicted_output=day_output,
                    suitability_score=day_score,
                )
            )
        return forecast_days


# Module-level singleton
awg_analyzer = AWGAnalyzer()
