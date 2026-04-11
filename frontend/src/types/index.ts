// DermaTwin TypeScript type definitions

export interface LifestyleInput {
  skin_type: string;
  sleep_quality: number;
  diet_quality: number;
  stress_level: number;
  climate_zone: string;
  age?: number;
  gender?: string;
}

export interface LesionInfo {
  id: string;
  lesion_class: string;
  bbox: number[];
  confidence: number;
}

export interface ZoneInfo {
  forehead: number;
  left_cheek: number;
  right_cheek: number;
  nose: number;
  chin_jawline: number;
}

export interface ScoreBreakdown {
  acne: number;
  lesion: number;
  pigmentation: number;
  zone: number;
}

export interface PredictionResult {
  projected_score: number;
  delta: number;
  label: string;
}

export interface AnalyzeResponse {
  annotated_image: string;
  acne_severity: string;
  acne_coverage_pct: number;
  lesions: LesionInfo[];
  lesion_count: number;
  zones: ZoneInfo;
  face_detected: boolean;
  zones_approximate: boolean;
  hyperpigmentation_pct: number;
  skin_health_score: number;
  score_breakdown: ScoreBreakdown;
  prediction_7d: PredictionResult;
  prediction_30d: PredictionResult;
  severity_confidence: number;
  severity_source: string;
  ita_angle?: number;
  error?: string;
}

export interface SimulationRequest {
  skin_health_score: number;
  acne_severity: string;
  acne_coverage_pct: number;
  lesion_count: number;
  hyperpigmentation_pct: number;
  lifestyle: LifestyleInput;
  interventions: string[];
}

export interface InterventionDetail {
  key: string;
  label: string;
  description: string;
  acne_impact_pct: number;
  pigmentation_impact_pct: number;
}

export interface SimulationResult {
  original_score: number;
  projected_score: number;
  total_acne_delta: number;
  total_pigmentation_delta: number;
  projected_acne_coverage: number;
  projected_pigmentation: number;
  projected_severity: string;
  intervention_details: InterventionDetail[];
  disclaimer: string;
}

export interface RoutineStep {
  step: number;
  action: string;
  product_type: string;
  key_ingredient: string;
  why: string;
  budget_option?: string;
  premium_option?: string;
}

export interface RoutineResponse {
  morning_routine: RoutineStep[];
  night_routine: RoutineStep[];
  priority_ingredients: string[];
  expected_timeline: string;
  climate_note: string;
  disclaimer: string;
}

export interface HistoryEntry {
  scan_id: string;
  timestamp: string;
  skin_health_score: number;
  acne_severity: string;
  lesion_count: number;
  hyperpigmentation_pct: number;
  score_breakdown?: ScoreBreakdown;
}

export interface AvailableIntervention {
  key: string;
  label: string;
  description: string;
  acne_impact: string;
  pigmentation_impact: string;
}
