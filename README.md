# AWG Climate Suitability Analyzer

A full-stack application that analyzes climate conditions and predicts Atmospheric Water Generator (AWG) performance for any location worldwide.

## Features

- **Geocoding**: Convert city names to coordinates using Open-Meteo Geocoding API
- **Weather Integration**: Real-time and 7-day forecast data via Open-Meteo (no API key required)
- **Psychrometric Calculations**: Absolute humidity, dew point, wet bulb temperature, air density
- **ML Predictions**: GradientBoosting model predicting daily water output (L/day)
- **Suitability Scoring**: 0–100 score based on humidity, temperature, pressure, and dew point
- **System Recommendations**: Small (10 L/day), Medium (25 L/day), or Large (50 L/day) AWG sizing
- **Interactive Dashboard**: React frontend with charts (Chart.js) and maps (Leaflet.js)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.10+) |
| ML | scikit-learn, pandas, numpy |
| Frontend | React 18 + Vite |
| Charts | Chart.js + react-chartjs-2 |
| Maps | Leaflet.js + react-leaflet |
| Weather API | Open-Meteo (free, no key needed) |

## Project Structure

```
AWG-Climate-Suitability-Analyzer/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # App entry point + CORS
│   │   ├── config.py           # pydantic-settings configuration
│   │   ├── models/             # ML model + Pydantic schemas
│   │   ├── services/           # Weather, geocoding, psychrometric, AWG
│   │   ├── api/routes.py       # REST endpoints
│   │   └── utils/constants.py  # App-wide constants
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # React + Vite application
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── pages/Dashboard.jsx # Main dashboard
│   │   └── services/api.js     # Axios API client
│   └── package.json
└── README.md
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

API available at: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at: http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Full climate analysis for a location |
| GET | `/api/weather/{city}` | Current weather data |
| POST | `/api/predict` | Predict water output from weather data |
| GET | `/api/suitability/{city}` | AWG suitability score |
| POST | `/api/train-model` | Train ML model with historical data |
| GET | `/api/forecast/{city}` | 7-day forecast with predictions |

## License

MIT