import axios from 'axios';
import type { AnalyzeResponse, SimulationRequest, SimulationResult, RoutineResponse, HistoryEntry, AvailableIntervention, LifestyleInput } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 minutes for model inference
});

export async function analyzeImage(
  imageFile: File,
  lifestyle: LifestyleInput
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('lifestyle', JSON.stringify(lifestyle));

  const response = await api.post<AnalyzeResponse>('/api/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function simulateTreatment(
  request: SimulationRequest
): Promise<SimulationResult> {
  const response = await api.post<SimulationResult>('/api/simulate', request);
  return response.data;
}

export async function generateRoutine(
  profile: Record<string, unknown>
): Promise<RoutineResponse> {
  const response = await api.post<RoutineResponse>('/api/routine', profile);
  return response.data;
}

export async function getHistory(uid: string): Promise<{ scans: HistoryEntry[] }> {
  const response = await api.get(`/api/history/${uid}`);
  return response.data;
}

export async function saveHistory(uid: string, scanData: Record<string, unknown>): Promise<{ scan_id: string }> {
  const response = await api.post('/api/history', { uid, scan_data: scanData });
  return response.data;
}

export async function getInterventions(): Promise<AvailableIntervention[]> {
  const response = await api.get('/api/interventions');
  return response.data.interventions;
}

export async function getApiStatus(): Promise<Record<string, unknown>> {
  const response = await api.get('/api/status');
  return response.data;
}
