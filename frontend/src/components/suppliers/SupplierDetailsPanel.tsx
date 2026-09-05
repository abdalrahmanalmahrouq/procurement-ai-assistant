import { Building2, RefreshCw, X } from 'lucide-react';
import { MiniSparkline } from '../ui/MetricCard';
import type { SupplierDetails } from '../../types/suppliers';
import { formatCompactCurrency } from '../../utils/format';

interface SupplierDetailsPanelProps {
  details: SupplierDetails | null;
  error: string | null;
  isLoading: boolean;
  onClose: () => void;
}

export function SupplierDetailsPanel({ details, error, isLoading, onClose }: SupplierDetailsPanelProps) {
  const departmentTotal = details?.departments.reduce((sum, department) => sum + department.total_spending, 0) ?? 0;
  const categoryTotal = details?.top_categories.reduce((sum, category) => sum + category.total_spending, 0) ?? 0;

  return (
    <aside className="card self-start p-4 2xl:sticky 2xl:top-[92px]">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-bold">Selected Supplier</h3>
          <span className="text-[8px] text-slate-400">All-time supplier profile</span>
        </div>
        <button aria-label="Close supplier details" onClick={onClose}>
          <X className="h-4 w-4 text-slate-500" />
        </button>
      </div>

      {isLoading && (
        <div className="mt-5 flex items-center gap-2 rounded-lg bg-blue-50 p-3 text-xs text-blue-700">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Loading supplier details…
        </div>
      )}
      {error && <div className="mt-5 rounded-lg bg-red-50 p-3 text-xs text-red-700">{error}</div>}

      {details && (
        <>
          <div className="mt-5 flex items-center gap-3 border-b border-slate-100 pb-4">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-blue text-white">
              <Building2 className="h-6 w-6" />
            </span>
            <div className="min-w-0">
              <h4 className="truncate text-sm font-bold" title={details.supplier.supplier_name}>{details.supplier.supplier_name}</h4>
              <span className="mt-1 inline-block rounded-full bg-green-50 px-2 py-1 text-[9px] text-green-700">Active</span>
            </div>
          </div>

          <PanelSection title="Supplier Information">
            <DetailRows rows={[
              ['Supplier Code', String(details.supplier.supplier_code)],
              ['ZIP Code', String(details.supplier.supplier_zip_code ?? '—')],
              ['Qualifications', details.supplier.supplier_qualifications ?? '—'],
            ]} />
          </PanelSection>

          <PanelSection title="Procurement Summary">
            <div className="grid grid-cols-2 gap-2">
              <SummaryTile label="Orders" value={details.summary.unique_orders.toLocaleString()} />
              <SummaryTile label="Line Records" value={details.summary.line_records.toLocaleString()} />
              <SummaryTile label="Total Spend" value={formatCompactCurrency(details.summary.total_procurement_value)} />
              <SummaryTile label="Average Order" value={formatCompactCurrency(details.summary.average_order_value)} />
            </div>
          </PanelSection>

          <PanelSection title="Quarterly Spend Trend">
            {details.spend_trend.length > 0 ? (
              <>
                <MiniSparkline values={details.spend_trend.map((period) => period.total_spending)} />
                <div className="mt-2 flex justify-between text-[8px] text-slate-500">
                  <span>{trendLabel(details.spend_trend[0])}</span>
                  <span>{trendLabel(details.spend_trend.at(-1)!)}</span>
                </div>
              </>
            ) : <SmallEmptyState message="No spend trend is available." />}
          </PanelSection>

          <PanelSection title="Departments Served">
            <SpendBreakdown items={details.departments} total={departmentTotal} />
          </PanelSection>

          <PanelSection title="Top Purchased Categories" last>
            <SpendBreakdown items={details.top_categories} total={categoryTotal} />
          </PanelSection>
        </>
      )}
    </aside>
  );
}

function PanelSection({ title, last = false, children }: { title: string; last?: boolean; children: React.ReactNode }) {
  return (
    <section className={`${last ? '' : 'border-b border-slate-100'} py-4`}>
      <h4 className="mb-3 text-[11px] font-bold">{title}</h4>
      {children}
    </section>
  );
}

function SummaryTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-2.5">
      <div className="text-[8px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 truncate text-[11px] font-bold text-slate-800" title={value}>{value}</div>
    </div>
  );
}

function DetailRows({ rows }: { rows: string[][] }) {
  return (
    <div className="space-y-2.5">
      {rows.map(([label, value]) => (
        <div key={label} className="grid grid-cols-[100px_minmax(0,1fr)] gap-3 text-[10px]">
          <span className="text-slate-500">{label}</span>
          <span className="break-words text-right font-medium text-slate-700">{value}</span>
        </div>
      ))}
    </div>
  );
}

function SpendBreakdown({ items, total }: { items: Array<{ _id: string | null; total_spending: number }>; total: number }) {
  if (items.length === 0) return <SmallEmptyState message="No spending breakdown is available." />;

  return (
    <div className="space-y-3">
      {items.slice(0, 6).map((item, index) => {
        const percent = total ? (item.total_spending / total) * 100 : 0;
        return (
          <div key={`${item._id ?? 'Unknown'}-${index}`}>
            <div className="mb-1.5 flex items-center justify-between gap-3 text-[9px] text-slate-600">
              <span className="truncate" title={item._id ?? 'Unknown'}>{item._id ?? 'Unknown'}</span>
              <span className="shrink-0">{percent.toFixed(1)}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-emerald" style={{ width: `${Math.max(percent, 2)}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SmallEmptyState({ message }: { message: string }) {
  return <div className="py-4 text-center text-[9px] text-slate-400">{message}</div>;
}

function trendLabel(period: { _id: { year: number; quarter: number } }) {
  return `Q${period._id.quarter} ${period._id.year}`;
}
