import { AlertTriangle } from 'lucide-react';

export default function Disclaimer() {
  return (
    <div className="disclaimer">
      <AlertTriangle size={16} className="disclaimer-icon" />
      <span>
        <strong>Not a medical diagnosis.</strong> DermaTwin provides AI-generated
        evidence-based projections for educational purposes only. Always consult a
        qualified dermatologist for medical advice.
      </span>
    </div>
  );
}
