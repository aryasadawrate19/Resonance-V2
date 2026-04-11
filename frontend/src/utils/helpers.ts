export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatScore(score: number): string {
  return `${score}/100`;
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'Clear': return '#22c55e';
    case 'Mild': return '#f59e0b';
    case 'Moderate': return '#f97316';
    case 'Severe': return '#ef4444';
    default: return '#6b7280';
  }
}

export function getScoreColor(score: number): string {
  if (score >= 80) return '#22c55e';
  if (score >= 60) return '#f59e0b';
  if (score >= 40) return '#f97316';
  return '#ef4444';
}

export function getDeltaColor(delta: number): string {
  if (delta > 0) return '#22c55e';
  if (delta < 0) return '#ef4444';
  return '#6b7280';
}

export function generateUID(): string {
  return 'user_' + Math.random().toString(36).substring(2, 10);
}

export function getStoredUID(): string {
  let uid = localStorage.getItem('dermatwin_uid');
  if (!uid) {
    uid = generateUID();
    localStorage.setItem('dermatwin_uid', uid);
  }
  return uid;
}
