import { useEffect, useState, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [pathname]);

  return (
    <div className="min-h-screen bg-[#f8fafb]">
      <Sidebar
        open={sidebarOpen}
        collapsed={sidebarCollapsed}
        onClose={() => setSidebarOpen(false)}
        onToggleCollapse={() => setSidebarCollapsed((current) => !current)}
      />
      <div className={`transition-[padding] duration-300 ${sidebarCollapsed ? 'lg:pl-[84px]' : 'lg:pl-[276px]'}`}>
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className={pathname === '/assistant'
          ? 'h-[calc(100dvh-92px)] min-h-0 overflow-hidden'
          : 'min-h-[calc(100vh-92px)] p-3 md:p-5'}>
          {children}
        </main>
      </div>
    </div>
  );
}
