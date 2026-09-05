import { useMemo, useState } from 'react';
import {
  Building2,
  Database,
  Landmark,
  ReceiptText,
  RefreshCw,
  TriangleAlert,
  Trophy,
} from 'lucide-react';
import { DepartmentFiltersBar } from '../components/departments/DepartmentFiltersBar';
import { DepartmentInsights } from '../components/departments/DepartmentInsights';
import { DepartmentRankingTable } from '../components/departments/DepartmentRankingTable';
import { Card } from '../components/ui/Card';
import { HorizontalBars } from '../components/ui/Charts';
import { MetricCard } from '../components/ui/MetricCard';
import { useDepartmentInsights, useDepartments } from '../hooks/useDepartments';
import type {
  DepartmentFilters,
  DepartmentTrendGranularity,
  RankedDepartment,
} from '../types/departments';
import { formatCompactCurrency } from '../utils/format';

const defaultFilters: DepartmentFilters = {
  year: null,
  quarter: null,
  limit: 10,
};

const chartColors = ['#07875f', '#31b987', '#2379d8', '#7968cc', '#f1af14', '#ef714f'];
const emptyRanking: RankedDepartment[] = [];

export function DepartmentsPage() {
  const [filters, setFilters] = useState(defaultFilters);
  const [search, setSearch] = useState('');
  const [reloadVersion, setReloadVersion] = useState(0);
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const [granularity, setGranularity] = useState<DepartmentTrendGranularity>('quarter');
  const { data, error, isLoading } = useDepartments(filters, reloadVersion);
  const ranking = data?.ranking ?? emptyRanking;

  const selectedDepartment = useMemo(() => {
    if (!ranking.length) return null;
    return ranking.find((department) => department.department_name === selectedName) ?? ranking[0];
  }, [ranking, selectedName]);

  const visibleDepartments = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase();
    if (!normalizedSearch) return ranking;

    return ranking.filter((department) =>
      department.department_name.toLocaleLowerCase().includes(normalizedSearch),
    );
  }, [ranking, search]);

  const insights = useDepartmentInsights(selectedDepartment?.department_name ?? null, granularity);

  const selectDepartment = (department: RankedDepartment) => {
    setSelectedName(department.department_name);
  };

  return (
    <div className="mx-auto max-w-[1650px] space-y-3">
      <Card className="p-4">
        <DepartmentFiltersBar
          filters={filters}
          search={search}
          onFiltersChange={(nextFilters) => {
            setFilters(nextFilters);
            setSelectedName(null);
          }}
          onSearchChange={setSearch}
          onRefresh={() => setReloadVersion((version) => version + 1)}
          onClear={() => {
            setFilters(defaultFilters);
            setSearch('');
            setSelectedName(null);
          }}
        />
      </Card>

      {isLoading && <LoadingBanner />}
      {error && <ErrorBanner message={error} onRetry={() => setReloadVersion((version) => version + 1)} />}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard
          label="Active Departments"
          value={data ? data.summary.department_count.toLocaleString() : '—'}
          helper={periodLabel(filters)}
          icon={Building2}
        />
        <MetricCard
          label="Total Procurement Value"
          value={data ? formatCompactCurrency(data.summary.total_procurement_value) : '—'}
          helper={periodLabel(filters)}
          icon={Database}
          color="amber"
        />
        <MetricCard
          label="Average Department Spend"
          value={data ? formatCompactCurrency(data.summary.average_department_spend) : '—'}
          helper="Per active department"
          icon={Landmark}
          color="blue"
        />
        <MetricCard
          label="Top Spending Department"
          value={<span className="text-[15px]">{data?.summary.top_spending_department?.department_name ?? '—'}</span>}
          helper={data?.summary.top_spending_department ? formatCompactCurrency(data.summary.top_spending_department.total_spending) : undefined}
          icon={Trophy}
          color="violet"
        />
        <MetricCard
          label="Most Orders"
          value={<span className="text-[15px]">{data?.summary.most_orders_department?.department_name ?? '—'}</span>}
          helper={data?.summary.most_orders_department ? `${data.summary.most_orders_department.unique_orders.toLocaleString()} orders` : undefined}
          icon={ReceiptText}
          color="teal"
        />
      </div>

      <div className="grid gap-3 xl:grid-cols-[1.08fr_.92fr]">
        <Card title="Department Ranking" info>
          <DepartmentRankingTable
            departments={visibleDepartments}
            totalValue={data?.summary.total_procurement_value ?? 0}
            selectedName={selectedDepartment?.department_name ?? null}
            onSelect={selectDepartment}
          />
        </Card>

        <Card title="Spend by Department (USD)" info>
          {visibleDepartments.length > 0 ? (
            <HorizontalBars
              compact
              items={visibleDepartments.map((department, index) => ({
                name: department.department_name,
                value: department.total_procurement_value,
                label: formatCompactCurrency(department.total_procurement_value).replace('USD ', ''),
                color: chartColors[index % chartColors.length],
              }))}
            />
          ) : <div className="flex min-h-48 items-center justify-center text-xs text-slate-400">No departments match this search.</div>}
          <div className="mt-4 text-center text-[10px] text-slate-500">Procurement value (USD)</div>
        </Card>
      </div>

      {selectedDepartment && (
        <DepartmentInsights
          department={selectedDepartment}
          data={insights.data}
          error={insights.error}
          isLoading={insights.isLoading}
          granularity={granularity}
          onGranularityChange={setGranularity}
        />
      )}
    </div>
  );
}

function LoadingBanner() {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-xs font-medium text-blue-700">
      <RefreshCw className="h-4 w-4 animate-spin" />
      Loading live department analytics from the procurement database…
    </div>
  );
}

function ErrorBanner({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-xs text-red-700">
      <TriangleAlert className="h-4 w-4" />
      <span className="flex-1">{message}</span>
      <button className="font-semibold" onClick={onRetry}>Try again</button>
    </div>
  );
}

function periodLabel(filters: DepartmentFilters) {
  if (filters.year === null) return 'All available procurement data';
  if (filters.quarter === null) return `Calendar year ${filters.year}`;
  return `Q${filters.quarter} ${filters.year}`;
}
