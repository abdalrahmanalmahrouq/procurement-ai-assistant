import { Building2 } from 'lucide-react';
import type { RankedDepartment } from '../../types/departments';
import { formatCurrency } from '../../utils/format';

interface DepartmentRankingTableProps {
  departments: RankedDepartment[];
  totalValue: number;
  selectedName: string | null;
  onSelect: (department: RankedDepartment) => void;
}

export function DepartmentRankingTable({
  departments,
  totalValue,
  selectedName,
  onSelect,
}: DepartmentRankingTableProps) {
  if (departments.length === 0) {
    return <div className="flex min-h-48 items-center justify-center text-xs text-slate-400">No departments match this search.</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-[10px]">
        <thead>
          <tr className="bg-slate-50 text-slate-500">
            {['Rank', 'Department', 'Procurement Value', '% of Total', 'Orders', 'Line Records'].map((heading) => (
              <th key={heading} className="px-3 py-2 font-medium">{heading}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {departments.map((department, index) => {
            const share = totalValue ? (department.total_procurement_value / totalValue) * 100 : 0;
            const isSelected = department.department_name === selectedName;

            return (
              <tr
                key={department.department_name}
                className={`${isSelected ? 'bg-emerald-50/60' : 'hover:bg-slate-50'} cursor-pointer border-b border-slate-100 text-slate-600`}
                onClick={() => onSelect(department)}
              >
                <td className="px-3 py-2.5">
                  <span className={`flex h-6 w-6 items-center justify-center rounded-full font-bold ${index === 0 ? 'bg-emerald text-white' : 'bg-slate-100'}`}>{index + 1}</span>
                </td>
                <td className="max-w-[260px] px-3 py-2.5">
                  <span className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 shrink-0 text-blue" />
                    <span className="truncate" title={department.department_name}>{department.department_name}</span>
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 font-medium">{formatCurrency(department.total_procurement_value, 2)}</td>
                <td className="px-3 py-2.5">{share.toFixed(1)}%</td>
                <td className="px-3 py-2.5">{department.unique_orders.toLocaleString()}</td>
                <td className="px-3 py-2.5">{department.line_records.toLocaleString()}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
