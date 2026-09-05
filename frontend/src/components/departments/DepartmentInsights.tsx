import { Building2, ChartPie, RefreshCw, TriangleAlert } from 'lucide-react';
import { Card } from '../ui/Card';
import { DonutChart, HorizontalBars } from '../ui/Charts';
import type {
  DepartmentInsightsData,
  DepartmentTrendGranularity,
  RankedDepartment,
} from '../../types/departments';
import { formatCompactCurrency } from '../../utils/format';

const colors = ['#07875f', '#31b987', '#2379d8', '#7968cc', '#f1af14', '#ef714f'];

interface DepartmentInsightsProps {
  department: RankedDepartment;
  data: DepartmentInsightsData | null;
  error: string | null;
  isLoading: boolean;
  granularity: DepartmentTrendGranularity;
  onGranularityChange: (granularity: DepartmentTrendGranularity) => void;
}

export function DepartmentInsights({
  department,
  data,
  error,
  isLoading,
  granularity,
  onGranularityChange,
}: DepartmentInsightsProps) {
  const acquisitionTotal = data?.acquisitionTypes.reduce((sum, type) => sum + type.total_spending, 0) ?? 0;
  const acquisitionTypes = (data?.acquisitionTypes ?? []).map((type, index) => ({
    name: type.acquisition_type,
    spend: type.total_spending,
    percent: acquisitionTotal ? (type.total_spending / acquisitionTotal) * 100 : 0,
    color: colors[index % colors.length],
  }));

  return (
    <section className="space-y-3">
      <div className="card flex flex-wrap items-center gap-4 p-4">
        <span className="icon-tile bg-blue-50 text-blue"><Building2 className="h-6 w-6" /></span>
        <div className="min-w-0 flex-1">
          <div className="text-[9px] font-semibold uppercase tracking-wide text-slate-400">Selected Department · All-time detail</div>
          <h2 className="mt-1 truncate text-base font-bold text-slate-900" title={department.department_name}>{department.department_name}</h2>
        </div>
        <Stat label="Procurement Value" value={formatCompactCurrency(department.total_procurement_value)} />
        <Stat label="Unique Orders" value={department.unique_orders.toLocaleString()} />
        <Stat label="Line Records" value={department.line_records.toLocaleString()} />
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-xs font-medium text-blue-700">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Loading live insights for {department.department_name}…
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-xs text-red-700">
          <TriangleAlert className="h-4 w-4" />{error}
        </div>
      )}

      <div className="grid gap-3 xl:grid-cols-2">
        <Card
          title="Department Spend Trend"
          info
          action={(
            <select
              aria-label="Spend trend granularity"
              className="soft-button h-8"
              value={granularity}
              onChange={(event) => onGranularityChange(event.target.value as DepartmentTrendGranularity)}
            >
              <option value="quarter">Quarterly</option>
              <option value="month">Monthly</option>
            </select>
          )}
        >
          {data?.spendTrend.length ? (
            <HorizontalBars
              compact
              items={data.spendTrend.slice(-12).map((period) => ({
                name: periodLabel(period._id),
                value: period.total_spending,
                label: formatCompactCurrency(period.total_spending).replace('USD ', ''),
              }))}
            />
          ) : <EmptyState message="No spend trend is available." />}
        </Card>

        <Card title="Spend by Acquisition Type" info>
          {acquisitionTypes.length ? (
            <div className="flex flex-col items-center gap-5 sm:flex-row">
              <DonutChart departments={acquisitionTypes} centerValue={formatCompactCurrency(acquisitionTotal)} />
              <div className="w-full min-w-0 flex-1 space-y-3">
                {acquisitionTypes.map((type) => (
                  <div key={type.name} className="grid grid-cols-[9px_minmax(0,1fr)_auto] items-center gap-2 text-[10px] text-slate-600">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: type.color }} />
                    <span className="truncate">{type.name}</span>
                    <span>{type.percent.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          ) : <EmptyState message="No acquisition-type data is available." />}
        </Card>

        <Card title="Top Suppliers for Department" info>
          {data?.topSuppliers.length ? (
            <HorizontalBars
              compact
              items={data.topSuppliers.map((supplier, index) => ({
                name: supplier.supplier_name,
                value: supplier.total_spending,
                label: formatCompactCurrency(supplier.total_spending).replace('USD ', ''),
                color: colors[index % colors.length],
              }))}
            />
          ) : <EmptyState message="No supplier data is available." />}
        </Card>

        <Card title="Top Commodity Categories" info>
          {data?.categories.length ? (
            <div className="space-y-3">
              {data.categories.map((category, index) => (
                <div key={category.category} className="grid grid-cols-[24px_minmax(0,1fr)_auto] items-center gap-3 text-[10px]">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 font-bold text-slate-600">{index + 1}</span>
                  <div className="min-w-0">
                    <div className="truncate font-medium text-slate-700" title={category.category}>{category.category}</div>
                    <div className="mt-0.5 text-[9px] text-slate-400">{category.unique_orders.toLocaleString()} orders</div>
                  </div>
                  <span className="font-medium text-slate-700">{formatCompactCurrency(category.total_spending)}</span>
                </div>
              ))}
            </div>
          ) : <EmptyState message="No category data is available." />}
        </Card>
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-[110px] rounded-lg bg-slate-50 px-3 py-2">
      <div className="text-[8px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1 text-xs font-bold text-slate-800">{value}</div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center text-center text-xs text-slate-400">
      <ChartPie className="mb-2 h-7 w-7" />
      {message}
    </div>
  );
}

function periodLabel(period: { year: number; month?: number; quarter?: number }) {
  if (period.month) return `${period.year}-${String(period.month).padStart(2, '0')}`;
  if (period.quarter) return `Q${period.quarter} ${period.year}`;
  return String(period.year);
}
