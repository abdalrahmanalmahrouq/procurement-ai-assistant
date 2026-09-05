import type { DashboardSummary } from '../types/procurement';

const API_URL = import.meta.env.VITE_API_URL ?? '';

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { signal });
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const procurementApi = {
  getDashboardSummary: (signal?: AbortSignal) =>
    request<DashboardSummary>('/api/procurement/dashboard/summary', signal),
  getOrderCount: (year: number, quarter: number, signal?: AbortSignal) =>
    request<{ total_orders: number }>(
      `/api/procurement/orders/count?year=${year}&quarter=${quarter}`,
      signal,
    ),
};
