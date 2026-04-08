/**
 * Dashboard page
 * Orchestrates state, API calls, and layout for all analysis components.
 */
import { useState } from 'react';
import LocationSearch from '../components/LocationSearch.jsx';
import WeatherDisplay from '../components/WeatherDisplay.jsx';
import SuitabilityScore from '../components/SuitabilityScore.jsx';
import ForecastChart from '../components/ForecastChart.jsx';
import SystemRecommendation from '../components/SystemRecommendation.jsx';
import LocationMap from '../components/LocationMap.jsx';
import PsychrometricDisplay from '../components/PsychrometricDisplay.jsx';
import { analyzeLocation } from '../services/api.js';

export default function Dashboard() {
  // ── State ──────────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [psychrometric, setPsychrometric] = useState(null);
  const [suitabilityScore, setSuitabilityScore] = useState(null);
  const [awgPrediction, setAwgPrediction] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [location, setLocation] = useState(null);

  // ── Handlers ───────────────────────────────────────────────────────────────
  async function handleSearch(city, country) {
    setLoading(true);
    setError(null);

    try {
      const data = await analyzeLocation(city, country);

      // Normalize response – backends may use slightly different key names
      setWeatherData(data.weather || data.current_weather || null);
      setPsychrometric(data.psychrometric || data.psychrometric_properties || null);
      setSuitabilityScore(
        data.suitability_score ??
          data.score ??
          data.awg_suitability_score ??
          null
      );
      setAwgPrediction(
        data.predicted_output ??
          data.awg_prediction ??
          data.water_output ??
          null
      );
      setRecommendation(data.system_recommendation || data.recommendation || null);
      setForecast(data.forecast || data.forecast_data || null);
      setLocation(
        data.location || {
          name: city,
          latitude: data.weather?.latitude ?? data.latitude,
          longitude: data.weather?.longitude ?? data.longitude,
        }
      );
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  }

  const hasData = weatherData !== null;

  return (
    <div className="dashboard">
      {/* ── App Header ─────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-inner">
          <div className="header-brand">
            <span className="header-icon" aria-hidden="true">💧</span>
            <div>
              <h1 className="header-title">AWG Climate Suitability Analyzer</h1>
              <p className="header-subtitle">
                Evaluate atmospheric water generation potential for any location
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* ── Main content ───────────────────────────────────────────────── */}
      <main className="dashboard-main">
        {/* Search bar – always visible */}
        <LocationSearch onSearch={handleSearch} loading={loading} error={error} />

        {/* Loading overlay while request is in flight */}
        {loading && (
          <div className="loading-overlay" role="status" aria-live="polite">
            <span className="spinner" aria-hidden="true" />
            <span className="loading-text">Analyzing location…</span>
          </div>
        )}

        {/* Welcome placeholder shown before any search */}
        {!hasData && !loading && (
          <div className="welcome-card card">
            <span className="welcome-icon" aria-hidden="true">🌍</span>
            <h2>Welcome to AWG Climate Suitability Analyzer</h2>
            <p>
              Enter a city name above to analyse local atmospheric conditions and
              discover the potential for harvesting drinking water from the air.
            </p>
            <ul className="feature-list">
              <li>🌡️ Real-time weather &amp; psychrometric data</li>
              <li>📊 7-day output forecast chart</li>
              <li>🗺️ Interactive location map</li>
              <li>⚙️ Personalised AWG system recommendation</li>
            </ul>
          </div>
        )}

        {/* ── Analysis results ─────────────────────────────────────────── */}
        {hasData && !loading && (
          <div className="results-grid">
            {/* Left column */}
            <div className="results-col-left">
              <WeatherDisplay weather={weatherData} location={location} />
              <PsychrometricDisplay psychrometric={psychrometric} />
              <SystemRecommendation
                recommendation={recommendation}
                predictedOutput={awgPrediction}
              />
            </div>

            {/* Right column */}
            <div className="results-col-right">
              <SuitabilityScore score={suitabilityScore} />
              <LocationMap
                latitude={location?.latitude}
                longitude={location?.longitude}
                locationName={location?.name}
              />
            </div>

            {/* Full-width forecast chart */}
            <div className="results-full-width">
              <ForecastChart forecast={forecast} />
            </div>
          </div>
        )}
      </main>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="app-footer">
        <p>AWG Climate Suitability Analyzer &copy; {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}
