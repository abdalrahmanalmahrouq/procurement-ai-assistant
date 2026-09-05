import { useEffect, useMemo, useState } from 'react';
import { departmentsService } from '../services/departmentsService';
import type {
  DepartmentFilters,
  DepartmentInsightsData,
  DepartmentsDashboardData,
  DepartmentTrendGranularity,
} from '../types/departments';

interface RequestState<T> {
  key: string;
  data: T | null;
  error: string | null;
}

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === 'AbortError';
}

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export function useDepartments(filters: DepartmentFilters, reloadVersion: number) {
  const [state, setState] = useState<RequestState<DepartmentsDashboardData>>({ key: '', data: null, error: null });
  const requestKey = useMemo(() => JSON.stringify([filters, reloadVersion]), [filters, reloadVersion]);

  useEffect(() => {
    const controller = new AbortController();

    Promise.all([
      departmentsService.getSummary(filters, controller.signal),
      departmentsService.getRanking(filters, controller.signal),
    ])
      .then(([summary, ranking]) => setState({ key: requestKey, data: { summary, ranking }, error: null }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) {
          setState({ key: requestKey, data: null, error: errorMessage(error, 'Unable to load department data.') });
        }
      });

    return () => controller.abort();
  }, [filters, requestKey]);

  const currentState = state.key === requestKey ? state : null;

  return {
    data: currentState?.data ?? null,
    error: currentState?.error ?? null,
    isLoading: currentState === null,
  };
}

export function useDepartmentInsights(
  department: string | null,
  granularity: DepartmentTrendGranularity,
) {
  const [state, setState] = useState<RequestState<DepartmentInsightsData>>({ key: '', data: null, error: null });
  const requestKey = department ? `${department}:${granularity}` : '';

  useEffect(() => {
    if (!department) return;

    const controller = new AbortController();

    Promise.all([
      departmentsService.getSpendTrend(department, granularity, controller.signal),
      departmentsService.getTopSuppliers(department, 10, controller.signal),
      departmentsService.getCategorySpend(department, 10, controller.signal),
      departmentsService.getAcquisitionTypes(department, controller.signal),
    ])
      .then(([spendTrend, topSuppliers, categories, acquisitionTypes]) => {
        setState({ key: requestKey, data: { spendTrend, topSuppliers, categories, acquisitionTypes }, error: null });
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) {
          setState({ key: requestKey, data: null, error: errorMessage(error, 'Unable to load department insights.') });
        }
      });

    return () => controller.abort();
  }, [department, granularity, requestKey]);

  const currentState = requestKey && state.key === requestKey ? state : null;

  return {
    data: currentState?.data ?? null,
    error: currentState?.error ?? null,
    isLoading: department !== null && currentState === null,
  };
}
