import {
  Building2,
  Headphones,
  Home,
  PackageCheck,
  Settings,
  Sparkles,
  Users,
  X,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { BrandMark } from './BrandMark';

const primaryItems = [
  { to: '/', label: 'Overview', icon: Home },
  { to: '/orders', label: 'Orders', icon: PackageCheck },
  { to: '/suppliers', label: 'Suppliers', icon: Users },
  { to: '/departments', label: 'Departments', icon: Building2 },
  { to: '/assistant', label: 'AI Assistant', icon: Sparkles },
  { to: '/settings', label: 'Settings', icon: Settings },
];

interface SidebarProps { open: boolean; onClose: () => void }

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/25 lg:hidden" onClick={onClose} />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-[276px] flex-col border-r border-slate-200 bg-white px-4 py-5 transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <button onClick={onClose} aria-label="Close navigation" className="absolute right-3 top-3 rounded-lg p-2 text-slate-500 lg:hidden"><X className="h-5 w-5" /></button>
        <div className="flex items-start gap-3 px-2">
          <BrandMark />
          <div className="pt-1">
            <div className="text-[19px] font-bold leading-6 tracking-[-0.02em] text-slate-950">Public Procurement<br />Demo</div>
            <div className="mt-2 text-xs leading-4 text-slate-500">California Public<br />Procurement Dataset</div>
          </div>
        </div>

        <nav className="mt-7 space-y-1" aria-label="Main navigation">
          {primaryItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={onClose}
              className={({ isActive }) => `flex h-11 items-center gap-4 rounded-xl px-4 text-[13px] font-medium transition ${isActive ? 'bg-blue-50 text-blue' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}`}
            >
              <Icon className="h-[18px] w-[18px]" strokeWidth={1.8} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto space-y-5 pt-6">
          
          <div className="flex items-center gap-3 rounded-xl border border-slate-200 p-4">
            <Headphones className="h-6 w-6 text-slate-600" />
            <div>
              <p className="text-[11px] font-semibold text-slate-800">Need help?</p>
              <button className="mt-1 text-[11px] font-semibold text-emerald">Contact support</button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
