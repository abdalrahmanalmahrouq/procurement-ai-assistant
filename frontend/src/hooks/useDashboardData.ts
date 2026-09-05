import { useCallback, useEffect, useState } from 'react';
import { procurementApi } from '../services/procurementApi';
import type { DashboardSummary } from '../types/procurement';

interface DashboardState {
  data: DashboardSummary | null;
  highestQuarterOrderCount: number | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: DashboardState = {
  data: null,
  highestQuarterOrderCount: null,
  isLoading: true,
  error: null,
};

export function useDashboardData() {
  const [state, setState] = useState<DashboardState>(initialState);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadDashboard() {
      setState((current) => ({ ...current, isLoading: true, error: null }));

      try {
        const data = await procurementApi.getDashboardSummary(controller.signal);
        let highestQuarterOrderCount: number | null = null;

        if (data.highest_spending_quarter) {
          const { year, quarter } = data.highest_spending_quarter;
          try {
            const result = await procurementApi.getOrderCount(year, quarter, controller.signal);
            highestQuarterOrderCount = result.total_orders;
          } catch (error) {
            if (error instanceof DOMException && error.name === 'AbortError') throw error;
          }
        }

        setState({ data, highestQuarterOrderCount, isLoading: false, error: null });
      } catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setState({
          data: null,
          highestQuarterOrderCount: null,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Unable to load dashboard data.',
        });
      }
    }

    void loadDashboard();
    return () => controller.abort();
  }, [requestVersion]);

  const retry = useCallback(() => setRequestVersion((version) => version + 1), []);

  return { ...state, retry };
}
