import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { AssistantPage } from './pages/AssistantPage';
import { ComingSoonPage } from './pages/ComingSoonPage';
import { DepartmentsPage } from './pages/DepartmentsPage';
import { OrdersPage } from './pages/OrdersPage';
import { OverviewPage } from './pages/OverviewPage';
import { ReportsPage } from './pages/ReportsPage';
import { SuppliersPage } from './pages/SuppliersPage';

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/suppliers" element={<SuppliersPage />} />
        <Route path="/departments" element={<DepartmentsPage />} />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/:section" element={<ComingSoonPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
