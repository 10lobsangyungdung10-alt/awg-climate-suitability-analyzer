# AWG Climate Suitability Analyzer — Backend

A FastAPI backend that analyzes atmospheric water generation (AWG) suitability for any location using real-time weather data and a machine-learning model.

## Features

- **Real-time weather** via the [Open-Meteo](https://open-meteo.com/) free API (no API key required)
- **Psychrometric calculations** (absolute humidity, dew point, wet-bulb temperature, air density)
- **ML model** (Gradient Boosting) trained on physics-derived data to predict daily water output
- **7-day forecast** with per-day suitability scores
- **RESTful API** built with FastAPI + Pydantic v2

## Quick Start

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and (optionally) edit the environment file
cp .env.example .env

# 4. Run the development server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root — service info |
| GET | `/health` | Health check |
| POST | `/api/analyze` | Full AWG analysis for a location |
| GET | `/api/weather/{city}` | Current weather for a city |
| POST | `/api/predict` | Predict water output from weather data |
| GET | `/api/suitability/{city}` | Suitability score for a city |
| POST | `/api/train-model` | Train the ML model with historical data |
| GET | `/api/forecast/{city}` | 7-day forecast with AWG predictions |

## Example Request

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"city": "Singapore", "country": "Singapore"}'
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry-point
│   ├── config.py            # Settings (pydantic-settings)
│   ├── models/
│   │   ├── ml_model.py      # GradientBoosting AWG model
│   │   └── schemas.py       # Pydantic request/response schemas
│   ├── services/
│   │   ├── weather_service.py      # Open-Meteo weather calls
│   │   ├── geocoding_service.py    # Open-Meteo geocoding
│   │   ├── psychrometric_service.py # Thermodynamic calculations
│   │   └── awg_analyzer.py         # Full analysis pipeline
│   ├── api/
│   │   └── routes.py        # All API route handlers
│   └── utils/
│       └── constants.py     # Shared constants
├── models/                  # Persisted ML model artefacts
├── requirements.txt
├── .env.example
└── README.md
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `AWG Climate Suitability Analyzer` | Application display name |
| `DEBUG` | `true` | Enable debug mode |
| `ALLOWED_ORIGINS` | `http://localhost:5173,...` | CORS allowed origins (comma-separated) |
| `MODEL_PATH` | `models/awg_model.joblib` | Path to persisted ML model |
