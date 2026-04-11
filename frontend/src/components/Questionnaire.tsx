import type { LifestyleInput } from '../types';

interface Props {
  lifestyle: LifestyleInput;
  onChange: (lifestyle: LifestyleInput) => void;
}

export default function Questionnaire({ lifestyle, onChange }: Props) {
  const update = (field: string, value: string | number) => {
    onChange({ ...lifestyle, [field]: value });
  };

  return (
    <div className="glass-card" style={{ marginTop: 24 }}>
      <h3 style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ color: 'var(--accent-green)' }}>●</span>
        Lifestyle Profile
      </h3>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 20 }}>
        These inputs improve prediction accuracy and personalize your skincare routine.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        <div className="input-group">
          <label>Skin Type</label>
          <select
            className="input-field"
            value={lifestyle.skin_type}
            onChange={(e) => update('skin_type', e.target.value)}
            id="skin-type-select"
          >
            <option value="oily">Oily</option>
            <option value="dry">Dry</option>
            <option value="combination">Combination</option>
            <option value="normal">Normal</option>
          </select>
        </div>

        <div className="input-group">
          <label>Sleep Quality (1-5)</label>
          <select
            className="input-field"
            value={lifestyle.sleep_quality}
            onChange={(e) => update('sleep_quality', Number(e.target.value))}
            id="sleep-quality-select"
          >
            <option value={1}>1 — Very Poor</option>
            <option value={2}>2 — Poor</option>
            <option value={3}>3 — Average</option>
            <option value={4}>4 — Good</option>
            <option value={5}>5 — Excellent</option>
          </select>
        </div>

        <div className="input-group">
          <label>Diet Quality (1-5)</label>
          <select
            className="input-field"
            value={lifestyle.diet_quality}
            onChange={(e) => update('diet_quality', Number(e.target.value))}
            id="diet-quality-select"
          >
            <option value={1}>1 — Very Unhealthy</option>
            <option value={2}>2 — Unhealthy</option>
            <option value={3}>3 — Average</option>
            <option value={4}>4 — Healthy</option>
            <option value={5}>5 — Very Healthy</option>
          </select>
        </div>

        <div className="input-group">
          <label>Stress Level (1-5)</label>
          <select
            className="input-field"
            value={lifestyle.stress_level}
            onChange={(e) => update('stress_level', Number(e.target.value))}
            id="stress-level-select"
          >
            <option value={1}>1 — Very Low</option>
            <option value={2}>2 — Low</option>
            <option value={3}>3 — Moderate</option>
            <option value={4}>4 — High</option>
            <option value={5}>5 — Very High</option>
          </select>
        </div>

        <div className="input-group">
          <label>Climate Zone</label>
          <select
            className="input-field"
            value={lifestyle.climate_zone}
            onChange={(e) => update('climate_zone', e.target.value)}
            id="climate-zone-select"
          >
            <option value="tropical">Tropical</option>
            <option value="humid">Humid</option>
            <option value="arid">Arid / Dry</option>
            <option value="temperate">Temperate</option>
            <option value="cold">Cold</option>
          </select>
        </div>
      </div>
    </div>
  );
}
