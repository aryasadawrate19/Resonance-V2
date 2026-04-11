import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { PredictionResult } from '../types';
import { getDeltaColor } from '../utils/helpers';

interface Props {
  prediction7d: PredictionResult;
  prediction30d: PredictionResult;
  currentScore: number;
}

export default function PredictionCard({ prediction7d, prediction30d }: Props) {
  const renderPrediction = (pred: PredictionResult, timeframe: string) => {
    const deltaColor = getDeltaColor(pred.delta);
    const DeltaIcon = pred.delta > 0 ? TrendingUp : pred.delta < 0 ? TrendingDown : Minus;

    return (
      <div className="prediction-card glass-card">
        <div className="prediction-timeframe">{timeframe}</div>
        <div className="prediction-score" style={{ color: deltaColor }}>
          {pred.projected_score}
        </div>
        <div className="prediction-delta" style={{ color: deltaColor }}>
          <DeltaIcon size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
          {pred.delta > 0 ? '+' : ''}{pred.delta} points
        </div>
        <div className="prediction-label">{pred.label}</div>
      </div>
    );
  };

  return (
    <div className="animate-in">
      <h3 style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
        <TrendingUp size={18} style={{ color: 'var(--accent-blue)' }} />
        Skin Predictions
      </h3>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 16 }}>
        Evidence-based projections based on your current skin condition and lifestyle factors.
      </p>
      <div className="grid-2">
        {renderPrediction(prediction7d, '7-Day Projection')}
        {renderPrediction(prediction30d, '30-Day Projection')}
      </div>
    </div>
  );
}
