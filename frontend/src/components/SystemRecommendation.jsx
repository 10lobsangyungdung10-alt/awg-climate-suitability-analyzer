/**
 * SystemRecommendation component
 * Recommends an AWG system size based on the predicted daily water output.
 */

/** System catalogue keyed by size tier. */
const SYSTEMS = {
  small: {
    name: 'Small AWG System',
    capacity: 10,
    icon: '🏠',
    colorClass: 'system-small',
    accentColor: '#64B5F6',
    useCase: 'Ideal for 1–2 people or a small household.',
    details: 'Compact unit, low power draw (~150 W), quiet operation.',
  },
  medium: {
    name: 'Medium AWG System',
    capacity: 25,
    icon: '🏢',
    colorClass: 'system-medium',
    accentColor: '#FF9800',
    useCase: 'Suitable for 5–8 people or a small office.',
    details: 'Mid-range unit (~400 W), can run on solar with battery backup.',
  },
  large: {
    name: 'Large AWG System',
    capacity: 50,
    icon: '🏭',
    colorClass: 'system-large',
    accentColor: '#4CAF50',
    useCase: 'Designed for 10+ people or commercial applications.',
    details: 'Industrial unit (~900 W), modular and scalable deployment.',
  },
};

/** Choose a tier based on predicted daily output. */
function selectTier(predictedOutput) {
  if (!predictedOutput) return 'small';
  if (predictedOutput >= 30) return 'large';
  if (predictedOutput >= 15) return 'medium';
  return 'small';
}

/**
 * @param {object} props
 * @param {string} [props.recommendation] - Explicit tier ('small'|'medium'|'large')
 * @param {number} [props.predictedOutput] - Predicted water output in L/day
 */
export default function SystemRecommendation({ recommendation, predictedOutput }) {
  const tier = recommendation?.toLowerCase() || selectTier(predictedOutput);
  const system = SYSTEMS[tier] || SYSTEMS.small;

  return (
    <div className={`card system-card ${system.colorClass}`}>
      <h2 className="system-title">
        <span aria-hidden="true">⚙️</span> Recommended System
      </h2>

      <div className="system-body" style={{ borderLeftColor: system.accentColor }}>
        {/* Icon + name */}
        <div className="system-header">
          <span className="system-icon" aria-hidden="true">{system.icon}</span>
          <div>
            <h3 className="system-name" style={{ color: system.accentColor }}>
              {system.name}
            </h3>
            <p className="system-capacity">
              Capacity: <strong>{system.capacity} L/day</strong>
            </p>
          </div>
        </div>

        {/* Specs */}
        <p className="system-use-case">{system.useCase}</p>
        <p className="system-details">{system.details}</p>

        {/* Predicted output chip */}
        {predictedOutput !== undefined && predictedOutput !== null && (
          <div className="system-output-chip" style={{ backgroundColor: system.accentColor }}>
            Predicted output: <strong>{Number(predictedOutput).toFixed(1)} L/day</strong>
          </div>
        )}
      </div>
    </div>
  );
}
