import { useId } from 'react';
import { BarChart3, Gauge } from 'lucide-react';
import type { ValueFormat, Visualization as VisualizationData } from '../../types/chat';

const colors = ['#07875f', '#1973d2', '#7c3aed', '#e59a18', '#dc5a5a', '#0e9eae'];

function formatValue(value: number, format: ValueFormat, compact = false): string {
  if (format === 'currency') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      notation: compact ? 'compact' : 'standard',
      maximumFractionDigits: compact ? 1 : 2,
    }).format(value);
  }
  if (format === 'percent') return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)}%`;
  return new Intl.NumberFormat('en-US', {
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: 1,
  }).format(value);
}

function BarVisualization({ visualization }: { visualization: VisualizationData }) {
  const max = Math.max(...visualization.data.map((item) => Math.abs(item.value)), 1);

  return (
    <div className="space-y-3.5" role="img" aria-label={visualization.title}>
      {visualization.data.map((item, index) => (
        <div key={`${item.label}-${index}`} className="grid grid-cols-[minmax(90px,1fr)_minmax(120px,2.5fr)_auto] items-center gap-3 text-xs">
          <span className="truncate font-medium text-slate-600" title={item.label}>{item.label}</span>
          <div className="h-5 overflow-hidden rounded-md bg-slate-100">
            <div
              className="bar-grow h-full rounded-md bg-gradient-to-r from-emerald to-emerald-400"
              style={{ width: `${Math.max(3, (Math.abs(item.value) / max) * 100)}%` }}
            />
          </div>
          <strong className="whitespace-nowrap text-[11px] font-semibold text-slate-700">
            {formatValue(item.value, visualization.value_format, true)}
          </strong>
        </div>
      ))}
    </div>
  );
}

function TrendVisualization({ visualization }: { visualization: VisualizationData }) {
  const width = 640;
  const height = 250;
  const padding = { top: 22, right: 18, bottom: 50, left: 62 };
  const values = visualization.data.map((item) => item.value);
  const minValue = Math.min(...values, 0);
  const maxValue = Math.max(...values, 1);
  const span = maxValue - minValue || 1;
  const x = (index: number) => padding.left + index * ((width - padding.left - padding.right) / Math.max(visualization.data.length - 1, 1));
  const y = (value: number) => padding.top + (maxValue - value) * ((height - padding.top - padding.bottom) / span);
  const points = visualization.data.map((item, index) => `${x(index)},${y(item.value)}`).join(' ');
  const baseline = height - padding.bottom;
  const area = `${padding.left},${baseline} ${points} ${x(visualization.data.length - 1)},${baseline}`;
  const labelEvery = Math.max(1, Math.ceil(visualization.data.length / 6));

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full min-w-[480px]" role="img" aria-label={visualization.title}>
      <defs>
        <linearGradient id="assistant-chart-fill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#07875f" stopOpacity=".28" />
          <stop offset="100%" stopColor="#07875f" stopOpacity=".02" />
        </linearGradient>
      </defs>
      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
        const value = minValue + span * ratio;
        return (
          <g key={ratio}>
            <line x1={padding.left} x2={width - padding.right} y1={y(value)} y2={y(value)} stroke="#d9e2e8" strokeDasharray="3 5" />
            <text x={padding.left - 8} y={y(value) + 4} textAnchor="end" fontSize="10" fill="#6b7890">{formatValue(value, visualization.value_format, true)}</text>
          </g>
        );
      })}
      {visualization.type === 'area' && <polygon points={area} fill="url(#assistant-chart-fill)" />}
      <polyline className="chart-line" points={points} fill="none" stroke="#07875f" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
      {visualization.data.map((item, index) => (
        <g key={`${item.label}-${index}`}>
          <circle cx={x(index)} cy={y(item.value)} r="5" fill="#07875f" stroke="white" strokeWidth="2"><title>{`${item.label}: ${formatValue(item.value, visualization.value_format)}`}</title></circle>
          {(index % labelEvery === 0 || index === visualization.data.length - 1) && (
            <text x={x(index)} y={height - 25} textAnchor="middle" fontSize="10" fill="#5f6e84">{item.label.slice(0, 14)}</text>
          )}
        </g>
      ))}
      {visualization.x_axis_label && <text x={(padding.left + width - padding.right) / 2} y={height - 4} textAnchor="middle" fontSize="10" fontWeight="600" fill="#5f6e84">{visualization.x_axis_label}</text>}
    </svg>
  );
}

function PieVisualization({ visualization }: { visualization: VisualizationData }) {
  const positiveData = visualization.data.filter((item) => item.value > 0);
  const total = positiveData.reduce((sum, item) => sum + item.value, 0);
  if (total === 0) {
    return <p className="text-sm text-slate-500">There are no positive values to chart.</p>;
  }

  return (
    <div className="grid items-center gap-6 sm:grid-cols-[210px_1fr]">
      <div className="relative mx-auto h-48 w-48">
        <svg viewBox="0 0 42 42" className="h-full w-full -rotate-90" role="img" aria-label={visualization.title}>
          {positiveData.map((item, index) => {
            const percent = (item.value / total) * 100;
            const currentOffset = positiveData
              .slice(0, index)
              .reduce((sum, previous) => sum + (previous.value / total) * 100, 0);
            return (
              <circle
                key={`${item.label}-${index}`}
                cx="21" cy="21" r="15.9155" fill="transparent" stroke={colors[index % colors.length]}
                strokeWidth={visualization.type === 'donut' ? 7 : 12}
                strokeDasharray={`${percent} ${100 - percent}`} strokeDashoffset={-currentOffset}
              ><title>{`${item.label}: ${formatValue(item.value, visualization.value_format)}`}</title></circle>
            );
          })}
        </svg>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-[10px] text-slate-500">Total</span>
          <strong className="mt-1 text-sm text-slate-900">{formatValue(total, visualization.value_format, true)}</strong>
        </div>
      </div>
      <div className="space-y-2.5">
        {positiveData.map((item, index) => (
          <div key={`${item.label}-${index}`} className="flex items-center gap-2 text-xs">
            <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: colors[index % colors.length] }} />
            <span className="min-w-0 flex-1 truncate text-slate-600">{item.label}</span>
            <strong className="font-semibold text-slate-800">{formatValue(item.value, visualization.value_format, true)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function MetricVisualization({ visualization }: { visualization: VisualizationData }) {
  const item = visualization.data[0];
  return (
    <div className="flex items-center gap-4 rounded-xl bg-gradient-to-br from-emerald-50 to-blue-50 p-5">
      <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white text-emerald shadow-sm"><Gauge className="h-6 w-6" /></span>
      <div>
        <p className="text-xs font-medium text-slate-500">{item.label}</p>
        <p className="mt-1 text-3xl font-bold tracking-tight text-slate-950">{formatValue(item.value, visualization.value_format)}</p>
      </div>
    </div>
  );
}

export function Visualization({ visualization }: { visualization: VisualizationData }) {
  const titleId = useId();
  if (visualization.data.length === 0) return null;

  return (
    <section className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-slate-50/40" aria-labelledby={titleId}>
      <header className="flex items-start gap-3 border-b border-slate-200 bg-white px-4 py-3.5">
        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald"><BarChart3 className="h-4 w-4" /></span>
        <div>
          <h4 id={titleId} className="text-sm font-semibold text-slate-900">{visualization.title}</h4>
          {visualization.subtitle && <p className="mt-0.5 text-xs text-slate-500">{visualization.subtitle}</p>}
        </div>
      </header>
      <div className="overflow-x-auto p-4 sm:p-5">
        {visualization.type === 'bar' && <BarVisualization visualization={visualization} />}
        {(visualization.type === 'line' || visualization.type === 'area') && <TrendVisualization visualization={visualization} />}
        {(visualization.type === 'pie' || visualization.type === 'donut') && <PieVisualization visualization={visualization} />}
        {visualization.type === 'metric' && <MetricVisualization visualization={visualization} />}
      </div>
    </section>
  );
}
