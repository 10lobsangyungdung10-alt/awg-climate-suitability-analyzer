"""
Application settings loaded from environment variables / .env file.

Uses pydantic-settings so every field can be overridden via the environment
without changing code.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object for the AWG backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    app_name: str = "AWG Climate Suitability Analyzer"
    debug: bool = False

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    #: Comma-separated list of allowed origins for CORS, or a Python list.
    allowed_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, value: object) -> List[str]:
        """Accept either a comma-separated string or a list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # ML model
    # ------------------------------------------------------------------
    #: Path (relative to the backend working directory) where the trained
    #: model artefact is stored / loaded.
    model_path: str = "models/awg_model.joblib"

    @property
    def model_path_resolved(self) -> Path:
        """Return the model path as an absolute :class:`~pathlib.Path`."""
        p = Path(self.model_path)
        if not p.is_absolute():
            # Resolve relative to the directory that contains this file's
            # parent package (i.e. the *backend/* directory).
            backend_dir = Path(__file__).parent.parent
            p = backend_dir / p
        return p


# Module-level singleton — import this everywhere instead of re-instantiating.
settings = Settings()
