import { useEffect, useMemo, useState } from 'react';
import { suppliersService } from '../services/suppliersService';
import type { SupplierDetails, SupplierFilters, SuppliersDashboardData } from '../types/suppliers';

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

export function useSuppliers(filters: SupplierFilters, reloadVersion: number) {
  const [state, setState] = useState<RequestState<SuppliersDashboardData>>({ key: '', data: null, error: null });
  const requestKey = useMemo(() => JSON.stringify([filters, reloadVersion]), [filters, reloadVersion]);

  useEffect(() => {
    const controller = new AbortController();

    Promise.all([
      suppliersService.getConcentration(filters, controller.signal),
      suppliersService.getCount(filters, controller.signal),
      suppliersService.getTopSupplier(filters, controller.signal),
      suppliersService.getTotalValue(filters, controller.signal),
      suppliersService.getAverageSpend(filters, controller.signal),
      suppliersService.getRanking(filters, controller.signal),
      suppliersService.getCategorySpend(filters, 5, controller.signal),
    ])
      .then(([concentration, count, topSupplier, totalValue, averageSpend, ranking, categories]) => {
        setState({
          key: requestKey,
          data: { concentration, count, topSupplier, totalValue, averageSpend, ranking, categories },
          error: null,
        });
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) {
          setState({ key: requestKey, data: null, error: errorMessage(error, 'Unable to load supplier data.') });
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

export function useSupplierDetails(supplierCode: string | number | null) {
  const [state, setState] = useState<RequestState<SupplierDetails>>({ key: '', data: null, error: null });
  const requestKey = supplierCode === null ? '' : String(supplierCode);

  useEffect(() => {
    if (supplierCode === null) return;

    const controller = new AbortController();

    suppliersService.getDetails(supplierCode, controller.signal)
      .then((data) => setState({ key: requestKey, data, error: null }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) {
          setState({ key: requestKey, data: null, error: errorMessage(error, 'Unable to load supplier details.') });
        }
      });

    return () => controller.abort();
  }, [requestKey, supplierCode]);

  const currentState = requestKey && state.key === requestKey ? state : null;

  return {
    details: currentState?.data ?? null,
    error: currentState?.error ?? null,
    isLoading: supplierCode !== null && currentState === null,
  };
}
