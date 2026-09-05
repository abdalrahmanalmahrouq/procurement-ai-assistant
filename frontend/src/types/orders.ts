export type SpendGranularity = 'month' | 'quarter' | 'year';
export type OrderSortField = 'creation_date' | 'total_value' | 'line_count' | 'purchase_order_number';

export interface LargestOrder {
  _id: string;
  order_total: number;
  line_count: number;
  purchase_order_number: string | null;
  department_name: string | null;
  supplier_name: string | null;
  creation_date: string | null;
}

export interface OrdersSummary {
  total_orders: number;
  total_line_records: number;
  total_procurement_value: number;
  average_order_value: number;
  largest_order: LargestOrder | null;
}

export interface SpendOverTimePoint {
  _id: { year: number; quarter?: number; month?: number };
  total_spending: number;
  order_count: number;
}

export interface AcquisitionTypeBreakdown {
  _id: string;
  total_procurement_value: number;
  unique_orders: number;
}

export interface OrderValueBucket {
  _id: string;
  orders: number;
  total_value: number;
}

export interface OrderFilterOptions {
  fiscal_years: string[];
  acquisition_types: string[];
  acquisition_methods: string[];
  departments: string[];
}

export interface OrderListItem {
  order_key: string;
  purchase_order_number: string | null;
  creation_date: string | null;
  purchase_date: string | null;
  fiscal_year: string | null;
  department_name: string | null;
  supplier_name: string | null;
  acquisition_type: string | null;
  acquisition_method: string | null;
  line_count: number;
  total_value: number;
  items_preview: Array<string | null>;
}

export interface OrdersListResponse {
  page: number;
  page_size: number;
  total_orders: number;
  total_pages: number;
  orders: OrderListItem[];
}

export interface OrderLineItem {
  item_name: string | null;
  item_description: string | null;
  quantity: number | null;
  unit_price: number | null;
  total_price: number | null;
  classification_codes: string | null;
  normalized_unspsc: string | number | null;
  commodity_title: string | null;
  class: string | number | null;
  class_title: string | null;
  family: string | number | null;
  family_title: string | null;
  segment: string | number | null;
}

export interface OrderDetail {
  order_key: string;
  purchase_order_number: string | null;
  creation_date: string | null;
  purchase_date: string | null;
  fiscal_year: string | null;
  department_name: string | null;
  supplier_code: string | number | null;
  supplier_name: string | null;
  supplier_qualifications: string | null;
  supplier_zip_code: string | number | null;
  lpa_number: string | null;
  requisition_number: string | null;
  acquisition_type: string | null;
  sub_acquisition_type: string | null;
  acquisition_method: string | null;
  sub_acquisition_method: string | null;
  calcard: string | null;
  total_value: number;
  line_count: number;
  items: OrderLineItem[];
}

export interface OrdersQuery {
  page: number;
  pageSize: number;
  year: number | null;
  quarter: number | null;
  fiscalYear: string;
  department: string;
  supplier: string;
  acquisitionType: string;
  acquisitionMethod: string;
  minValue: number | null;
  maxValue: number | null;
  search: string;
  sortBy: OrderSortField;
  sortDirection: 'asc' | 'desc';
}
