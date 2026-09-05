import type { OrderStatus } from '../../types/procurement';

const styles: Record<OrderStatus, string> = {
  Delivered: 'bg-green-50 text-green-700',
  Approved: 'bg-emerald-50 text-emerald-700',
  'In Transit': 'bg-blue-50 text-blue-700',
  Pending: 'bg-amber-50 text-amber-700',
  Cancelled: 'bg-slate-100 text-slate-600',
};

export function StatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`rounded-md px-2.5 py-1 text-[11px] font-semibold ${styles[status]}`}>{status}</span>;
}

export function ScoreBadge({ score }: { score: number }) {
  return <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-bold text-emerald-700">{score}</span>;
}
