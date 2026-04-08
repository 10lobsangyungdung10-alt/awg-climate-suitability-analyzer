"""
Machine-learning model for AWG water-output prediction.

Architecture
------------
* Algorithm : ``sklearn.ensemble.GradientBoostingRegressor``
* Features  : temperature, humidity, pressure, wind_speed, dew_point,
              absolute_humidity, month, hour, temp_rh_interaction,
              pressure_adjusted
* Target    : daily water output (L/day) derived from a physics-based
              formula, making the labels interpretable and physically
              consistent.

The model trains itself on synthetic data if real historical observations are
not available (or insufficient), so it is immediately usable after startup
without any external pre-training step.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.utils.constants import FEATURE_COLUMNS, STANDARD_PRESSURE_HPA

logger = logging.getLogger(__name__)

# Minimum number of training rows required before we fall back to synthetic data.
_MIN_TRAINING_ROWS = 50


class AWGMLModel:
    """
    Gradient-Boosting regressor wrapped with feature engineering, scaling,
    and persistence helpers.

    Usage
    -----
    ::

        model = AWGMLModel()
        df    = model.generate_training_data(lat=1.3, lon=103.8)
        model.train(df)
        output, confidence = model.predict({"temperature": 28, "humidity": 75, ...})
    """

    FEATURE_COLUMNS: list[str] = FEATURE_COLUMNS

    def __init__(self) -> None:
        self._model: Optional[GradientBoostingRegressor] = None
        self._scaler: Optional[StandardScaler] = None
        self._trained: bool = False
        self._training_metrics: dict = {}

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_trained(self) -> bool:
        """Return ``True`` when the model has been successfully trained."""
        return self._trained

    # ------------------------------------------------------------------
    # Physics-based water-output formula
    # ------------------------------------------------------------------

    @staticmethod
    def _physics_water_output(
        temperature: float,
        humidity: float,
        pressure: float = 1013.25,
        wind_speed: float = 0.0,
    ) -> float:
        """
        Estimate AWG water output (L/day) from first-principles thermodynamics.

        The formula accounts for:
        * Condensation rate proportional to absolute humidity and airflow.
        * Temperature-dependent COP (coefficient of performance) of the
          refrigeration cycle.
        * Pressure correction for high-altitude sites.

        Parameters
        ----------
        temperature:
            Dry-bulb temperature in °C.
        humidity:
            Relative humidity in %.
        pressure:
            Atmospheric pressure in hPa.
        wind_speed:
            Wind speed in km/h (increases air throughput slightly).

        Returns
        -------
        float
            Estimated water output in litres per day, clamped to [0, 200].
        """
        if humidity < 20 or temperature < 5:
            return 0.0

        # Saturation vapour pressure via Magnus formula (hPa)
        e_s = 6.1078 * math.exp(17.625 * temperature / (243.04 + temperature))
        # Actual vapour pressure (hPa)
        e_a = (humidity / 100.0) * e_s
        # Absolute humidity (g/m³)
        abs_hum = (e_a * 100.0 * 18.015) / (8.314 * (temperature + 273.15))

        # COP decreases outside 15–40 °C range
        if temperature < 15:
            cop_factor = max(0.1, (temperature - 5) / 10.0)
        elif temperature > 40:
            cop_factor = max(0.3, 1.0 - (temperature - 40) / 20.0)
        else:
            cop_factor = 1.0

        # Altitude / pressure correction
        pressure_factor = pressure / STANDARD_PRESSURE_HPA

        # Wind bonus: more airflow → more condensation, up to +20 %
        wind_factor = 1.0 + min(0.20, wind_speed / 500.0)

        # Base output: condensation rate × 24 h × operational efficiency
        # 0.35 is the assumed fraction of AH extractable per pass (empirical)
        base_output = abs_hum * 0.35 * 24.0 * cop_factor * pressure_factor * wind_factor

        return round(max(0.0, min(200.0, base_output)), 3)

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    @staticmethod
    def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add engineered features to a raw weather DataFrame in-place.

        Parameters
        ----------
        df:
            Must contain at least: temperature, humidity, pressure.

        Returns
        -------
        pd.DataFrame
            The same DataFrame with new columns added.
        """
        df = df.copy()
        if "month" not in df.columns:
            df["month"] = 6  # fallback to mid-year
        if "hour" not in df.columns:
            df["hour"] = 12  # fallback to noon

        df["temp_rh_interaction"] = df["temperature"] * df["humidity"]
        df["pressure_adjusted"] = df["pressure"] / STANDARD_PRESSURE_HPA

        # Ensure all expected columns exist, filling with sensible defaults.
        for col in FEATURE_COLUMNS:
            if col not in df.columns:
                df[col] = 0.0

        return df

    # ------------------------------------------------------------------
    # Synthetic training data generation
    # ------------------------------------------------------------------

    def generate_training_data(
        self,
        lat: float = 0.0,
        lon: float = 0.0,
        n_samples: int = 2000,
    ) -> pd.DataFrame:
        """
        Generate a synthetic training dataset using the physics formula.

        Samples are drawn from realistic meteorological distributions so the
        model learns a smooth response surface even without real observations.

        Parameters
        ----------
        lat, lon:
            Geographic coordinates (used to add a mild seasonal bias based
            on hemisphere).
        n_samples:
            Number of synthetic records to generate.

        Returns
        -------
        pd.DataFrame
            DataFrame with all FEATURE_COLUMNS plus a ``water_output`` target.
        """
        rng = np.random.default_rng(seed=42)

        # Seasonal variation: southern hemisphere gets inverted months
        hemisphere_sign = -1 if lat < 0 else 1

        months = rng.integers(1, 13, size=n_samples)
        hours = rng.integers(0, 24, size=n_samples)

        # Seasonal temperature modulation (±5 °C around a mean of 25 °C)
        seasonal_temp_offset = hemisphere_sign * 5.0 * np.sin(
            2 * np.pi * (months - 3) / 12
        )
        temperature = np.clip(
            rng.normal(25.0, 8.0, n_samples) + seasonal_temp_offset, 5.0, 50.0
        )

        # Higher humidity in hotter months (rough tropical approximation)
        humidity_base = 65.0 - abs(lat) * 0.3  # tropics tend to be more humid
        humidity = np.clip(
            rng.normal(humidity_base, 15.0, n_samples)
            + 5.0 * np.sin(2 * np.pi * months / 12),
            10.0,
            100.0,
        )

        pressure = np.clip(rng.normal(1013.25, 8.0, n_samples), 950.0, 1050.0)
        wind_speed = np.clip(rng.exponential(10.0, n_samples), 0.0, 80.0)

        # Derived quantities
        dew_point = np.array(
            [
                self._physics_dew_point(t, h)
                for t, h in zip(temperature, humidity)
            ]
        )
        absolute_humidity = np.array(
            [
                (6.1078 * math.exp(17.625 * t / (243.04 + t)) * h / 100.0 * 100.0 * 18.015)
                / (8.314 * (t + 273.15))
                for t, h in zip(temperature, humidity)
            ]
        )

        # Physics-based target
        water_output = np.array(
            [
                self._physics_water_output(t, h, p, w)
                for t, h, p, w in zip(temperature, humidity, pressure, wind_speed)
            ]
        )
        # Add small Gaussian noise to prevent overfitting to the formula
        water_output += rng.normal(0.0, 0.05 * water_output.mean(), n_samples)
        water_output = np.clip(water_output, 0.0, 200.0)

        df = pd.DataFrame(
            {
                "temperature": temperature,
                "humidity": humidity,
                "pressure": pressure,
                "wind_speed": wind_speed,
                "dew_point": dew_point,
                "absolute_humidity": absolute_humidity,
                "month": months.astype(float),
                "hour": hours.astype(float),
                "water_output": water_output,
            }
        )
        return self._engineer_features(df)

    @staticmethod
    def _physics_dew_point(temp_c: float, rh_percent: float) -> float:
        """Inline Magnus dew-point (avoids circular import)."""
        rh_frac = max(1e-6, min(100.0, rh_percent)) / 100.0
        gamma = math.log(rh_frac) + (17.625 * temp_c) / (243.04 + temp_c)
        return (243.04 * gamma) / (17.625 - gamma)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, historical_data: pd.DataFrame) -> dict:
        """
        Train the Gradient Boosting model on the supplied data.

        If the DataFrame is too small (< ``_MIN_TRAINING_ROWS``), synthetic
        data is generated and appended.

        Parameters
        ----------
        historical_data:
            DataFrame that must contain the target column ``water_output``
            plus the feature columns defined in :attr:`FEATURE_COLUMNS`.

        Returns
        -------
        dict
            Training metrics: ``mae``, ``r2``, ``n_samples``.
        """
        df = historical_data.copy()

        # Supplement with synthetic data if necessary
        if len(df) < _MIN_TRAINING_ROWS:
            logger.info(
                "Only %d training rows — augmenting with synthetic data.", len(df)
            )
            synthetic = self.generate_training_data(n_samples=2000)
            df = pd.concat([df, synthetic], ignore_index=True)

        df = self._engineer_features(df)

        if "water_output" not in df.columns:
            raise ValueError("Training data must contain a 'water_output' target column.")

        X = df[self.FEATURE_COLUMNS].values
        y = df["water_output"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self._scaler = StandardScaler()
        X_train_scaled = self._scaler.fit_transform(X_train)
        X_test_scaled = self._scaler.transform(X_test)

        self._model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            min_samples_split=5,
            random_state=42,
        )
        self._model.fit(X_train_scaled, y_train)

        y_pred = self._model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        self._trained = True
        self._training_metrics = {
            "mae": round(float(mae), 4),
            "r2": round(float(r2), 4),
            "n_samples": len(df),
        }
        logger.info("Model trained — MAE=%.4f  R²=%.4f", mae, r2)
        return self._training_metrics

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features: dict) -> Tuple[float, float]:
        """
        Predict water output and return a confidence estimate.

        If the model has not been trained yet, it trains itself on synthetic
        data before predicting.

        Parameters
        ----------
        features:
            Dictionary with keys matching :attr:`FEATURE_COLUMNS`
            (extra keys are ignored; missing keys default to 0).

        Returns
        -------
        tuple[float, float]
            ``(water_output_liters_per_day, confidence)``
            where *confidence* is in the range [0, 1].
        """
        if not self._trained:
            logger.info("Model not yet trained — auto-training on synthetic data.")
            self.train(pd.DataFrame())  # empty df → triggers synthetic generation

        # Build a single-row DataFrame with all required features
        row = {col: features.get(col, 0.0) for col in self.FEATURE_COLUMNS}
        df_row = pd.DataFrame([row])
        df_row = self._engineer_features(df_row)

        X = df_row[self.FEATURE_COLUMNS].values
        X_scaled = self._scaler.transform(X)  # type: ignore[union-attr]

        prediction = float(self._model.predict(X_scaled)[0])  # type: ignore[union-attr]
        prediction = max(0.0, prediction)

        # Confidence: based on R² of training and how well input conditions
        # sit within the model's training distribution.
        base_confidence = self._training_metrics.get("r2", 0.85)
        # Penalise edge-case inputs
        humidity = features.get("humidity", 50.0)
        temperature = features.get("temperature", 25.0)
        if humidity < 20 or temperature < 5 or temperature > 50:
            confidence = max(0.3, base_confidence * 0.6)
        elif humidity < 35:
            confidence = max(0.4, base_confidence * 0.75)
        else:
            confidence = min(1.0, base_confidence)

        return round(prediction, 3), round(confidence, 3)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> None:
        """
        Persist the trained model and scaler to disk using joblib.

        Parameters
        ----------
        path:
            Destination file path (``*.joblib`` recommended).
        """
        if not self._trained:
            raise RuntimeError("Cannot save an untrained model.")
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"model": self._model, "scaler": self._scaler, "metrics": self._training_metrics},
            p,
        )
        logger.info("Model saved to %s", p)

    def load(self, path: str | Path) -> bool:
        """
        Load a previously saved model from disk.

        Parameters
        ----------
        path:
            Path to a joblib artefact created by :meth:`save`.

        Returns
        -------
        bool
            ``True`` if loading succeeded, ``False`` if the file was not found.
        """
        p = Path(path)
        if not p.exists():
            logger.warning("Model file not found at %s", p)
            return False
        artefact = joblib.load(p)
        self._model = artefact["model"]
        self._scaler = artefact["scaler"]
        self._training_metrics = artefact.get("metrics", {})
        self._trained = True
        logger.info("Model loaded from %s", p)
        return True


# Module-level singleton shared across the application lifetime.
awg_model = AWGMLModel()
