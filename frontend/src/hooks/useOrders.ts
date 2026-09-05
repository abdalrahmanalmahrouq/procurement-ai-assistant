import { useEffect, useMemo, useState } from 'react';
import { ordersService } from '../services/ordersService';
import type {
  AcquisitionTypeBreakdown,
  OrderDetail,
  OrderFilterOptions,
  OrdersListResponse,
  OrdersQuery,
  OrdersSummary,
  OrderValueBucket,
  SpendOverTimePoint,
} from '../types/orders';

const emptyFilters: OrderFilterOptions = {
  fiscal_years: [],
  acquisition_types: [],
  acquisition_methods: [],
  departments: [],
};

interface OrderAnalytics {
  summary: OrdersSummary;
  spendOverTime: SpendOverTimePoint[];
  acquisitionTypes: AcquisitionTypeBreakdown[];
  valueDistribution: OrderValueBucket[];
}

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

export function useOrders(query: OrdersQuery, reloadVersion: number) {
  const [debouncedSearch, setDebouncedSearch] = useState(query.search);
  const [listState, setListState] = useState<RequestState<OrdersListResponse>>({ key: '', data: null, error: null });
  const [analyticsState, setAnalyticsState] = useState<RequestState<OrderAnalytics>>({ key: '', data: null, error: null });
  const [filtersState, setFiltersState] = useState<RequestState<OrderFilterOptions>>({ key: '', data: null, error: null });

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebouncedSearch(query.search), 350);
    return () => window.clearTimeout(timeout);
  }, [query.search]);

  const effectiveQuery = useMemo<OrdersQuery>(() => ({ ...query, search: debouncedSearch }), [query, debouncedSearch]);
  const listKey = useMemo(() => JSON.stringify([effectiveQuery, reloadVersion]), [effectiveQuery, reloadVersion]);
  const sharedKey = String(reloadVersion);

  useEffect(() => {
    const controller = new AbortController();
    ordersService.getOrders(effectiveQuery, controller.signal)
      .then((data) => setListState({ key: listKey, data, error: null }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) setListState({ key: listKey, data: null, error: errorMessage(error, 'Unable to load orders.') });
      });
    return () => controller.abort();
  }, [effectiveQuery, listKey]);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      ordersService.getSummary(controller.signal),
      ordersService.getSpendOverTime('quarter', undefined, controller.signal),
      ordersService.getAcquisitionTypes(undefined, controller.signal),
      ordersService.getValueDistribution(controller.signal),
    ])
      .then(([summary, spendOverTime, acquisitionTypes, valueDistribution]) => {
        setAnalyticsState({ key: sharedKey, data: { summary, spendOverTime, acquisitionTypes, valueDistribution }, error: null });
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) setAnalyticsState({ key: sharedKey, data: null, error: errorMessage(error, 'Unable to load order analytics.') });
      });
    return () => controller.abort();
  }, [sharedKey]);

  useEffect(() => {
    const controller = new AbortController();
    ordersService.getFilterOptions(controller.signal)
      .then((data) => setFiltersState({ key: sharedKey, data, error: null }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) setFiltersState({ key: sharedKey, data: null, error: errorMessage(error, 'Unable to load order filters.') });
      });
    return () => controller.abort();
  }, [sharedKey]);

  const currentList = listState.key === listKey ? listState : null;
  const currentAnalytics = analyticsState.key === sharedKey ? analyticsState : null;
  const currentFilters = filtersState.key === sharedKey ? filtersState : null;

  return {
    orders: currentList?.data ?? null,
    analytics: currentAnalytics?.data ?? null,
    filters: currentFilters?.data ?? emptyFilters,
    isLoadingOrders: currentList === null,
    isLoadingAnalytics: currentAnalytics === null,
    isLoadingFilters: currentFilters === null,
    error: currentList?.error ?? currentAnalytics?.error ?? currentFilters?.error ?? null,
  };
}

export function useSupplierSuggestions(search: string) {
  const [debouncedSearch, setDebouncedSearch] = useState(search);
  const [state, setState] = useState<RequestState<string[]>>({ key: '', data: null, error: null });

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timeout);
  }, [search]);

  useEffect(() => {
    if (debouncedSearch.length < 2) return;
    const controller = new AbortController();
    ordersService.searchSuppliers(debouncedSearch, 12, controller.signal)
      .then((data) => setState({ key: debouncedSearch, data, error: null }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) setState({ key: debouncedSearch, data: null, error: errorMessage(error, 'Unable to search suppliers.') });
      });
    return () => controller.abort();
  }, [debouncedSearch]);

  return debouncedSearch.length >= 2 && state.key === debouncedSearch ? state.data ?? [] : [];
}

export function useOrderDetail(orderKey: string | null) {
  const [state, setState] = useState<RequestState<OrderDetail>>({ key: '', data: null, error: null });

  useEffect(() => {
    if (!orderKey) return;
    const controller = new AbortController();
    ordersService.getOrderDetails(orderKey, controller.signal)
      .then((data) => setState({ key: orderKey, data, error: null }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) setState({ key: orderKey, data: null, error: errorMessage(error, 'Unable to load order details.') });
      });
    return () => controller.abort();
  }, [orderKey]);

  const currentState = orderKey && state.key === orderKey ? state : null;
  return {
    detail: currentState?.data ?? null,
    isLoading: orderKey !== null && currentState === null,
    error: currentState?.error ?? null,
  };
}
