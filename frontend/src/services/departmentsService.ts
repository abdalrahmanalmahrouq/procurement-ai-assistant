import type {
  DepartmentAcquisitionType,
  DepartmentCategory,
  DepartmentFilters,
  DepartmentSpendPeriod,
  DepartmentSupplier,
  DepartmentSummary,
  DepartmentTrendGranularity,
  RankedDepartment,
} from '../types/departments';

const API_URL = import.meta.env.VITE_API_URL ?? '';

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { signal });

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Department request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function periodParameters(filters: Pick<DepartmentFilters, 'year' | 'quarter'>) {
  const params = new URLSearchParams();
  if (filters.year !== null) params.set('year', String(filters.year));
  if (filters.quarter !== null) params.set('quarter', String(filters.quarter));
  return params;
}

function withParameters(path: string, params: URLSearchParams) {
  return params.size ? `${path}?${params}` : path;
}

export const departmentsService = {
  getSummary(filters: DepartmentFilters, signal?: AbortSignal) {
    return request<DepartmentSummary>(withParameters('/api/departments/summary', periodParameters(filters)), signal);
  },

  getRanking(filters: DepartmentFilters, signal?: AbortSignal) {
    const params = periodParameters(filters);
    params.set('limit', String(filters.limit));
    return request<RankedDepartment[]>(withParameters('/api/departments/ranking', params), signal);
  },

  getSpendTrend(department: string, granularity: DepartmentTrendGranularity, signal?: AbortSignal) {
    const params = new URLSearchParams({ department, granularity });
    return request<DepartmentSpendPeriod[]>(`/api/departments/spend-trend?${params}`, signal);
  },

  getTopSuppliers(department: string, limit = 10, signal?: AbortSignal) {
    const params = new URLSearchParams({ department, limit: String(limit) });
    return request<DepartmentSupplier[]>(`/api/departments/top-suppliers?${params}`, signal);
  },

  getCategorySpend(department: string, limit = 10, signal?: AbortSignal) {
    const params = new URLSearchParams({ department, limit: String(limit) });
    return request<DepartmentCategory[]>(`/api/departments/category-spend?${params}`, signal);
  },

  getAcquisitionTypes(department: string, signal?: AbortSignal) {
    const params = new URLSearchParams({ department });
    return request<DepartmentAcquisitionType[]>(`/api/departments/acquisition-types?${params}`, signal);
  },
};
