import { useMemo, useState } from 'react';
import {
  Award,
  ChartPie,
  Database,
  RefreshCw,
  TriangleAlert,
  Users,
  WalletCards,
} from 'lucide-react';
import { SupplierDetailsPanel } from '../components/suppliers/SupplierDetailsPanel';
import { SupplierFiltersBar } from '../components/suppliers/SupplierFiltersBar';
import { SupplierRankingTable } from '../components/suppliers/SupplierRankingTable';
import { Card } from '../components/ui/Card';
import { DonutChart, HorizontalBars } from '../components/ui/Charts';
import { MetricCard } from '../components/ui/MetricCard';
import { useSupplierDetails, useSuppliers } from '../hooks/useSuppliers';
import type { RankedSupplier, SupplierFilters } from '../types/suppliers';
import { formatCompactCurrency } from '../utils/format';

const defaultFilters: SupplierFilters = {
  year: null,
  quarter: null,
  limit: 10,
};

const chartColors = ['#2379d8', '#24aa72', '#f1af14', '#7968cc', '#ef714f', '#c8ccd4'];

export function SuppliersPage() {
  const [filters, setFilters] = useState(defaultFilters);
  const [search, setSearch] = useState('');
  const [reloadVersion, setReloadVersion] = useState(0);
  const [selectedCode, setSelectedCode] = useState<string | number | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const { data, error, isLoading } = useSuppliers(filters, reloadVersion);

  const defaultSupplierCode = data?.ranking.find((supplier) => supplier.supplier_code !== null)?.supplier_code ?? null;
  const activeSupplierCode = isPanelOpen ? selectedCode ?? defaultSupplierCode : null;
  const supplierDetails = useSupplierDetails(activeSupplierCode);

  const visibleSuppliers = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase();
    if (!normalizedSearch) return data?.ranking ?? [];

    return (data?.ranking ?? []).filter((supplier) =>
      supplier.supplier_name.toLocaleLowerCase().includes(normalizedSearch),
    );
  }, [data?.ranking, search]);

  const categoryTotal = data?.categories.reduce((sum, category) => sum + category.total_spending, 0) ?? 0;
  const categories = (data?.categories ?? []).map((category, index) => ({
    name: category.category,
    spend: category.total_spending,
    percent: categoryTotal ? (category.total_spending / categoryTotal) * 100 : 0,
    color: chartColors[index % chartColors.length],
  }));

  const selectSupplier = (supplier: RankedSupplier) => {
    if (supplier.supplier_code === null) return;
    setSelectedCode(supplier.supplier_code);
    setIsPanelOpen(true);
  };

  return (
    <div className="mx-auto max-w-[1650px] space-y-3">
      <Card className="p-4">
        <SupplierFiltersBar
          filters={filters}
          search={search}
          onFiltersChange={(nextFilters) => {
            setFilters(nextFilters);
            setSelectedCode(null);
          }}
          onSearchChange={setSearch}
          onRefresh={() => setReloadVersion((version) => version + 1)}
          onClear={() => {
            setFilters(defaultFilters);
            setSearch('');
            setSelectedCode(null);
          }}
        />
      </Card>

      {isLoading && <LoadingBanner />}
      {error && <ErrorBanner message={error} onRetry={() => setReloadVersion((version) => version + 1)} />}

      <div className={`grid gap-3 ${activeSupplierCode !== null ? '2xl:grid-cols-[minmax(0,1fr)_350px]' : ''}`}>
        <main className="min-w-0 space-y-3">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Active Suppliers"
              value={data ? data.count.active_suppliers.toLocaleString() : '—'}
              helper={periodLabel(filters)}
              icon={Users}
            />
            <MetricCard
              label="Top Supplier"
              value={<span className="text-[16px]">{data?.topSupplier?.supplier_name ?? '—'}</span>}
              helper={data?.topSupplier ? formatCompactCurrency(data.topSupplier.total_procurement_value) : undefined}
              icon={Award}
              color="violet"
            />
            <MetricCard
              label="Total Procurement Value"
              value={data ? formatCompactCurrency(data.totalValue.total_procurement_value) : '—'}
              helper={periodLabel(filters)}
              icon={Database}
              color="amber"
            />
            <MetricCard
              label="Average Supplier Spend"
              value={data ? formatCompactCurrency(data.averageSpend.average_supplier_spend) : '—'}
              helper={data ? `Across ${data.averageSpend.supplier_count.toLocaleString()} suppliers` : undefined}
              icon={WalletCards}
              color="blue"
            />
          </div>

          <div className="grid gap-3 xl:grid-cols-[1.05fr_.95fr]">
            <Card title="Top Suppliers by Spend" info>
              <SupplierRankingTable
                suppliers={visibleSuppliers}
                totalValue={data?.totalValue.total_procurement_value ?? 0}
                selectedCode={activeSupplierCode}
                colors={chartColors}
                onSelect={selectSupplier}
              />
            </Card>

            <Card title="Spend by Supplier (USD)" info>
              {visibleSuppliers.length > 0 ? (
                <HorizontalBars
                  compact
                  items={visibleSuppliers.map((supplier, index) => ({
                    name: supplier.supplier_name,
                    value: supplier.total_procurement_value,
                    label: formatCompactCurrency(supplier.total_procurement_value).replace('USD ', ''),
                    color: chartColors[index % chartColors.length],
                  }))}
                />
              ) : <EmptyState message="No suppliers match this search." />}
              <div className="mt-4 text-center text-[10px] text-slate-500">Procurement value (USD)</div>
            </Card>
          </div>

          <div className="grid gap-3 xl:grid-cols-[1.1fr_.9fr]">
            <Card title="Spend by Commodity Category" info>
              {categories.length > 0 ? (
                <div className="flex flex-col items-center gap-5 lg:flex-row">
                  <DonutChart
                    departments={categories}
                    centerLabel="Total Spend"
                    centerValue={formatCompactCurrency(categoryTotal)}
                  />
                  <div className="w-full min-w-0 flex-1 space-y-3">
                    {categories.map((category) => (
                      <div key={category.name} className="grid grid-cols-[9px_minmax(0,1fr)_auto] items-center gap-2 text-[10px] text-slate-600">
                        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: category.color }} />
                        <span className="truncate" title={category.name}>{category.name}</span>
                        <span>{formatCompactCurrency(category.spend)} ({category.percent.toFixed(1)}%)</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : <EmptyState message="No category spending is available for this period." />}
            </Card>

            <Card title="Supplier Concentration" info>
              {data ? (
                <div className="space-y-5">
                  <div className="rounded-xl bg-emerald-50 p-4">
                    <div className="text-[10px] font-semibold uppercase tracking-wide text-emerald-700">Supplier market</div>
                    <div className="mt-2 text-2xl font-bold text-slate-950">{data.concentration.supplier_count.toLocaleString()}</div>
                    <div className="mt-1 text-[10px] text-slate-600">Suppliers representing {formatCompactCurrency(data.concentration.total_procurement_value)}</div>
                  </div>
                  <ConcentrationBar label="Top supplier share" value={data.concentration.top_1_share} />
                  <ConcentrationBar label="Top 5 supplier share" value={data.concentration.top_5_share} />
                  <ConcentrationBar label="Top 10 supplier share" value={data.concentration.top_10_share} />
                </div>
              ) : <EmptyState message="Supplier concentration is loading." />}
            </Card>
          </div>
        </main>

        {activeSupplierCode !== null && (
          <SupplierDetailsPanel
            details={supplierDetails.details}
            error={supplierDetails.error}
            isLoading={supplierDetails.isLoading}
            onClose={() => setIsPanelOpen(false)}
          />
        )}
      </div>
    </div>
  );
}

function ConcentrationBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-[10px] text-slate-600">
        <span>{label}</span>
        <strong className="text-slate-800">{value.toFixed(2)}%</strong>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
        <div className="bar-grow h-full rounded-full bg-emerald" style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} />
      </div>
    </div>
  );
}

function LoadingBanner() {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-xs font-medium text-blue-700">
      <RefreshCw className="h-4 w-4 animate-spin" />
      Loading live supplier analytics from the procurement database…
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

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center text-center text-xs text-slate-400">
      <ChartPie className="mb-2 h-7 w-7" />
      {message}
    </div>
  );
}

function periodLabel(filters: SupplierFilters) {
  if (filters.year === null) return 'All available procurement data';
  if (filters.quarter === null) return `Calendar year ${filters.year}`;
  return `Q${filters.quarter} ${filters.year}`;
}
