import { Menu, Search } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { Avatar } from '../ui/Avatar';

const person ='Abdalrahman Almahrouq';

const pageMeta: Record<string, { title: string; subtitle: string; name?: string }> = {
  '/': { title: 'Good morning, Abdalrahman 👋', subtitle: "Here’s your procurement records and order overview." },
  '/orders': { title: 'Good morning, Abdalrahman 👋', subtitle: "Here’s your procurement records and order overview." },
  '/suppliers': { title: 'Supplier Intelligence', subtitle: 'Insights and performance overview of your supplier ecosystem.', name: person },
  '/departments': { title: 'Department Intelligence', subtitle: 'Spending, order activity, and procurement patterns across departments.', name: person },
  '/assistant': { title: 'AI Assistant', subtitle: 'Conversational analytics for California public procurement data.', name: person },
};

export function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const { pathname } = useLocation();
  const fallbackName = pathname.slice(1).replace(/-/g, ' ');
  const meta = pageMeta[pathname] ?? {
    title: fallbackName ? fallbackName[0].toUpperCase() + fallbackName.slice(1) : 'Overview',
    subtitle: 'Explore your public procurement data.',
  };
  const person = meta.name ?? 'Abdalrahman Almahrouq';

  return (
    <header className="sticky top-0 z-20 flex h-[92px] items-center border-b border-slate-200 bg-white/95 px-4 backdrop-blur md:px-7">
      <button className="mr-3 rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden" onClick={onMenuClick} aria-label="Open navigation">
        <Menu className="h-5 w-5" />
      </button>
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-xl font-bold tracking-[-0.025em] text-slate-950">{meta.title}</h1>
        <p className="mt-1 hidden truncate text-xs text-slate-500 sm:block">{meta.subtitle}</p>
      </div>
      <div className={`ml-5 h-11 max-w-[450px] flex-1 items-center gap-3 rounded-lg border border-slate-200 px-3 text-xs text-slate-500 shadow-sm ${pathname === '/assistant' ? 'hidden' : 'hidden xl:flex'}`}>
        <Search className="h-5 w-5" />
        <input aria-label="Global search" className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-slate-500" placeholder={pathname === '/suppliers' ? 'Search suppliers, categories, spend...' : 'Search orders, suppliers, items, departments...'} />
        <kbd className="rounded bg-slate-50 px-2 py-1 text-[10px] font-medium">⌘ K</kbd>
      </div>
      
      
      <div className={`ml-3 flex items-center gap-3 border-l border-slate-100 pl-4 ${pathname === '/assistant' ? 'xl:w-[270px]' : ''}`}>
        <Avatar name={person} size="lg" color={pathname === '/assistant' ? '#1f619e' : '#1f619e'} />
        <div className="hidden min-w-0 xl:block">
          <p className="truncate text-xs font-bold text-slate-900">{person}</p>
          <p className="mt-1 text-[10px] text-slate-500">Procurement Analyst</p>
        </div>
      </div>
    </header>
  );
}
