/**
 * PsychrometricDisplay component
 * Shows a table/grid of psychrometric air properties derived from current conditions.
 */

/** Individual row in the psychrometric table. */
function PsychRow({ icon, label, value, unit }) {
  return (
    <div className="psych-row">
      <span className="psych-icon" aria-hidden="true">{icon}</span>
      <span className="psych-label">{label}</span>
      <span className="psych-value">
        {value !== undefined && value !== null
          ? `${Number(value).toFixed(3)} ${unit}`
          : '—'}
      </span>
    </div>
  );
}

/**
 * @param {object} props
 * @param {object} props.psychrometric - Psychrometric properties object from API
 *   Expected keys: absolute_humidity, dew_point, wet_bulb_temperature,
 *                  specific_humidity, air_density
 */
export default function PsychrometricDisplay({ psychrometric }) {
  if (!psychrometric) return null;

  const {
    absolute_humidity,
    dew_point,
    wet_bulb_temperature,
    specific_humidity,
    air_density,
  } = psychrometric;

  const rows = [
    {
      icon: '💧',
      label: 'Absolute Humidity',
      value: absolute_humidity,
      unit: 'g/m³',
    },
    {
      icon: '❄️',
      label: 'Dew Point',
      value: dew_point,
      unit: '°C',
    },
    {
      icon: '🌡️',
      label: 'Wet Bulb Temp.',
      value: wet_bulb_temperature,
      unit: '°C',
    },
    {
      icon: '📊',
      label: 'Specific Humidity',
      value: specific_humidity,
      unit: 'g/kg',
    },
    {
      icon: '⚖️',
      label: 'Air Density',
      value: air_density,
      unit: 'kg/m³',
    },
  ];

  return (
    <div className="card psych-card">
      <h2 className="psych-title">
        <span aria-hidden="true">🔬</span> Psychrometric Properties
      </h2>
      <div className="psych-table">
        {rows.map((row) => (
          <PsychRow key={row.label} {...row} />
        ))}
      </div>
    </div>
  );
}
