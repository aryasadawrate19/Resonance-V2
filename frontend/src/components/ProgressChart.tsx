import { useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import type { HistoryEntry } from '../types';

Chart.register(...registerables);

interface Props {
  history: HistoryEntry[];
}

export default function ProgressChart({ history }: Props) {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current || history.length === 0) return;

    // Destroy previous instance
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const labels = history.map((entry) => {
      const d = new Date(entry.timestamp);
      return `${d.getMonth() + 1}/${d.getDate()}`;
    });

    const scores = history.map((e) => e.skin_health_score);
    const lesions = history.map((e) => e.lesion_count);

    chartInstance.current = new Chart(chartRef.current, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Skin Health Score',
            data: scores,
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34, 197, 94, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 6,
            pointBackgroundColor: '#22c55e',
            pointBorderColor: '#0a0e17',
            pointBorderWidth: 2,
            borderWidth: 2,
          },
          {
            label: 'Lesion Count',
            data: lesions,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 5,
            pointBackgroundColor: '#ef4444',
            pointBorderColor: '#0a0e17',
            pointBorderWidth: 2,
            borderWidth: 2,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: {
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } },
          },
          tooltip: {
            backgroundColor: '#1a2332',
            titleColor: '#f1f5f9',
            bodyColor: '#94a3b8',
            borderColor: 'rgba(148, 163, 184, 0.2)',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8,
          },
        },
        scales: {
          x: {
            ticks: { color: '#64748b', font: { size: 11 } },
            grid: { color: 'rgba(148, 163, 184, 0.06)' },
          },
          y: {
            position: 'left',
            min: 0,
            max: 100,
            ticks: { color: '#22c55e', font: { size: 11 } },
            grid: { color: 'rgba(148, 163, 184, 0.06)' },
            title: { display: true, text: 'Score', color: '#64748b' },
          },
          y1: {
            position: 'right',
            min: 0,
            ticks: { color: '#ef4444', font: { size: 11 } },
            grid: { display: false },
            title: { display: true, text: 'Lesions', color: '#64748b' },
          },
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [history]);

  if (history.length === 0) {
    return (
      <div className="empty-state">
        <p>No scan history yet. Complete your first analysis to start tracking progress.</p>
      </div>
    );
  }

  return (
    <div style={{ height: 350 }}>
      <canvas ref={chartRef} id="progress-chart" />
    </div>
  );
}
