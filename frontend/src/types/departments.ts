export interface DepartmentFilters {
  year: number | null;
  quarter: number | null;
  limit: number;
}

export interface DepartmentSummaryEntry {
  department_name: string;
  total_spending: number;
  unique_orders: number;
}

export interface DepartmentSummary {
  department_count: number;
  total_procurement_value: number;
  average_department_spend: number;
  top_spending_department: DepartmentSummaryEntry | null;
  most_orders_department: DepartmentSummaryEntry | null;
}

export interface RankedDepartment {
  department_name: string;
  total_procurement_value: number;
  unique_orders: number;
  line_records: number;
}

export type DepartmentTrendGranularity = 'month' | 'quarter';

export interface DepartmentSpendPeriod {
  _id: {
    year: number;
    month?: number;
    quarter?: number;
  };
  total_spending: number;
  unique_orders: number;
}

export interface DepartmentSupplier {
  supplier_code: string | number | null;
  supplier_name: string;
  total_spending: number;
  unique_orders: number;
}

export interface DepartmentCategory {
  category: string;
  total_spending: number;
  unique_orders: number;
}

export interface DepartmentAcquisitionType {
  acquisition_type: string;
  total_spending: number;
  unique_orders: number;
}

export interface DepartmentsDashboardData {
  summary: DepartmentSummary;
  ranking: RankedDepartment[];
}

export interface DepartmentInsightsData {
  spendTrend: DepartmentSpendPeriod[];
  topSuppliers: DepartmentSupplier[];
  categories: DepartmentCategory[];
  acquisitionTypes: DepartmentAcquisitionType[];
}
