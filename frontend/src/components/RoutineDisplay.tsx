import { useState } from 'react';
import { Sun, Moon, Sparkles } from 'lucide-react';
import type { RoutineResponse } from '../types';

interface Props {
  routine: RoutineResponse;
}

export default function RoutineDisplay({ routine }: Props) {
  const [activeTab, setActiveTab] = useState<'morning' | 'night'>('morning');
  const steps = activeTab === 'morning' ? routine.morning_routine : routine.night_routine;

  return (
    <div className="animate-in">
      <h3 style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Sparkles size={18} style={{ color: 'var(--accent-amber)' }} />
        AI Skincare Routine
      </h3>

      <div className="tab-group">
        <button
          className={`tab-btn ${activeTab === 'morning' ? 'active' : ''}`}
          onClick={() => setActiveTab('morning')}
        >
          <Sun size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
          Morning
        </button>
        <button
          className={`tab-btn ${activeTab === 'night' ? 'active' : ''}`}
          onClick={() => setActiveTab('night')}
        >
          <Moon size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
          Night
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {steps.map((step) => (
          <div className="routine-step" key={step.step}>
            <div className="routine-step-num">{step.step}</div>
            <div className="routine-step-content">
              <div className="routine-step-action">{step.action}</div>
              <div className="routine-step-product">
                {step.product_type} — {step.key_ingredient}
              </div>
              <div className="routine-step-why">{step.why}</div>
              {(step.budget_option || step.premium_option) && (
                <div className="routine-step-options">
                  {step.budget_option && (
                    <span className="badge badge-green">💰 {step.budget_option}</span>
                  )}
                  {step.premium_option && (
                    <span className="badge badge-purple">✨ {step.premium_option}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {routine.priority_ingredients && routine.priority_ingredients.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <h4 style={{ fontSize: '0.9rem', marginBottom: 8 }}>Priority Ingredients</h4>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {routine.priority_ingredients.map((ing) => (
              <span key={ing} className="badge badge-blue">{ing}</span>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <p style={{ fontSize: '0.82rem', color: 'var(--accent-teal)' }}>
          ⏱ {routine.expected_timeline}
        </p>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 4 }}>
          🌍 {routine.climate_note}
        </p>
      </div>

      {routine.disclaimer && (
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 12, fontStyle: 'italic' }}>
          {routine.disclaimer}
        </p>
      )}
    </div>
  );
}
