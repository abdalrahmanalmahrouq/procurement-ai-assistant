export type ReportSection = 'spending_overview' | 'order_statistics' | 'top_suppliers' | 'department_spending' | 'department_quarterly' | 'monthly_trends' | 'quarterly_trends' | 'category_spending' | 'category_comparison' | 'custom_analysis';

export interface ReportSpec {
  report_focus: 'comprehensive' | 'supplier' | 'department' | 'category';
  report_type: 'all' | 'annual' | 'quarterly';
  year: number | null;
  quarter: number | null;
  department: string | null;
  acquisition_type: string | null;
  supplier: string | null;
  category: string | null;
  sections: ReportSection[];
  ranking_limit: number;
  charts: ('supplier' | 'department' | 'monthly' | 'quarterly' | 'category')[];
  tables: ('supplier' | 'department' | 'monthly' | 'quarterly' | 'category')[];
  export_format: 'pdf' | 'pdf_csv';
  custom_requirements: string[];
}

export interface ReportSummary {
  id: string;
  title: string;
  period: string;
  status: 'complete';
  created_at: string;
  conversation_id: string | null;
}

export interface Report extends ReportSummary {
  spec: ReportSpec;
  data: Record<string, Record<string, number | null> | Record<string, string | number | null>[]>;
  narrative: Record<string, string>;
}
