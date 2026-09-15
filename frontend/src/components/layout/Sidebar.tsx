import {
  Building2,
  ChevronLeft,
  ChevronRight,
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

interface SidebarProps {
  open: boolean;
  collapsed: boolean;
  onClose: () => void;
  onToggleCollapse: () => void;
}

export function Sidebar({ open, collapsed, onClose, onToggleCollapse }: SidebarProps) {
  return (
    <>
      {open && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/25 lg:hidden" onClick={onClose} />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-[276px] flex-col border-r border-slate-200 bg-white px-4 py-5 transition-[width,padding,transform] duration-300 lg:translate-x-0 ${collapsed ? 'lg:w-[84px] lg:px-3' : 'lg:w-[276px]'} ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <button onClick={onClose} aria-label="Close navigation" className="absolute right-3 top-3 rounded-lg p-2 text-slate-500 lg:hidden"><X className="h-5 w-5" /></button>
        <button
          type="button"
          onClick={onToggleCollapse}
          aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          title={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          className="absolute -right-3.5 top-7 hidden h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm transition hover:border-blue-300 hover:text-blue lg:flex"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
        <div className={`flex items-start gap-3 px-2 ${collapsed ? 'lg:justify-center lg:px-0' : ''}`}>
          <BrandMark />
          <div className={`pt-1 ${collapsed ? 'lg:hidden' : ''}`}>
            <div className="text-[19px] font-bold leading-6 tracking-[-0.02em] text-slate-950">Procurement<br />Demo</div>
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
              title={collapsed ? label : undefined}
              aria-label={label}
              className={({ isActive }) => `flex h-11 items-center gap-4 rounded-xl px-4 text-[13px] font-medium transition ${collapsed ? 'lg:justify-center lg:px-0' : ''} ${isActive ? 'bg-blue-50 text-blue' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}`}
            >
              <Icon className="h-[18px] w-[18px]" strokeWidth={1.8} />
              <span className={collapsed ? 'lg:hidden' : ''}>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto space-y-5 pt-6">
          
          <div className={`flex items-center gap-3 rounded-xl border border-slate-200 p-4 ${collapsed ? 'lg:justify-center lg:px-2' : ''}`} title={collapsed ? 'Contact support' : undefined}>
            <Headphones className="h-6 w-6 text-slate-600" />
            <div className={collapsed ? 'lg:hidden' : ''}>
              <p className="text-[11px] font-semibold text-slate-800">Need help?</p>
              <button className="mt-1 text-[11px] font-semibold text-blue">Contact support</button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
