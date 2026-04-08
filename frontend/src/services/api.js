/**
 * API service layer for the AWG Climate Suitability Analyzer.
 * All backend communication is centralized here.
 * The base URL defaults to an empty string so Vite's dev-server proxy
 * forwards /api/* requests to the FastAPI backend at http://localhost:8000.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

/**
 * Run a full climate analysis for the given city (and optional country).
 * Returns combined weather, psychrometric, suitability score, AWG prediction
 * and a 7-day forecast in one response.
 *
 * @param {string} city
 * @param {string} [country]
 * @returns {Promise<object>}
 */
export async function analyzeLocation(city, country = '') {
  try {
    const response = await api.post('/api/analyze', { city, country });
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail ||
        error.message ||
        'Failed to analyze location'
    );
  }
}

/**
 * Fetch current weather data for a city.
 *
 * @param {string} city
 * @returns {Promise<object>}
 */
export async function getWeather(city) {
  try {
    const response = await api.get(`/api/weather/${encodeURIComponent(city)}`);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail ||
        error.message ||
        'Failed to fetch weather data'
    );
  }
}

/**
 * Fetch 7-day forecast data for a city.
 *
 * @param {string} city
 * @returns {Promise<object[]>}
 */
export async function getForecast(city) {
  try {
    const response = await api.get(`/api/forecast/${encodeURIComponent(city)}`);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail ||
        error.message ||
        'Failed to fetch forecast data'
    );
  }
}

/**
 * Fetch the AWG suitability score for a city.
 *
 * @param {string} city
 * @returns {Promise<object>}
 */
export async function getSuitability(city) {
  try {
    const response = await api.get(
      `/api/suitability/${encodeURIComponent(city)}`
    );
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail ||
        error.message ||
        'Failed to fetch suitability score'
    );
  }
}

/**
 * Trigger model training on the backend.
 *
 * @returns {Promise<object>}
 */
export async function trainModel() {
  try {
    const response = await api.post('/api/train-model');
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail ||
        error.message ||
        'Failed to train model'
    );
  }
}

/**
 * Predict AWG water output from a weather data object.
 *
 * @param {object} weatherData
 * @returns {Promise<object>}
 */
export async function predictOutput(weatherData) {
  try {
    const response = await api.post('/api/predict', weatherData);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail ||
        error.message ||
        'Failed to predict water output'
    );
  }
}
