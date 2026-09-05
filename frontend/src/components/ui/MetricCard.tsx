import type { LucideIcon } from 'lucide-react';
import { ArrowDown, ArrowUp, Info } from 'lucide-react';
import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: ReactNode;
  helper?: string;
  trend?: number;
  icon: LucideIcon;
  color?: 'green' | 'blue' | 'teal' | 'amber' | 'violet';
  className?: string;
  sparkline?: number[];
}

const tileColors = {
  green: 'bg-green-50 text-green-700',
  blue: 'bg-blue-50 text-blue-700',
  teal: 'bg-teal-50 text-teal-700',
  amber: 'bg-amber-50 text-amber-600',
  violet: 'bg-violet-50 text-violet-700',
};

export function MetricCard({ label, value, helper, trend, icon: Icon, color = 'green', className = '', sparkline }: MetricCardProps) {
  return (
    <article className={`card min-h-[126px] p-4 ${className}`}>
      <div className="flex h-full gap-4">
        <div className={`icon-tile ${tileColors[color]}`}><Icon className="h-6 w-6" strokeWidth={1.8} /></div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-600">
            {label}<Info className="h-3 w-3 text-slate-400" />
          </div>
          <div className="mt-2 truncate text-[22px] font-bold leading-none tracking-[-0.025em] text-slate-950">{value}</div>
          {(trend !== undefined || helper) && (
            <div className="mt-3 flex items-center gap-1 text-[10px] text-slate-500">
              {trend !== undefined && (
                <span className={`inline-flex items-center font-semibold ${trend >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                  {trend >= 0 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}{Math.abs(trend)}%
                </span>
              )}
              {helper}
            </div>
          )}
          {sparkline && <MiniSparkline values={sparkline} />}
        </div>
      </div>
    </article>
  );
}

export function MiniSparkline({ values, color = '#0b9c6d' }: { values: number[]; color?: string }) {
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const points = values.map((value, index) => `${(index / (values.length - 1)) * 100},${28 - ((value - min) / range) * 24}`).join(' ');
  return (
    <svg viewBox="0 0 100 32" className="mt-2 h-8 w-full overflow-visible" preserveAspectRatio="none" aria-hidden="true">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
