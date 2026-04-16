import { useEffect, useState } from 'react';
import type { ScoreBreakdown } from '../types';
import { getScoreColor } from '../utils/helpers';

interface Props {
  score: number;
  breakdown: ScoreBreakdown;
  severity: string;
  severityConfidence: number;
  severitySource: string;
}

export default function SkinScoreCard({ score, breakdown, severity, severityConfidence, severitySource }: Props) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const scoreColor = getScoreColor(score);
  const circumference = 283; // 2 * PI * 45
  const offset = circumference - (score / 100) * circumference;

  useEffect(() => {
    let frame: number;
    const duration = 1500;
    const start = performance.now();

    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setAnimatedScore(Math.round(eased * score));
      if (progress < 1) frame = requestAnimationFrame(animate);
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const barData = [
    { name: 'Acne Health', value: breakdown.acne, weight: '35%', color: scoreColor },
    { name: 'Lesion Health', value: breakdown.lesion, weight: '25%', color: 'var(--accent-blue)' },
    { name: 'Pigmentation Health', value: breakdown.pigmentation, weight: '20%', color: 'var(--accent-purple)' },
    { name: 'Zone Health', value: breakdown.zone, weight: '20%', color: 'var(--accent-orange)' },
  ];

  return (
    <div className="glass-card animate-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
        <h3>Skin Health Score</h3>
        <span
          className={`badge ${
            severity === 'Clear' ? 'badge-green' :
            severity === 'Mild' ? 'badge-amber' :
            severity === 'Moderate' ? 'badge-orange' : 'badge-red'
          }`}
          style={{ marginLeft: 'auto' }}
        >
          {severity}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: 32, alignItems: 'center' }}>
        {/* Score Ring */}
        <div className="score-ring-container">
          <svg className="score-ring" viewBox="0 0 100 100">
            <circle className="score-ring-bg" cx="50" cy="50" r="45" />
            <circle
              className="score-ring-fill"
              cx="50" cy="50" r="45"
              stroke={scoreColor}
              style={{ '--score-offset': `${offset}` } as React.CSSProperties}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="score-value">
            <div className="score-number" style={{ color: scoreColor }}>
              {animatedScore}
            </div>
            <div className="score-label">of 100</div>
          </div>
        </div>

        {/* Breakdown Bars */}
        <div>
          {barData.map((bar) => (
            <div className="score-bar" key={bar.name}>
              <div className="score-bar-header">
                <span className="score-bar-name">{bar.name} ({bar.weight})</span>
                <span className="score-bar-value" style={{ color: bar.color }}>{bar.value}</span>
              </div>
              <div className="score-bar-track">
                <div
                  className="score-bar-fill"
                  style={{
                    '--bar-width': `${bar.value}%`,
                    width: `${bar.value}%`,
                    background: bar.color,
                  } as React.CSSProperties}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 16, fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
        Classified by: {severitySource} · {Math.round(severityConfidence * 100)}% confidence
      </div>
    </div>
  );
}
