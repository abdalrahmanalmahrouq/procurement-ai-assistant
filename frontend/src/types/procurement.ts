export type TrendDirection = 'up' | 'down' | 'neutral';

export interface Department {
  name: string;
  spend: number;
  percent: number;
  color: string;
}

export type OrderStatus = 'Delivered' | 'Approved' | 'In Transit' | 'Pending' | 'Cancelled';

export interface Order {
  id: string;
  date: string;
  supplier: string;
  department: string;
  category: string;
  item: string;
  value: number;
  status: OrderStatus;
}

export interface QuarterSpend {
  label: string;
  value: number;
}

export interface DashboardSummary {
  highest_spending_quarter: {
    year: number;
    quarter: number;
    total_spending: number;
  } | null;
  average_order_value: number;
  top_suppliers: Array<{
    supplier_name: string;
    total_procurement_value: number;
  }>;
  top_departments: Array<{
    department_name: string;
    total_spending: number;
  }>;
  top_items: Array<{
    item_name: string;
    frequency: number;
  }>;
}
