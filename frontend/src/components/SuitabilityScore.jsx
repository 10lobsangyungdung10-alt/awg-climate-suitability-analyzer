/**
 * SuitabilityScore component
 * Renders an animated circular gauge showing the AWG suitability score (0-100).
 */
import { useEffect, useState } from 'react';

/** Map a score to a CSS colour class and a human-readable label. */
function getScoreCategory(score) {
  if (score >= 81) return { label: 'Excellent', colorClass: 'score-excellent', color: '#4CAF50' };
  if (score >= 61) return { label: 'Good',      colorClass: 'score-good',      color: '#FF9800' };
  if (score >= 31) return { label: 'Fair',       colorClass: 'score-fair',      color: '#FFC107' };
  return              { label: 'Poor',       colorClass: 'score-poor',      color: '#f44336' };
}

/** Interpretation blurb shown beneath the score. */
function getInterpretation(score) {
  if (score >= 81)
    return 'Excellent conditions for atmospheric water generation. High water yield expected.';
  if (score >= 61)
    return 'Good conditions for AWG operation. Moderate-to-high water yield.';
  if (score >= 31)
    return 'Fair conditions. AWG can operate but efficiency may be limited.';
  return 'Poor conditions for AWG. Consider supplemental humidity sources.';
}

/**
 * @param {object} props
 * @param {number} props.score - AWG suitability score between 0 and 100
 */
export default function SuitabilityScore({ score }) {
  // Animate the displayed score from 0 to the target value.
  const [displayed, setDisplayed] = useState(0);

  useEffect(() => {
    if (score === undefined || score === null) return;
    setDisplayed(0);
    const target = Math.max(0, Math.min(100, Number(score)));
    let current = 0;
    const step = Math.ceil(target / 60); // ~60 frames
    const id = setInterval(() => {
      current = Math.min(current + step, target);
      setDisplayed(current);
      if (current >= target) clearInterval(id);
    }, 16);
    return () => clearInterval(id);
  }, [score]);

  if (score === undefined || score === null) return null;

  const { label, colorClass, color } = getScoreCategory(score);
  const interpretation = getInterpretation(score);

  // SVG arc parameters
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const progress = (displayed / 100) * circumference;
  const dash = `${progress} ${circumference}`;

  return (
    <div className={`card suitability-card ${colorClass}`}>
      <h2 className="suitability-title">AWG Suitability Score</h2>

      {/* Circular gauge */}
      <div className="gauge-wrapper">
        <svg
          viewBox="0 0 180 180"
          className="gauge-svg"
          role="img"
          aria-label={`Suitability score: ${Math.round(score)} out of 100 – ${label}`}
        >
          {/* Background track */}
          <circle
            cx="90" cy="90" r={radius}
            fill="none"
            stroke="#e0e0e0"
            strokeWidth="14"
          />
          {/* Coloured progress arc – starts at the top (−90°) */}
          <circle
            cx="90" cy="90" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="14"
            strokeDasharray={dash}
            strokeLinecap="round"
            transform="rotate(-90 90 90)"
            style={{ transition: 'stroke-dasharray 0.05s linear' }}
          />
          {/* Score text */}
          <text x="90" y="86" textAnchor="middle" className="gauge-score" fill={color}>
            {Math.round(displayed)}
          </text>
          <text x="90" y="108" textAnchor="middle" className="gauge-out-of" fill="#999">
            / 100
          </text>
        </svg>
      </div>

      {/* Label badge */}
      <div className="score-badge" style={{ backgroundColor: color }}>
        {label}
      </div>

      {/* Interpretation */}
      <p className="score-interpretation">{interpretation}</p>
    </div>
  );
}
