import { useState, useCallback } from 'react';
import { Beaker, Check, TrendingUp } from 'lucide-react';
import { simulateTreatment } from '../api/client';
import type { AnalyzeResponse, SimulationResult, LifestyleInput } from '../types';
import { getScoreColor } from '../utils/helpers';

const INTERVENTIONS = [
  { key: 'salicylic_acid', label: 'Salicylic Acid (2%)', desc: 'BHA exfoliant that unclogs pores', acne: '-35%', pigment: '-2%' },
  { key: 'improved_sleep', label: 'Improved Sleep (+2 hrs)', desc: 'Reduces cortisol-driven inflammation', acne: '-15%', pigment: '-5%' },
  { key: 'reduced_sugar', label: 'Reduced Sugar Intake', desc: 'Lower insulin-driven sebum', acne: '-20%', pigment: '-2%' },
  { key: 'niacinamide', label: 'Niacinamide Serum', desc: 'Reduces pigmentation & strengthens barrier', acne: '-10%', pigment: '-25%' },
  { key: 'spf_daily', label: 'SPF 50 Daily', desc: 'Prevents UV pigmentation', acne: '-2%', pigment: '-20%' },
  { key: 'hydration', label: 'Hydration (+2L Water)', desc: 'Supports skin barrier & healing', acne: '-10%', pigment: '-5%' },
];

interface Props {
  analysisData: AnalyzeResponse;
  lifestyle: LifestyleInput;
}

export default function SimulationPanel({ analysisData, lifestyle }: Props) {
  const [selected, setSelected] = useState<string[]>([]);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const toggle = (key: string) => {
    setSelected(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
    setResult(null);
  };

  const runSimulation = useCallback(async () => {
    if (selected.length === 0) return;
    setLoading(true);
    try {
      const res = await simulateTreatment({
        skin_health_score: analysisData.skin_health_score,
        acne_severity: analysisData.acne_severity,
        acne_coverage_pct: analysisData.acne_coverage_pct,
        lesion_count: analysisData.lesion_count,
        hyperpigmentation_pct: analysisData.hyperpigmentation_pct,
        lifestyle,
        interventions: selected,
      });
      setResult(res);
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setLoading(false);
    }
  }, [selected, analysisData, lifestyle]);

  return (
    <div className="animate-in">
      <h3 style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Beaker size={18} style={{ color: 'var(--accent-purple)' }} />
        Treatment Simulator
      </h3>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 16 }}>
        Toggle interventions to see projected improvement. Based on peer-reviewed evidence.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 20 }}>
        {INTERVENTIONS.map((item) => (
          <div
            key={item.key}
            className={`intervention-toggle ${selected.includes(item.key) ? 'active' : ''}`}
            onClick={() => toggle(item.key)}
            id={`intervention-${item.key}`}
          >
            <div className="intervention-checkbox">
              {selected.includes(item.key) && <Check size={14} color="#fff" />}
            </div>
            <div className="intervention-info">
              <div className="intervention-name">{item.label}</div>
              <div className="intervention-desc">{item.desc}</div>
            </div>
            <div className="intervention-impact">
              <div style={{ color: 'var(--accent-green)' }}>Acne: {item.acne}</div>
              <div style={{ color: 'var(--accent-purple)' }}>Pigment: {item.pigment}</div>
            </div>
          </div>
        ))}
      </div>

      <button
        className="btn btn-primary"
        onClick={runSimulation}
        disabled={loading || selected.length === 0}
        style={{ width: '100%' }}
        id="run-simulation-btn"
      >
        {loading ? (
          <><span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> Simulating...</>
        ) : (
          <><TrendingUp size={18} /> Simulate {selected.length} Intervention{selected.length !== 1 ? 's' : ''}</>
        )}
      </button>

      {result && (
        <div className="glass-card animate-in" style={{ marginTop: 20 }}>
          <h4 style={{ marginBottom: 16 }}>Simulation Results</h4>
          
          <div className="grid-2" style={{ marginBottom: 16 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Current</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: getScoreColor(result.original_score) }}>
                {result.original_score}
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Projected</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: getScoreColor(result.projected_score) }}>
                {result.projected_score}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
            <div className="badge badge-green">Acne: {result.total_acne_delta}%</div>
            <div className="badge badge-purple">Pigmentation: {result.total_pigmentation_delta}%</div>
            <div className={`badge ${
              result.projected_severity === 'Clear' ? 'badge-green' :
              result.projected_severity === 'Mild' ? 'badge-amber' : 'badge-orange'
            }`}>
              → {result.projected_severity}
            </div>
          </div>

          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
