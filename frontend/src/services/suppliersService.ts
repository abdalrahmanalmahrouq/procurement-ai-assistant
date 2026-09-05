import type {
  AverageSupplierSpend,
  RankedSupplier,
  SupplierCategorySpend,
  SupplierConcentration,
  SupplierCount,
  SupplierDetails,
  SupplierFilters,
  TopSupplier,
  TotalProcurementValue,
} from '../types/suppliers';

const API_URL = import.meta.env.VITE_API_URL ?? '';

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { signal });

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Supplier request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function periodParameters(filters: Pick<SupplierFilters, 'year' | 'quarter'>) {
  const params = new URLSearchParams();

  if (filters.year !== null) params.set('year', String(filters.year));
  if (filters.quarter !== null) params.set('quarter', String(filters.quarter));

  return params;
}

function withParameters(path: string, params: URLSearchParams) {
  return params.size ? `${path}?${params}` : path;
}

export const suppliersService = {
  getConcentration(filters: SupplierFilters, signal?: AbortSignal) {
    return request<SupplierConcentration>(withParameters('/api/suppliers/concentration', periodParameters(filters)), signal);
  },

  getCount(filters: SupplierFilters, signal?: AbortSignal) {
    return request<SupplierCount>(withParameters('/api/suppliers/number-of-suppliers', periodParameters(filters)), signal);
  },

  getTopSupplier(filters: SupplierFilters, signal?: AbortSignal) {
    return request<TopSupplier | null>(withParameters('/api/suppliers/top', periodParameters(filters)), signal);
  },

  getTotalValue(filters: SupplierFilters, signal?: AbortSignal) {
    return request<TotalProcurementValue>(withParameters('/api/suppliers/total-value', periodParameters(filters)), signal);
  },

  getAverageSpend(filters: SupplierFilters, signal?: AbortSignal) {
    return request<AverageSupplierSpend>(withParameters('/api/suppliers/average-spend', periodParameters(filters)), signal);
  },

  getRanking(filters: SupplierFilters, signal?: AbortSignal) {
    const params = periodParameters(filters);
    params.set('limit', String(filters.limit));
    return request<RankedSupplier[]>(withParameters('/api/suppliers/ranking', params), signal);
  },

  getCategorySpend(filters: SupplierFilters, topN = 5, signal?: AbortSignal) {
    const params = periodParameters(filters);
    params.set('top_n', String(topN));
    return request<SupplierCategorySpend[]>(withParameters('/api/suppliers/category-spend', params), signal);
  },

  getDetails(supplierCode: string | number, signal?: AbortSignal) {
    const params = new URLSearchParams({ supplier_code: String(supplierCode) });
    return request<SupplierDetails>(`/api/suppliers/details?${params}`, signal);
  },
};
