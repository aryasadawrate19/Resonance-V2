import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Eye, MapPin, Droplets } from 'lucide-react';
import CanvasOverlay from '../components/CanvasOverlay';
import SkinScoreCard from '../components/SkinScoreCard';
import PredictionCard from '../components/PredictionCard';
import SimulationPanel from '../components/SimulationPanel';
import RoutineDisplay from '../components/RoutineDisplay';
import Disclaimer from '../components/Disclaimer';
import type { AnalyzeResponse, RoutineResponse, LifestyleInput } from '../types';
import { generateRoutine, saveHistory } from '../api/client';
import { getStoredUID, formatPercent } from '../utils/helpers';

interface Props {
  analysisData: AnalyzeResponse | null;
  lifestyle: LifestyleInput;
}

export default function ResultsPage({ analysisData, lifestyle }: Props) {
  const navigate = useNavigate();
  const [routine, setRoutine] = useState<RoutineResponse | null>(null);
  const [routineLoading, setRoutineLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!analysisData) {
      navigate('/');
      return;
    }

    // Auto-generate routine on mount
    const fetchRoutine = async () => {
      setRoutineLoading(true);
      try {
        const res = await generateRoutine({
          skin_type: lifestyle.skin_type,
          acne_severity: analysisData.acne_severity,
          acne_coverage_pct: analysisData.acne_coverage_pct,
          lesion_count: analysisData.lesion_count,
          hyperpigmentation_pct: analysisData.hyperpigmentation_pct,
          skin_health_score: analysisData.skin_health_score,
          sleep_quality: lifestyle.sleep_quality,
          diet_quality: lifestyle.diet_quality,
          stress_level: lifestyle.stress_level,
          climate_zone: lifestyle.climate_zone,
        });
        setRoutine(res);
      } catch {
        console.error('Failed to generate routine');
      } finally {
        setRoutineLoading(false);
      }
    };

    fetchRoutine();
  }, [analysisData, lifestyle, navigate]);

  const handleSave = async () => {
    if (!analysisData) return;
    try {
      await saveHistory(getStoredUID(), {
        skin_health_score: analysisData.skin_health_score,
        acne_severity: analysisData.acne_severity,
        lesion_count: analysisData.lesion_count,
        hyperpigmentation_pct: analysisData.hyperpigmentation_pct,
        score_breakdown: analysisData.score_breakdown,
      });
      setSaved(true);
    } catch {
      console.error('Failed to save scan');
    }
  };

  if (!analysisData) return null;

  return (
    <div className="page">
      <div className="container">
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
          <button className="btn btn-ghost" onClick={() => navigate('/')} id="back-btn">
            <ArrowLeft size={18} /> New Analysis
          </button>
          <button
            className={`btn ${saved ? 'btn-ghost' : 'btn-secondary'}`}
            onClick={handleSave}
            disabled={saved}
            id="save-scan-btn"
          >
            <Save size={16} />
            {saved ? 'Saved ✓' : 'Save to History'}
          </button>
        </div>

        {/* Row 1: Annotated Image + Score */}
        <div className="results-grid" style={{ marginBottom: 32 }}>
          <div>
            <div className="section-title" style={{ marginBottom: 12 }}>
              <Eye size={18} className="section-title-icon" />
              <h2>Annotated Analysis</h2>
              <div className="section-title-line" />
            </div>
            <CanvasOverlay base64Image={analysisData.annotated_image} />

            {/* Quick Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 12 }}>
              <div className="glass-card" style={{ padding: '12px 14px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  <Eye size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Lesions
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-red)' }}>
                  {analysisData.lesion_count}
                </div>
              </div>
              <div className="glass-card" style={{ padding: '12px 14px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  <MapPin size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Coverage
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-orange)' }}>
                  {formatPercent(analysisData.acne_coverage_pct)}
                </div>
              </div>
              <div className="glass-card" style={{ padding: '12px 14px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  <Droplets size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Pigment
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-purple)' }}>
                  {formatPercent(analysisData.hyperpigmentation_pct)}
                </div>
              </div>
            </div>
          </div>

          <div>
            <SkinScoreCard
              score={analysisData.skin_health_score}
              breakdown={analysisData.score_breakdown}
              severity={analysisData.acne_severity}
              severityConfidence={analysisData.severity_confidence}
              severitySource={analysisData.severity_source}
            />
          </div>
        </div>


        {/* Predictions */}
        <div style={{ marginBottom: 32 }}>
          <PredictionCard
            prediction7d={analysisData.prediction_7d}
            prediction30d={analysisData.prediction_30d}
            currentScore={analysisData.skin_health_score}
          />
        </div>

        {/* Simulation */}
        <div className="glass-card" style={{ marginBottom: 32 }}>
          <SimulationPanel analysisData={analysisData} lifestyle={lifestyle} />
        </div>

        {/* AI Routine */}
        <div className="glass-card" style={{ marginBottom: 32 }}>
          {routineLoading ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 20 }}>
              <div className="spinner" />
              <div>
                <p style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Generating personalized routine...</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Powered by Gemini AI</p>
              </div>
            </div>
          ) : routine ? (
            <RoutineDisplay routine={routine} />
          ) : (
            <p style={{ color: 'var(--text-muted)', padding: 20 }}>Routine generation unavailable.</p>
          )}
        </div>

        <Disclaimer />
        <div style={{ height: 60 }} />
      </div>
    </div>
  );
}
