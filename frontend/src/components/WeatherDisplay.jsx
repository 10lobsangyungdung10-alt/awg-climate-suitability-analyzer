/**
 * WeatherDisplay component
 * Shows a grid of current-conditions cards for the analyzed location.
 */

/**
 * Single metric card helper.
 */
function MetricCard({ icon, label, value, unit, colorClass }) {
  return (
    <div className={`metric-card ${colorClass || ''}`}>
      <span className="metric-icon" aria-hidden="true">{icon}</span>
      <div className="metric-body">
        <span className="metric-value">
          {value !== undefined && value !== null ? value : '—'}
          {unit && <span className="metric-unit"> {unit}</span>}
        </span>
        <span className="metric-label">{label}</span>
      </div>
    </div>
  );
}

/**
 * @param {object}  props
 * @param {object}  props.weather   - Current weather data object from the API
 * @param {object}  props.location  - Location metadata (name, lat, lon)
 */
export default function WeatherDisplay({ weather, location }) {
  if (!weather) return null;

  const {
    temperature,
    humidity,
    pressure,
    wind_speed,
    dew_point,
  } = weather;

  const locationName = location?.name || weather?.city || 'Unknown location';
  const lat = location?.latitude ?? weather?.latitude;
  const lon = location?.longitude ?? weather?.longitude;

  return (
    <div className="card weather-display">
      {/* Header row */}
      <div className="weather-header">
        <div>
          <h2 className="weather-title">
            <span aria-hidden="true">📍</span> {locationName}
          </h2>
          {lat !== undefined && lon !== undefined && (
            <p className="weather-coords">
              {Number(lat).toFixed(4)}°, {Number(lon).toFixed(4)}°
            </p>
          )}
        </div>
        <span className="weather-badge">Live Conditions</span>
      </div>

      {/* Metric grid */}
      <div className="metric-grid">
        <MetricCard
          icon="🌡️"
          label="Temperature"
          value={temperature !== undefined ? Number(temperature).toFixed(1) : undefined}
          unit="°C"
          colorClass="metric-temp"
        />
        <MetricCard
          icon="💧"
          label="Humidity"
          value={humidity !== undefined ? Number(humidity).toFixed(0) : undefined}
          unit="%"
          colorClass="metric-humid"
        />
        <MetricCard
          icon="🔵"
          label="Pressure"
          value={pressure !== undefined ? Number(pressure).toFixed(0) : undefined}
          unit="hPa"
          colorClass="metric-pressure"
        />
        <MetricCard
          icon="💨"
          label="Wind Speed"
          value={wind_speed !== undefined ? Number(wind_speed).toFixed(1) : undefined}
          unit="km/h"
          colorClass="metric-wind"
        />
        <MetricCard
          icon="🌫️"
          label="Dew Point"
          value={dew_point !== undefined ? Number(dew_point).toFixed(1) : undefined}
          unit="°C"
          colorClass="metric-dew"
        />
      </div>
    </div>
  );
}
