import { Avatar } from '../ui/Avatar';
import type { RankedSupplier } from '../../types/suppliers';
import { formatCurrency } from '../../utils/format';

interface SupplierRankingTableProps {
  suppliers: RankedSupplier[];
  totalValue: number;
  selectedCode: string | number | null;
  colors: string[];
  onSelect: (supplier: RankedSupplier) => void;
}

export function SupplierRankingTable({
  suppliers,
  totalValue,
  selectedCode,
  colors,
  onSelect,
}: SupplierRankingTableProps) {
  if (suppliers.length === 0) {
    return <div className="flex min-h-48 items-center justify-center text-xs text-slate-400">No suppliers match this search.</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[690px] text-left text-[10px]">
        <thead>
          <tr className="bg-slate-50 text-slate-500">
            {['Rank', 'Supplier', 'Spend (USD)', '% of Total', 'Orders', 'Line Records'].map((heading) => (
              <th key={heading} className="px-2 py-2 font-medium">{heading}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {suppliers.map((supplier, index) => {
            const isSelected = supplier.supplier_code !== null && String(selectedCode) === String(supplier.supplier_code);
            const share = totalValue ? (supplier.total_procurement_value / totalValue) * 100 : 0;

            return (
              <tr
                key={`${supplier.supplier_code ?? supplier.supplier_name}-${index}`}
                className={`${isSelected ? 'bg-blue-50/60' : 'hover:bg-slate-50'} ${supplier.supplier_code === null ? 'cursor-default' : 'cursor-pointer'} border-b border-slate-100 text-slate-600`}
                onClick={() => onSelect(supplier)}
              >
                <td className="px-2 py-2.5">
                  <span className={`flex h-6 w-6 items-center justify-center rounded-full font-bold ${index === 0 ? 'bg-emerald text-white' : 'bg-slate-100'}`}>{index + 1}</span>
                </td>
                <td className="max-w-[220px] px-2 py-2.5">
                  <span className="flex items-center gap-2">
                    <Avatar name={supplier.supplier_name} color={colors[index % colors.length]} size="sm" />
                    <span className="truncate" title={supplier.supplier_name}>{supplier.supplier_name}</span>
                  </span>
                </td>
                <td className="whitespace-nowrap px-2 py-2.5 font-medium">{formatCurrency(supplier.total_procurement_value, 2)}</td>
                <td className="px-2 py-2.5">{share.toFixed(1)}%</td>
                <td className="px-2 py-2.5">{supplier.unique_orders.toLocaleString()}</td>
                <td className="px-2 py-2.5">{supplier.line_records.toLocaleString()}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
