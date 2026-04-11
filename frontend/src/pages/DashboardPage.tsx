import { useState, useEffect } from 'react';
import { BarChart3 } from 'lucide-react';
import ProgressChart from '../components/ProgressChart';
import type { HistoryEntry } from '../types';
import { getHistory } from '../api/client';
import { getStoredUID, getSeverityColor } from '../utils/helpers';

export default function DashboardPage() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await getHistory(getStoredUID());
        setHistory(res.scans || []);
      } catch {
        console.error('Failed to fetch history');
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  return (
    <div className="page">
      <div className="container">
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <BarChart3 size={28} style={{ color: 'var(--accent-green)' }} />
            Progress Dashboard
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Track your skin health over time. Complete multiple scans to see trends.
          </p>
        </div>

        {/* Chart */}
        <div className="glass-card" style={{ marginBottom: 32 }}>
          <h3 style={{ marginBottom: 16 }}>Score Trend</h3>
          {loading ? (
            <div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div className="spinner" />
            </div>
          ) : (
            <ProgressChart history={history} />
          )}
        </div>

        {/* History Table */}
        <div className="glass-card">
          <h3 style={{ marginBottom: 16 }}>Scan History</h3>
          {history.length === 0 ? (
            <div className="empty-state">
              <p>No scans recorded yet. Upload an image and save your first scan.</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <th style={{ padding: '10px 12px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Date</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Score</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Severity</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Lesions</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Pigmentation</th>
                  </tr>
                </thead>
                <tbody>
                  {[...history].reverse().map((entry) => (
                    <tr key={entry.scan_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>
                        {new Date(entry.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                        {entry.skin_health_score}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <span style={{ color: getSeverityColor(entry.acne_severity), fontWeight: 600 }}>
                          {entry.acne_severity}
                        </span>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
                        {entry.lesion_count}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
                        {entry.hyperpigmentation_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div style={{ height: 60 }} />
      </div>
    </div>
  );
}
