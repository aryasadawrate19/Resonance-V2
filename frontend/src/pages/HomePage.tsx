import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Scan, Sparkles, ChevronRight } from 'lucide-react';
import ImageUpload from '../components/ImageUpload';
import Questionnaire from '../components/Questionnaire';
import Disclaimer from '../components/Disclaimer';
import type { LifestyleInput, AnalyzeResponse } from '../types';
import { analyzeImage } from '../api/client';

interface Props {
  onAnalysisComplete: (data: AnalyzeResponse, lifestyle: LifestyleInput) => void;
  onAnalysisError: (error: string | null) => void;
}

export default function HomePage({ onAnalysisComplete, onAnalysisError }: Props) {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [lifestyle, setLifestyle] = useState<LifestyleInput>({
    skin_type: 'combination',
    sleep_quality: 3,
    diet_quality: 3,
    stress_level: 3,
    climate_zone: 'tropical',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (file: File | null) => {
    setSelectedFile(file);
    setError(null);
    onAnalysisError(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setError(null);
    onAnalysisError(null);

    try {
      const result = await analyzeImage(selectedFile, lifestyle);
      if (result.error) {
        const errorMsg = result.error;
        setError(errorMsg);
        onAnalysisError(errorMsg);
        navigate('/results');
        return;
      }

      if (result.face_detected === false || result.zones_approximate === true) {
        const rejectionMsg = "We couldn't clearly map a front-facing profile. To ensure accurate results, please upload a strictly front-facing selfie looking directly at the camera.";
        setError(rejectionMsg);
        onAnalysisError(rejectionMsg);
        return;
      }

      onAnalysisComplete(result, lifestyle);
      navigate('/results');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Analysis failed. Is the backend running?';
      setError(errorMsg);
      onAnalysisError(errorMsg);
      navigate('/results');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {loading && (
        <div className="loading-overlay">
          <div className="spinner" style={{ width: 56, height: 56, borderWidth: 4 }} />
          <div className="loading-text">Analyzing your skin with hybrid AI...</div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: 400, textAlign: 'center' }}>
            Running HuggingFace Transformer model + OpenCV pipeline.
            This can take 5–15 seconds on first run (model loading).
          </p>
        </div>
      )}

      <div className="page">
        <div className="container">
          {/* Hero Section */}
          <div className="hero">
            <div className="hero-eyebrow">
              <Sparkles size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 6 }} />
              AI-Powered Skin Intelligence
            </div>
            <h1 className="hero-title">
              Your Skin's <span>Digital Twin</span>
            </h1>
            <p className="hero-subtitle">
              Upload a face photo. Get AI-powered severity grading, lesion detection,
              zone mapping, predictions, and a personalized skincare routine — in seconds.
            </p>

            <div style={{ width: '100%', maxWidth: 600 }}>
              <ImageUpload
                onFileSelect={handleFileSelect}
                selectedFile={selectedFile}
              />
            </div>

            {selectedFile && (
              <div className="animate-slide-up" style={{ width: '100%', maxWidth: 600 }}>
                <Questionnaire
                  lifestyle={lifestyle}
                  onChange={setLifestyle}
                />

                {error && (
                  <div style={{
                    marginTop: 16,
                    padding: '12px 16px',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--accent-red)',
                    fontSize: '0.85rem',
                  }}>
                    ⚠ {error}
                  </div>
                )}

                <button
                  className="btn btn-primary"
                  onClick={handleAnalyze}
                  disabled={loading}
                  style={{ width: '100%', marginTop: 20, padding: '16px 32px', fontSize: '1rem' }}
                  id="analyze-btn"
                >
                  <Scan size={20} />
                  Analyze My Skin
                  <ChevronRight size={18} />
                </button>

                <Disclaimer />
                <div style={{ marginTop: 12 }} />
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
