import type {
  AcquisitionTypeBreakdown,
  OrderDetail,
  OrderFilterOptions,
  OrdersListResponse,
  OrdersQuery,
  OrdersSummary,
  OrderValueBucket,
  SpendGranularity,
  SpendOverTimePoint,
} from '../types/orders';

const API_URL = import.meta.env.VITE_API_URL ?? '';

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { signal });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Orders request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function orderQueryParameters(query: OrdersQuery) {
  const params = new URLSearchParams({
    page: String(query.page),
    page_size: String(query.pageSize),
    sort_by: query.sortBy,
    sort_direction: query.sortDirection,
  });

  if (query.year !== null) params.set('year', String(query.year));
  if (query.quarter !== null) params.set('quarter', String(query.quarter));
  if (query.fiscalYear) params.set('fiscal_year', query.fiscalYear);
  if (query.department) params.set('department', query.department);
  if (query.supplier) params.set('supplier', query.supplier);
  if (query.acquisitionType) params.set('acquisition_type', query.acquisitionType);
  if (query.acquisitionMethod) params.set('acquisition_method', query.acquisitionMethod);
  if (query.minValue !== null) params.set('min_value', String(query.minValue));
  if (query.maxValue !== null) params.set('max_value', String(query.maxValue));
  if (query.search.trim()) params.set('search', query.search.trim());

  return params;
}

export const ordersService = {
  getSummary(signal?: AbortSignal) {
    return request<OrdersSummary>('/api/orders/summary', signal);
  },
  getSpendOverTime(granularity: SpendGranularity = 'quarter', year?: number, signal?: AbortSignal) {
    const params = new URLSearchParams({ granularity });
    if (year !== undefined) params.set('year', String(year));
    return request<SpendOverTimePoint[]>(`/api/orders/spend-over-time?${params}`, signal);
  },
  getAcquisitionTypes(year?: number, signal?: AbortSignal) {
    const params = new URLSearchParams();
    if (year !== undefined) params.set('year', String(year));
    const suffix = params.size ? `?${params}` : '';
    return request<AcquisitionTypeBreakdown[]>(`/api/orders/acquisition-types${suffix}`, signal);
  },
  getValueDistribution(signal?: AbortSignal) {
    return request<OrderValueBucket[]>('/api/orders/value-distribution', signal);
  },
  getFilterOptions(signal?: AbortSignal) {
    return request<OrderFilterOptions>('/api/orders/filter-options', signal);
  },
  searchSuppliers(query: string, limit = 20, signal?: AbortSignal) {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    return request<string[]>(`/api/orders/suppliers/search?${params}`, signal);
  },
  getOrders(query: OrdersQuery, signal?: AbortSignal) {
    return request<OrdersListResponse>(`/api/orders?${orderQueryParameters(query)}`, signal);
  },
  getOrderDetails(orderKey: string, signal?: AbortSignal) {
    const params = new URLSearchParams({ order_key: orderKey });
    return request<OrderDetail>(`/api/orders/details?${params}`, signal);
  },
};
