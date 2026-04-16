import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { HistoryEntry } from '../types';

interface Props {
  history: HistoryEntry[];
}

export default function ProgressChart({ history }: Props) {
  const chartData = useMemo(
    () =>
      [...history]
        .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
        .map((entry) => ({
          date: new Date(entry.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          skin_health_score: entry.skin_health_score,
        })),
    [history],
  );

  if (history.length < 2) {
    return (
      <div className="empty-state">
        <p>No history yet — scan again tomorrow to see your progress</p>
      </div>
    );
  }

  return (
    <div style={{ height: 320 }} id="progress-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="rgba(148, 163, 184, 0.15)" strokeDasharray="4 4" />
          <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }} tickLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111827',
              borderColor: 'rgba(148, 163, 184, 0.2)',
              borderRadius: 10,
              color: '#e2e8f0',
            }}
            formatter={(value) => [`${value}`, 'Skin Health Score']}
          />
          <Line
            type="monotone"
            dataKey="skin_health_score"
            stroke="#22c55e"
            strokeWidth={3}
            dot={{ r: 4, fill: '#22c55e' }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
