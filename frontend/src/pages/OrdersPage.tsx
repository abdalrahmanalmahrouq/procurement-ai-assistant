import { useState } from 'react';
import {
  ArrowDownToLine,
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  CircleDollarSign,
  FileStack,
  Filter,
  RefreshCw,
  Search,
  ShoppingCart,
  TriangleAlert,
  WalletCards,
  X,
} from 'lucide-react';
import { DonutChart, HorizontalBars } from '../components/ui/Charts';
import { Card } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { useOrderDetail, useOrders, useSupplierSuggestions } from '../hooks/useOrders';
import type { OrderDetail, OrderListItem, OrdersQuery } from '../types/orders';
import { formatCompactCurrency, formatCurrency } from '../utils/format';

const defaultQuery: OrdersQuery = {
  page: 1,
  pageSize: 20,
  year: null,
  quarter: null,
  fiscalYear: '',
  department: '',
  supplier: '',
  acquisitionType: '',
  acquisitionMethod: '',
  minValue: null,
  maxValue: null,
  search: '',
  sortBy: 'creation_date',
  sortDirection: 'desc',
};

const chartColors = ['#21ad70', '#4fbd8d', '#4c9edf', '#f1b938', '#8f97a8', '#7c68c9'];

export function OrdersPage() {
  const [query, setQuery] = useState<OrdersQuery>(defaultQuery);
  const [reloadVersion, setReloadVersion] = useState(0);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const { orders, analytics, filters, isLoadingOrders, isLoadingAnalytics, isLoadingFilters, error } = useOrders(query, reloadVersion);
  const supplierSuggestions = useSupplierSuggestions(query.supplier);
  const selectedOrder = orders?.orders.find((order) => order.order_key === selectedKey) ?? null;
  const orderDetail = useOrderDetail(selectedKey);

  const updateFilter = <Key extends keyof OrdersQuery>(key: Key, value: OrdersQuery[Key]) => {
    setQuery((current) => ({ ...current, [key]: value, page: 1 }));
    setSelectedKey(null);
    setChecked(new Set());
  };

  const clearFilters = () => {
    setQuery(defaultQuery);
    setSelectedKey(null);
    setChecked(new Set());
  };

  const toggleRow = (orderKey: string) => {
    setChecked((current) => {
      const next = new Set(current);
      if (next.has(orderKey)) next.delete(orderKey); else next.add(orderKey);
      return next;
    });
  };

  const currentIds = orders?.orders.map((order) => order.order_key) ?? [];
  const acquisitionTotal = analytics?.acquisitionTypes.reduce((sum, item) => sum + item.unique_orders, 0) ?? 0;
  const acquisitionTypes = (analytics?.acquisitionTypes ?? []).map((item, index) => ({
    name: item._id,
    percent: acquisitionTotal ? Number(((item.unique_orders / acquisitionTotal) * 100).toFixed(1)) : 0,
    spend: item.total_procurement_value,
    color: chartColors[index % chartColors.length],
  }));
  const activeFilterCount = [query.fiscalYear, query.department, query.supplier, query.acquisitionType, query.acquisitionMethod, query.search.trim()].filter(Boolean).length;

  return (
    <div className="mx-auto max-w-[1650px]">
      <section className="card overflow-hidden">
        <div className="border-b border-slate-200 p-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-[22px] font-bold tracking-[-0.02em] text-slate-950">Orders &amp; Records</h2>
              <p className="mt-1 text-xs text-slate-500">Live purchase-order records and analytics from the procurement database.</p>
            </div>
            <div className="flex gap-2">
              <button className="soft-button" onClick={() => exportOrders(orders?.orders ?? [])} disabled={!orders?.orders.length}><ArrowDownToLine className="h-4 w-4" />Export current page</button>
              <button className="soft-button" onClick={() => setReloadVersion((version) => version + 1)}><RefreshCw className="h-4 w-4" />Refresh</button>
            </div>
          </div>

          
        </div>

        {(isLoadingOrders || isLoadingAnalytics) && <div className="flex items-center gap-2 border-b border-blue-100 bg-blue-50 px-4 py-2.5 text-xs font-medium text-blue-700"><RefreshCw className="h-4 w-4 animate-spin" />Loading live order data…</div>}
        {error && <ErrorBanner message={error} onRetry={() => setReloadVersion((version) => version + 1)} />}

        <div className={`grid ${selectedKey ? '2xl:grid-cols-[1fr_350px]' : ''}`}>
          <div className="min-w-0 space-y-4 p-4">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              <MetricCard label="Total Line Records" value={analytics ? analytics.summary.total_line_records.toLocaleString() : '—'} helper="Procurement data rows" icon={FileStack} />
              <MetricCard label="Unique Orders" value={analytics ? analytics.summary.total_orders.toLocaleString() : '—'} helper="Grouped by order key" icon={ShoppingCart} color="teal" />
              <MetricCard label="Total Procurement Value" value={analytics ? formatCompactCurrency(analytics.summary.total_procurement_value) : '—'} helper="Across all orders" icon={CircleDollarSign} color="green" />
              <MetricCard label="Average Order Value" value={analytics ? formatCompactCurrency(analytics.summary.average_order_value) : '—'} helper="Per unique order" icon={WalletCards} color="blue" />
              <div className="card min-h-[126px] p-3"><div className="mb-1 text-[10px] font-semibold text-slate-700">Orders by Acquisition Type</div>{acquisitionTypes.length ? <div className="flex items-center gap-1"><div className="-m-9 scale-[.55]"><DonutChart departments={acquisitionTypes} centerLabel="" centerValue={acquisitionTotal.toLocaleString()} /></div><div className="flex-1 space-y-1">{acquisitionTypes.slice(0, 5).map((item) => <div key={item.name} className="grid grid-cols-[7px_1fr_auto] gap-1 text-[8px] text-slate-600"><span className="mt-0.5 h-1.5 w-1.5 rounded-full" style={{ background: item.color }} /><span className="truncate">{item.name}</span><span>{item.percent}%</span></div>)}</div></div> : <div className="flex h-20 items-center justify-center text-[10px] text-slate-400">No analytics data</div>}</div>
            </div>

            {analytics && <div className="grid gap-3 xl:grid-cols-2">
              <Card title="Spend Over Time" info><HorizontalBars compact items={analytics.spendOverTime.slice(-12).map((point, index) => ({ name: periodLabel(point._id), value: point.total_spending, label: formatCompactCurrency(point.total_spending), color: chartColors[index % chartColors.length] }))} /></Card>
              <Card title="Order Value Distribution" info><HorizontalBars compact items={sortValueBuckets(analytics.valueDistribution).map((bucket, index) => ({ name: bucket._id, value: bucket.orders, label: `${bucket.orders.toLocaleString()} orders`, color: chartColors[index % chartColors.length] }))} /></Card>
            </div>}

            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-[.85fr_1.1fr_1.1fr_1fr_1fr_1.5fr_auto_auto]">
            <SelectFilter label="Fiscal Year" value={query.fiscalYear} onChange={(value) => updateFilter('fiscalYear', value)} disabled={isLoadingFilters}>
              <option value="">All fiscal years</option>{filters.fiscal_years.filter(Boolean).map((year) => <option key={year}>{year}</option>)}
            </SelectFilter>
            <SelectFilter label="Department" value={query.department} onChange={(value) => updateFilter('department', value)} disabled={isLoadingFilters}>
              <option value="">All departments</option>{filters.departments.map((department) => <option key={department}>{department}</option>)}
            </SelectFilter>
            <label className="min-w-0"><span className="field-label">Supplier</span><span className="form-field"><input list="supplier-options" value={query.supplier} onChange={(event) => updateFilter('supplier', event.target.value)} className="min-w-0 flex-1 outline-none" placeholder="Search supplier" /><datalist id="supplier-options">{supplierSuggestions.map((supplier) => <option key={supplier} value={supplier} />)}</datalist></span></label>
            <SelectFilter label="Acquisition Type" value={query.acquisitionType} onChange={(value) => updateFilter('acquisitionType', value)} disabled={isLoadingFilters}>
              <option value="">All types</option>{filters.acquisition_types.map((type) => <option key={type}>{type}</option>)}
            </SelectFilter>
            <SelectFilter label="Method" value={query.acquisitionMethod} onChange={(value) => updateFilter('acquisitionMethod', value)} disabled={isLoadingFilters}>
              <option value="">All methods</option>{filters.acquisition_methods.map((method) => <option key={method}>{method}</option>)}
            </SelectFilter>
            <label><span className="field-label opacity-0">Search</span><span className="form-field"><Search className="h-4 w-4 text-slate-400" /><input value={query.search} onChange={(event) => updateFilter('search', event.target.value)} className="min-w-0 flex-1 outline-none" placeholder="Search orders, items, suppliers..." /></span></label>
            <div className="primary-button mt-auto bg-emerald-50 text-emerald hover:bg-emerald-50"><Filter className="h-4 w-4" />Filters<span className="rounded-full bg-emerald px-1.5 py-0.5 text-[9px] text-white">{activeFilterCount}</span></div>
            <button onClick={clearFilters} className="mt-auto h-9 whitespace-nowrap text-xs font-medium text-slate-600">Clear all</button>
          </div>

            <div>
              <div className="flex flex-wrap items-center gap-3 rounded-t-xl border border-slate-200 bg-white px-4 py-3 text-[11px]"><button className={`flex h-4 w-4 items-center justify-center rounded border ${checked.size ? 'border-emerald bg-emerald text-white' : 'border-slate-300'}`} onClick={() => setChecked(currentIds.length && currentIds.every((id) => checked.has(id)) ? new Set() : new Set(currentIds))}>{checked.size > 0 && <Check className="h-3 w-3" />}</button><strong>{checked.size} row{checked.size === 1 ? '' : 's'} selected</strong><span className="text-slate-500">{orders?.total_orders.toLocaleString() ?? '0'} orders found</span><div className="ml-auto text-[10px] text-slate-500">Click a row to view its line-item details</div></div>
              <div className="overflow-x-auto border-x border-b border-slate-200 bg-white">
                <table className="w-full min-w-[1050px] text-left text-[10px]"><thead className="bg-slate-50 text-slate-600"><tr><th className="border-b border-slate-200 px-3 py-3" /><th className="border-b border-slate-200 px-3 py-3 font-semibold">Order Number</th><th className="border-b border-slate-200 px-3 py-3 font-semibold"><SortButton field="creation_date" label="Creation Date" query={query} setQuery={setQuery} /></th><th className="border-b border-slate-200 px-3 py-3 font-semibold">Supplier</th><th className="border-b border-slate-200 px-3 py-3 font-semibold">Department</th><th className="border-b border-slate-200 px-3 py-3 font-semibold">Acquisition Type</th><th className="border-b border-slate-200 px-3 py-3 font-semibold">Items</th><th className="border-b border-slate-200 px-3 py-3 font-semibold"><SortButton field="total_value" label="Total Value" query={query} setQuery={setQuery} /></th><th className="border-b border-slate-200 px-3 py-3 font-semibold"><SortButton field="line_count" label="Lines" query={query} setQuery={setQuery} /></th><th className="border-b border-slate-200 px-3 py-3 font-semibold">Actions</th></tr></thead>
                  <tbody>{orders?.orders.map((order) => <tr key={order.order_key} onClick={() => setSelectedKey(order.order_key)} className={`${selectedKey === order.order_key ? 'bg-emerald-50/60' : 'hover:bg-slate-50'} cursor-pointer text-slate-700`}><td className="border-b border-slate-100 px-3 py-3"><button onClick={(event) => { event.stopPropagation(); toggleRow(order.order_key); }} className={`flex h-4 w-4 items-center justify-center rounded border ${checked.has(order.order_key) ? 'border-emerald bg-emerald text-white' : 'border-slate-300 bg-white'}`}>{checked.has(order.order_key) && <Check className="h-3 w-3" />}</button></td><td className="border-b border-slate-100 px-3 py-3 font-medium">{order.purchase_order_number ?? '—'}</td><td className="border-b border-slate-100 px-3 py-3">{formatDate(order.creation_date)}</td><td className="max-w-[170px] truncate border-b border-slate-100 px-3 py-3">{order.supplier_name ?? 'Unknown'}</td><td className="max-w-[180px] truncate border-b border-slate-100 px-3 py-3">{order.department_name ?? 'Unknown'}</td><td className="border-b border-slate-100 px-3 py-3">{order.acquisition_type ?? '—'}</td><td className="max-w-[190px] truncate border-b border-slate-100 px-3 py-3">{order.items_preview.filter(Boolean).join(', ') || '—'}</td><td className="border-b border-slate-100 px-3 py-3 font-medium">{formatCurrency(order.total_value, 2)}</td><td className="border-b border-slate-100 px-3 py-3">{order.line_count}</td><td className="border-b border-slate-100 px-3 py-3 text-base font-bold">···</td></tr>)}</tbody>
                </table>
                {!isLoadingOrders && !orders?.orders.length && <div className="py-16 text-center text-sm text-slate-500">No orders match these filters.</div>}
                <Pagination query={query} totalPages={orders?.total_pages ?? 0} onPageChange={(page) => setQuery((current) => ({ ...current, page }))} onPageSizeChange={(pageSize) => setQuery((current) => ({ ...current, page: 1, pageSize }))} />
              </div>
            </div>
          </div>
          {selectedKey && <OrderDrawer summary={selectedOrder} detail={orderDetail.detail} isLoading={orderDetail.isLoading} error={orderDetail.error} onClose={() => setSelectedKey(null)} />}
        </div>
      </section>
    </div>
  );
}

function SelectFilter({ label, value, onChange, disabled, children }: { label: string; value: string; onChange: (value: string) => void; disabled: boolean; children: React.ReactNode }) { return <label className="min-w-0"><span className="field-label">{label}</span><span className="relative block"><select className="form-field w-full appearance-none pr-8 disabled:bg-slate-50" value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled}>{children}</select><ChevronDown className="pointer-events-none absolute right-3 top-3 h-3.5 w-3.5 text-slate-400" /></span></label>; }

function SortButton({ field, label, query, setQuery }: { field: OrdersQuery['sortBy']; label: string; query: OrdersQuery; setQuery: React.Dispatch<React.SetStateAction<OrdersQuery>> }) { return <button onClick={() => setQuery((current) => ({ ...current, page: 1, sortBy: field, sortDirection: current.sortBy === field && current.sortDirection === 'desc' ? 'asc' : 'desc' }))}>{label} {query.sortBy === field ? (query.sortDirection === 'desc' ? '↓' : '↑') : ''}</button>; }

function ErrorBanner({ message, onRetry }: { message: string; onRetry: () => void }) { return <div className="flex flex-wrap items-center gap-3 border-b border-red-100 bg-red-50 px-4 py-3 text-xs text-red-700"><TriangleAlert className="h-4 w-4" /><span className="flex-1">{message}</span><button className="font-semibold" onClick={onRetry}>Try again</button></div>; }

function Pagination({ query, totalPages, onPageChange, onPageSizeChange }: { query: OrdersQuery; totalPages: number; onPageChange: (page: number) => void; onPageSizeChange: (size: number) => void }) { const pages = pageNumbers(query.page, totalPages); return <div className="flex flex-wrap items-center gap-3 px-4 py-4 text-[11px] text-slate-600"><span>Show</span><select className="soft-button h-8 appearance-none" value={query.pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>{[10,20,50,100].map((size) => <option key={size}>{size}</option>)}</select><span>per page</span><div className="ml-auto flex items-center gap-1"><button disabled={query.page <= 1} onClick={() => onPageChange(query.page - 1)} className="p-2 disabled:opacity-30"><ArrowLeft className="h-4 w-4" /></button>{pages.map((page, index) => page === null ? <span key={`ellipsis-${index}`} className="px-1">…</span> : <button key={page} onClick={() => onPageChange(page)} className={`h-8 min-w-8 rounded-lg px-2 ${page === query.page ? 'bg-emerald font-semibold text-white' : ''}`}>{page}</button>)}<button disabled={query.page >= totalPages} onClick={() => onPageChange(query.page + 1)} className="p-2 disabled:opacity-30"><ArrowRight className="h-4 w-4" /></button></div></div>; }

function pageNumbers(current: number, total: number): Array<number | null> { if (total <= 7) return Array.from({ length: total }, (_, index) => index + 1); const values = new Set([1, total, current - 1, current, current + 1].filter((page) => page >= 1 && page <= total)); const sorted = [...values].sort((a, b) => a - b); const result: Array<number | null> = []; sorted.forEach((page, index) => { if (index > 0 && page - sorted[index - 1] > 1) result.push(null); result.push(page); }); return result; }

function OrderDrawer({ summary, detail, isLoading, error, onClose }: { summary: OrderListItem | null; detail: OrderDetail | null; isLoading: boolean; error: string | null; onClose: () => void }) { return <aside className="border-t border-slate-200 bg-white p-4 2xl:border-l 2xl:border-t-0"><div className="flex items-start justify-between gap-3"><div><div className="text-[9px] text-slate-500">Order details</div><h3 className="mt-1 break-all text-base font-bold">{summary?.purchase_order_number ?? 'Loading…'}</h3></div><button onClick={onClose} aria-label="Close order details"><X className="h-4 w-4" /></button></div>{isLoading && <div className="mt-6 flex items-center gap-2 rounded-lg bg-blue-50 p-3 text-xs text-blue-700"><RefreshCw className="h-4 w-4 animate-spin" />Loading line items…</div>}{error && <div className="mt-6 rounded-lg bg-red-50 p-3 text-xs text-red-700">{error}</div>}{detail && <><DetailSection title="Order Information" rows={[["Order Key", detail.order_key], ["Creation Date", formatDate(detail.creation_date)], ["Purchase Date", formatDate(detail.purchase_date)], ["Fiscal Year", detail.fiscal_year ?? '—'], ["Department", detail.department_name ?? '—'], ["Acquisition Type", detail.acquisition_type ?? '—'], ["Acquisition Method", detail.acquisition_method ?? '—'], ["Requisition", detail.requisition_number ?? '—'], ["LPA Number", detail.lpa_number ?? '—'], ["CalCard", detail.calcard ?? '—']]} /><div className="border-b border-slate-100 py-5"><h4 className="text-[11px] font-bold">Supplier Information</h4><div className="my-4 flex items-center gap-3 text-blue"><span className="text-2xl">♜</span><strong className="text-xs">{detail.supplier_name ?? 'Unknown supplier'}</strong></div><DetailRows rows={[["Supplier Code", String(detail.supplier_code ?? '—')], ["Qualifications", detail.supplier_qualifications ?? '—'], ["ZIP Code", String(detail.supplier_zip_code ?? '—')]]} /></div><div className="border-b border-slate-100 py-5"><h4 className="text-[11px] font-bold">Order Summary</h4><div className="mt-4"><DetailRows rows={[["Line Items", detail.line_count.toLocaleString()]]} /></div><div className="mt-3 flex justify-between text-xs font-bold"><span>Total Value</span><span className="text-base text-emerald">{formatCurrency(detail.total_value, 2)}</span></div></div><div className="py-5"><h4 className="text-[11px] font-bold">Line Items</h4><div className="mt-3 max-h-[340px] space-y-2 overflow-y-auto">{detail.items.map((item, index) => <article key={`${item.item_name}-${index}`} className="rounded-lg border border-slate-100 p-3"><div className="text-[10px] font-semibold text-slate-800">{item.item_name || 'Unnamed item'}</div>{item.item_description && item.item_description !== item.item_name && <p className="mt-1 line-clamp-2 text-[9px] text-slate-500">{item.item_description}</p>}<div className="mt-2 grid grid-cols-3 gap-2 text-[9px] text-slate-500"><span>Qty<br /><strong className="text-slate-700">{Number(item.quantity ?? 0).toLocaleString()}</strong></span><span>Unit price<br /><strong className="text-slate-700">{formatCurrency(Number(item.unit_price ?? 0), 2)}</strong></span><span>Total<br /><strong className="text-slate-700">{formatCurrency(Number(item.total_price ?? 0), 2)}</strong></span></div></article>)}</div></div></>}</aside>; }

function DetailSection({ title, rows }: { title: string; rows: string[][] }) { return <div className="border-b border-slate-100 py-5"><h4 className="mb-4 text-[11px] font-bold">{title}</h4><DetailRows rows={rows} /></div>; }
function DetailRows({ rows }: { rows: string[][] }) { return <div className="space-y-2">{rows.map(([label, value]) => <div key={label} className="flex items-start justify-between gap-4 text-[10px]"><span className="shrink-0 text-slate-500">{label}</span><span className="break-all text-right font-medium text-slate-700">{value}</span></div>)}</div>; }

function formatDate(value: string | null) { if (!value) return '—'; const date = new Date(value); return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en-US', { year: 'numeric', month: 'short', day: 'numeric' }).format(date); }
function periodLabel(period: { year: number; quarter?: number; month?: number }) { if (period.month) return `${period.year}-${String(period.month).padStart(2, '0')}`; if (period.quarter) return `Q${period.quarter} ${period.year}`; return String(period.year); }
function sortValueBuckets<T extends { _id: string }>(buckets: T[]) { const order = ['Negative', 'Under $5K', '$5K-$25K', '$25K-$100K', '$100K-$500K', '$500K+']; return [...buckets].sort((a, b) => order.indexOf(a._id) - order.indexOf(b._id)); }

function exportOrders(items: OrderListItem[]) { const headings = ['Order Number', 'Creation Date', 'Supplier', 'Department', 'Acquisition Type', 'Items', 'Total Value', 'Line Count']; const rows = items.map((order) => [order.purchase_order_number ?? '', order.creation_date ?? '', order.supplier_name ?? '', order.department_name ?? '', order.acquisition_type ?? '', order.items_preview.filter(Boolean).join(' | '), order.total_value, order.line_count]); const csv = [headings, ...rows].map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\n'); const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'procurement-orders.csv'; anchor.click(); URL.revokeObjectURL(url); }
