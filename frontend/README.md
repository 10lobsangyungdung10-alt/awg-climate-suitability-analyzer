# AWG Climate Suitability Analyzer – Frontend

React + Vite frontend for the AWG (Atmospheric Water Generation) Climate Suitability Analyzer.

## Stack

| Library | Purpose |
|---|---|
| React 18 | UI framework |
| Vite 5 | Build tool & dev server |
| Axios | HTTP client |
| Chart.js + react-chartjs-2 | 7-day forecast chart |
| Leaflet + react-leaflet | Interactive map |

## Getting started

```bash
# Install dependencies
npm install

# Start dev server (proxies /api → http://localhost:8000)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `""` (uses Vite proxy) | Override backend base URL |

## Project structure

```
src/
├── components/
│   ├── LocationSearch.jsx      # City / country search form
│   ├── WeatherDisplay.jsx      # Current conditions grid
│   ├── SuitabilityScore.jsx    # Animated circular gauge
│   ├── ForecastChart.jsx       # 7-day Chart.js line chart
│   ├── SystemRecommendation.jsx # AWG system size card
│   ├── LocationMap.jsx         # Leaflet map with marker
│   └── PsychrometricDisplay.jsx# Air property table
├── pages/
│   └── Dashboard.jsx           # Main layout & state
├── services/
│   └── api.js                  # Axios API service layer
├── App.jsx
├── index.css
└── main.jsx
```

## Backend API contract

The frontend expects `POST /api/analyze` to return:

```jsonc
{
  "location":   { "name": "Dubai", "latitude": 25.2, "longitude": 55.27 },
  "weather":    { "temperature": 35, "humidity": 60, "pressure": 1010,
                  "wind_speed": 15, "dew_point": 26 },
  "psychrometric": {
    "absolute_humidity": 18.5, "dew_point": 26, "wet_bulb_temperature": 29,
    "specific_humidity": 15.8, "air_density": 1.18
  },
  "suitability_score": 72,
  "predicted_output":  18.4,
  "system_recommendation": "medium",
  "forecast": [
    { "date": "2024-01-01", "temperature": 35, "humidity": 60,
      "water_output": 18.4, "suitability_score": 72 }
    // … 7 items
  ]
}
```
