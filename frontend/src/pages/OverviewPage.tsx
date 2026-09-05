import {
  Award,
  Building2,
  CalendarDays,
  LoaderCircle,
  PackageCheck,
  PackageSearch,
  RefreshCw,
  TriangleAlert,
  WalletCards,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { HorizontalBars } from '../components/ui/Charts';
import { MetricCard } from '../components/ui/MetricCard';
import { useDashboardData } from '../hooks/useDashboardData';
import { formatCompactCurrency, formatCompactNumber } from '../utils/format';

const chartColors = ['#1479dc', '#16a36f', '#f0a91a', '#7057c7', '#ef664c'];

export function OverviewPage() {
  const { data, highestQuarterOrderCount, isLoading, error, retry } = useDashboardData();

  if (isLoading) return <DashboardSkeleton />;
  if (error || !data) return <DashboardError message={error} onRetry={retry} />;

  const quarter = data.highest_spending_quarter;
  const topSupplier = data.top_suppliers[0];
  const topDepartment = data.top_departments[0];
  const topItem = data.top_items[0];

  const supplierBars = data.top_suppliers.map((supplier, index) => ({
    name: supplier.supplier_name,
    value: supplier.total_procurement_value,
    label: formatCompactCurrency(supplier.total_procurement_value),
    color: chartColors[index % chartColors.length],
  }));
  const departmentBars = data.top_departments.map((department, index) => ({
    name: department.department_name,
    value: department.total_spending,
    label: formatCompactCurrency(department.total_spending),
    color: chartColors[index % chartColors.length],
  }));
  const itemBars = data.top_items.map((item, index) => ({
    name: item.item_name,
    value: item.frequency,
    label: `${formatCompactNumber(item.frequency)} records`,
    color: chartColors[index % chartColors.length],
  }));

  return (
    <div className="mx-auto max-w-[1650px] space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold tracking-[-0.02em] text-slate-950">Procurement Overview</h2>
          <p className="mt-1 text-xs text-slate-500">Live analytics from the procurement database.</p>
        </div>
        <button className="soft-button" onClick={retry}>
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <MetricCard label="Average Order Value" value={formatCompactCurrency(data.average_order_value)} helper="Across all unique orders" icon={WalletCards} color="teal" />
        <MetricCard label="Highest-Spending Quarter" value={quarter ? `Q${quarter.quarter} ${quarter.year}` : 'No data'} helper={quarter ? formatCompactCurrency(quarter.total_spending) : undefined} icon={CalendarDays} color="green" />
        <MetricCard label="Orders in Highest Quarter" value={highestQuarterOrderCount === null ? 'Unavailable' : highestQuarterOrderCount.toLocaleString()} helper={quarter ? `Q${quarter.quarter} ${quarter.year}` : undefined} icon={PackageCheck} color="green" />
        <MetricCard label="Top Supplier" value={<span className="text-[17px]">{topSupplier?.supplier_name ?? 'No data'}</span>} helper={topSupplier ? formatCompactCurrency(topSupplier.total_procurement_value) : undefined} icon={Award} color="blue" />
        <MetricCard label="Top Department" value={<span className="text-[17px]">{topDepartment?.department_name ?? 'No data'}</span>} helper={topDepartment ? formatCompactCurrency(topDepartment.total_spending) : undefined} icon={Building2} color="violet" />
        <MetricCard label="Most Frequent Item" value={<span className="text-[17px]">{topItem?.item_name ?? 'No data'}</span>} helper={topItem ? `${topItem.frequency.toLocaleString()} records` : undefined} icon={PackageSearch} color="amber" />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <AnalyticsCard title="Top Suppliers by Procurement Value" items={supplierBars} valueLabel="Procurement value (USD)" />
        <AnalyticsCard title="Top Departments by Spending" items={departmentBars} valueLabel="Department spend (USD)" />
        <AnalyticsCard title="Most Frequent Items" items={itemBars} valueLabel="Matching records" />
      </div>
    </div>
  );
}

interface BarItem {
  name: string;
  value: number;
  label: string;
  color: string;
}

function AnalyticsCard({ title, items, valueLabel }: { title: string; items: BarItem[]; valueLabel: string }) {
  return (
    <Card title={title} info className="min-h-[360px]">
      {items.length ? (
        <>
          <div className="pt-2"><HorizontalBars items={items} /></div>
          <p className="mt-6 text-center text-[10px] text-slate-500">{valueLabel}</p>
        </>
      ) : (
        <div className="flex min-h-[250px] items-center justify-center text-xs text-slate-500">No data returned.</div>
      )}
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-[1650px] space-y-4" aria-label="Loading dashboard" aria-live="polite">
      <div className="flex items-center gap-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-blue-700 shadow-sm">
        <LoaderCircle className="h-5 w-5 shrink-0 animate-spin" />
        <div>
          <p className="text-sm font-semibold">Loading procurement dashboard</p>
          <p className="mt-0.5 text-[11px] text-blue-600">Fetching the latest analytics from the procurement database…</p>
        </div>
      </div>
      <div className="animate-pulse space-y-4">
        <div className="h-12 w-72 rounded-lg bg-slate-200" />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
          {Array.from({ length: 6 }, (_, index) => <div key={index} className="h-[126px] rounded-xl bg-slate-200" />)}
        </div>
        <div className="grid gap-4 xl:grid-cols-3">
          {Array.from({ length: 3 }, (_, index) => <div key={index} className="h-[360px] rounded-xl bg-slate-200" />)}
        </div>
      </div>
    </div>
  );
}

function DashboardError({ message, onRetry }: { message: string | null; onRetry: () => void }) {
  return (
    <div className="card mx-auto flex min-h-[480px] max-w-2xl flex-col items-center justify-center p-8 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-full bg-red-50 text-red-500"><TriangleAlert className="h-7 w-7" /></span>
      <h2 className="mt-4 text-lg font-bold text-slate-950">Couldn’t load dashboard data</h2>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{message ?? 'The procurement API did not return dashboard data.'}</p>
      <button className="primary-button mt-5" onClick={onRetry}><RefreshCw className="h-4 w-4" />Try again</button>
    </div>
  );
}
