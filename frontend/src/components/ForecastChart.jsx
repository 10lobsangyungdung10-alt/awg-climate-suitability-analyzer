/**
 * ForecastChart component
 * Renders a 7-day forecast line chart using Chart.js via react-chartjs-2.
 * Shows predicted water output (L/day) on the primary Y-axis and
 * suitability score on the secondary Y-axis.
 */
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register all required Chart.js components before use.
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

/**
 * Format an ISO date string (or any date string) to a short "Mon DD" label.
 */
function shortDate(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}

/**
 * @param {object}   props
 * @param {object[]} props.forecast - Array of ForecastDay objects from the API
 *   Each item should have: date, temperature, humidity, water_output, suitability_score
 */
export default function ForecastChart({ forecast }) {
  if (!forecast || forecast.length === 0) return null;

  const labels = forecast.map((d) => shortDate(d.date));

  const data = {
    labels,
    datasets: [
      {
        label: 'Water Output (L/day)',
        data: forecast.map((d) => Number(d.water_output ?? d.predicted_output ?? 0).toFixed(2)),
        yAxisID: 'yOutput',
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33,150,243,0.12)',
        fill: true,
        tension: 0.4,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: '#2196F3',
      },
      {
        label: 'Suitability Score',
        data: forecast.map((d) => Number(d.suitability_score ?? d.score ?? 0).toFixed(1)),
        yAxisID: 'yScore',
        borderColor: '#4CAF50',
        backgroundColor: 'rgba(76,175,80,0.08)',
        fill: false,
        tension: 0.4,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: '#4CAF50',
        borderDash: [5, 3],
      },
      {
        label: 'Temperature (°C)',
        data: forecast.map((d) => Number(d.temperature ?? 0).toFixed(1)),
        yAxisID: 'yOutput',
        borderColor: '#FF9800',
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#FF9800',
        borderDash: [3, 3],
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: { usePointStyle: true, padding: 20, color: '#555' },
      },
      title: {
        display: true,
        text: '7-Day Forecast',
        color: '#333',
        font: { size: 16, weight: 'bold' },
        padding: { bottom: 12 },
      },
      tooltip: {
        callbacks: {
          // Add units to tooltip labels
          label(ctx) {
            const units = {
              'Water Output (L/day)': ' L/day',
              'Suitability Score': '',
              'Temperature (°C)': ' °C',
            };
            const unit = units[ctx.dataset.label] ?? '';
            return ` ${ctx.dataset.label}: ${ctx.parsed.y}${unit}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(0,0,0,0.05)' },
        ticks: { color: '#555', maxRotation: 30 },
      },
      yOutput: {
        type: 'linear',
        position: 'left',
        title: { display: true, text: 'L/day  |  °C', color: '#555' },
        grid: { color: 'rgba(0,0,0,0.05)' },
        ticks: { color: '#555' },
      },
      yScore: {
        type: 'linear',
        position: 'right',
        min: 0,
        max: 100,
        title: { display: true, text: 'Suitability Score', color: '#4CAF50' },
        grid: { drawOnChartArea: false },
        ticks: { color: '#4CAF50' },
      },
    },
  };

  return (
    <div className="card forecast-card">
      <div className="forecast-chart-container">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
