export interface SupplierFilters {
  year: number | null;
  quarter: number | null;
  limit: number;
}

export interface SupplierConcentration {
  supplier_count: number;
  total_procurement_value: number;
  top_1_share: number;
  top_5_share: number;
  top_10_share: number;
}

export interface SupplierCount {
  active_suppliers: number;
}

export interface TopSupplier {
  supplier_code: string | number | null;
  supplier_name: string;
  total_procurement_value: number;
}

export interface TotalProcurementValue {
  total_procurement_value: number;
}

export interface AverageSupplierSpend {
  average_supplier_spend: number;
  supplier_count: number;
}

export interface RankedSupplier extends TopSupplier {
  unique_orders: number;
  line_records: number;
}

export interface SupplierCategorySpend {
  category: string;
  total_spending: number;
}

export interface SupplierSpendGroup {
  _id: string | null;
  total_spending: number;
}

export interface SupplierSpendPeriod {
  _id: {
    year: number;
    quarter: number;
  };
  total_spending: number;
}

export interface SupplierDetails {
  supplier: {
    supplier_code: string | number;
    supplier_name: string;
    supplier_zip_code: string | number | null;
    supplier_qualifications: string | null;
  };
  summary: {
    unique_orders: number;
    total_procurement_value: number;
    average_order_value: number;
    line_records: number;
  };
  departments: SupplierSpendGroup[];
  top_categories: SupplierSpendGroup[];
  spend_trend: SupplierSpendPeriod[];
}

export interface SuppliersDashboardData {
  concentration: SupplierConcentration;
  count: SupplierCount;
  topSupplier: TopSupplier | null;
  totalValue: TotalProcurementValue;
  averageSpend: AverageSupplierSpend;
  ranking: RankedSupplier[];
  categories: SupplierCategorySpend[];
}
