/**
 * LocationSearch component
 * Provides a city/country search form with loading and error feedback.
 */
import { useState } from 'react';

/**
 * @param {object}   props
 * @param {Function} props.onSearch  - Called with (city, country) when submitted
 * @param {boolean}  props.loading   - Disables form while a request is in flight
 * @param {string}   props.error     - Error message to display beneath the form
 */
export default function LocationSearch({ onSearch, loading, error }) {
  const [city, setCity] = useState('');
  const [country, setCountry] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    const trimmedCity = city.trim();
    if (!trimmedCity) return;
    onSearch(trimmedCity, country.trim());
  }

  return (
    <div className="card location-search">
      <h2 className="search-title">
        <span className="icon" aria-hidden="true">🔍</span>
        Analyze a Location
      </h2>

      <form onSubmit={handleSubmit} className="search-form" noValidate>
        <div className="search-inputs">
          {/* City name – required */}
          <div className="input-group">
            <label htmlFor="city-input" className="input-label">
              City Name <span className="required">*</span>
            </label>
            <input
              id="city-input"
              type="text"
              className="input"
              placeholder="e.g. Dubai"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              disabled={loading}
              required
              autoComplete="off"
            />
          </div>

          {/* Country – optional */}
          <div className="input-group">
            <label htmlFor="country-input" className="input-label">
              Country <span className="optional">(optional)</span>
            </label>
            <input
              id="country-input"
              type="text"
              className="input"
              placeholder="e.g. AE"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              disabled={loading}
              autoComplete="off"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary search-btn"
            disabled={loading || !city.trim()}
          >
            {loading ? (
              <>
                <span className="spinner spinner-sm" aria-hidden="true" />
                Analyzing…
              </>
            ) : (
              <>
                <span aria-hidden="true">🌍</span> Analyze
              </>
            )}
          </button>
        </div>
      </form>

      {/* Inline error message */}
      {error && (
        <div className="alert alert-error" role="alert">
          <span aria-hidden="true">⚠️</span> {error}
        </div>
      )}
    </div>
  );
}
