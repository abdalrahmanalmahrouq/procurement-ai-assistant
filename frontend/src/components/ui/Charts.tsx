import type { Department, QuarterSpend } from '../../types/procurement';

export function LineAreaChart({ data }: { data: QuarterSpend[] }) {
  const width = 560;
  const height = 240;
  const left = 48;
  const right = 20;
  const top = 20;
  const bottom = 45;
  const max = 75;
  const x = (index: number) => left + index * ((width - left - right) / (data.length - 1));
  const y = (value: number) => top + (max - value) * ((height - top - bottom) / max);
  const points = data.map((item, index) => `${x(index)},${y(item.value)}`).join(' ');
  const area = `${left},${height - bottom} ${points} ${width - right},${height - bottom}`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-[240px] w-full" role="img" aria-label="Quarterly spending trend">
      <defs>
        <linearGradient id="quarter-fill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#0b9367" stopOpacity=".25" />
          <stop offset="100%" stopColor="#0b9367" stopOpacity=".02" />
        </linearGradient>
      </defs>
      {[0, 15, 30, 45, 60, 75].map((tick) => (
        <g key={tick}>
          <line x1={left} x2={width - right} y1={y(tick)} y2={y(tick)} stroke="#d9e2e8" strokeDasharray="3 4" />
          <text x="4" y={y(tick) + 4} fontSize="11" fill="#6b7890">{tick === 0 ? '0' : `${tick}M`}</text>
        </g>
      ))}
      <polygon points={area} fill="url(#quarter-fill)" />
      <polyline className="chart-line" points={points} fill="none" stroke="#07875f" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
      {data.map((item, index) => (
        <g key={item.label}>
          <circle cx={x(index)} cy={y(item.value)} r="5.5" fill="#07875f" stroke="white" strokeWidth="2" />
          <text x={x(index)} y={y(item.value) - 14} textAnchor="middle" fontSize="11" fontWeight="700" fill="#14213a">{item.value.toFixed(1)}M</text>
          <text x={x(index)} y={height - 20} textAnchor="middle" fontSize="11" fill="#5f6e84">{item.label.split('\n')[0]}</text>
          {item.label.includes('\n') && <text x={x(index)} y={height - 7} textAnchor="middle" fontSize="9" fill="#5f6e84">(YTD)</text>}
        </g>
      ))}
    </svg>
  );
}

interface BarItem { name: string; value: number; label?: string; color?: string }

export function HorizontalBars({ items, compact = false }: { items: BarItem[]; compact?: boolean }) {
  const max = Math.max(...items.map((item) => item.value), 1);
  return (
    <div className={compact ? 'space-y-2.5' : 'space-y-3'}>
      {items.map((item, index) => (
        <div key={item.name} className="grid grid-cols-[minmax(100px,1.15fr)_minmax(110px,2fr)_auto] items-center gap-3 text-[10px] sm:text-[11px]">
          <div className="flex min-w-0 items-center gap-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[8px] font-bold text-white" style={{ backgroundColor: item.color ?? '#1973d2' }}>{index + 1}</span>
            <span className="truncate text-slate-600">{item.name}</span>
          </div>
          <div className="h-3.5 overflow-hidden rounded-r-sm bg-slate-50">
            <div className="bar-grow h-full rounded-r-sm bg-gradient-to-r from-emerald to-emerald-400" style={{ width: `${Math.max(8, (item.value / max) * 100)}%` }} />
          </div>
          <span className="whitespace-nowrap text-slate-600">{item.label ?? item.value}</span>
        </div>
      ))}
    </div>
  );
}

export function DonutChart({ departments, centerLabel = 'Total Spend', centerValue = 'USD 24.68M' }: { departments: Department[]; centerLabel?: string; centerValue?: string }) {
  return (
    <div className="relative mx-auto h-52 w-52 shrink-0">
      <svg viewBox="0 0 42 42" className="h-full w-full -rotate-90" role="img" aria-label="Department spending breakdown">
        {departments.map((item, index) => {
          const currentOffset = departments.slice(0, index).reduce((sum, department) => sum + department.percent, 0);
          return (
            <circle
              key={item.name}
              cx="21" cy="21" r="15.9155" fill="transparent" stroke={item.color} strokeWidth="9"
              strokeDasharray={`${item.percent} ${100 - item.percent}`}
              strokeDashoffset={-currentOffset}
            />
          );
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-[10px] text-slate-500">{centerLabel}</span>
        <strong className="mt-1 text-sm text-slate-950">{centerValue}</strong>
      </div>
    </div>
  );
}
