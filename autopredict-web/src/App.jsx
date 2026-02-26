import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { WebSocketProvider } from './contexts/WebSocketContext';
import HeroSection from './components/HeroSection';
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';

/* ── Shared pages ─────────────────────────────────── */
import ConversationsPage from './pages/ConversationsPage';
import RecallsPage from './pages/RecallsPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';

/* ── Operations Dashboard (nested) ───────────────── */
import OperationsLayout from './pages/operations/OperationsLayout';
import OpsOverview from './pages/operations/OpsOverview';
import OpsFleet from './pages/operations/OpsFleet';
import OpsCalendar from './pages/operations/OpsCalendar';
import OpsConversations from './pages/operations/OpsConversations';

/* ── Manager Dashboard (nested) ──────────────────── */
import ManagerLayout from './pages/manager/ManagerLayout';
import ManagerOverview from './pages/manager/ManagerOverview';
import ManagerEscalations from './pages/manager/ManagerEscalations';
import ManagerRevenue from './pages/manager/ManagerRevenue';
import ManagerWorkload from './pages/manager/ManagerWorkload';

/* ── Executive Dashboard (nested) ────────────────── */
import ExecutiveLayout from './pages/executive/ExecutiveLayout';
import ExecOverview from './pages/executive/ExecOverview';
import ExecFleetHealth from './pages/executive/ExecFleetHealth';
import ExecTrends from './pages/executive/ExecTrends';
import ExecRecalls from './pages/executive/ExecRecalls';

function App() {
  return (
    <BrowserRouter>
      <WebSocketProvider>
      <Routes>
        {/* ── Public ────────────────────────────────── */}
        <Route path="/" element={<HeroSection />} />
        <Route path="/login" element={<Login />} />

        {/* ── Operations Dashboard ──────────────────── */}
        <Route
          path="/dashboard/operations"
          element={<ProtectedRoute role="ops"><OperationsLayout /></ProtectedRoute>}
        >
          <Route index element={<OpsOverview />} />
          <Route path="fleet" element={<OpsFleet />} />
          <Route path="calendar" element={<OpsCalendar />} />
          <Route path="conversations" element={<OpsConversations />} />
        </Route>

        {/* ── Manager Dashboard ─────────────────────── */}
        <Route
          path="/dashboard/manager"
          element={<ProtectedRoute role="manager"><ManagerLayout /></ProtectedRoute>}
        >
          <Route index element={<ManagerOverview />} />
          <Route path="escalations" element={<ManagerEscalations />} />
          <Route path="revenue" element={<ManagerRevenue />} />
          <Route path="workload" element={<ManagerWorkload />} />
        </Route>

        {/* ── Executive Dashboard ───────────────────── */}
        <Route
          path="/dashboard/executive"
          element={<ProtectedRoute role="executive"><ExecutiveLayout /></ProtectedRoute>}
        >
          <Route index element={<ExecOverview />} />
          <Route path="fleet-health" element={<ExecFleetHealth />} />
          <Route path="trends" element={<ExecTrends />} />
          <Route path="recalls" element={<ExecRecalls />} />
        </Route>

        {/* ── Shared authenticated pages ────────────── */}
        <Route path="/dashboard/conversations" element={<ProtectedRoute><ConversationsPage /></ProtectedRoute>} />
        <Route path="/dashboard/recalls" element={<ProtectedRoute><RecallsPage /></ProtectedRoute>} />
        <Route path="/dashboard/reports" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
        <Route path="/dashboard/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />

        {/* ── 404 catch-all ─────────────────────────── */}
        <Route path="*" element={
          <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-[#0b0f19]">
            <div className="text-center">
              <p className="text-6xl font-extrabold text-gray-900 dark:text-white mb-2">404</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">Page not found</p>
              <a href="/" className="px-5 py-2.5 rounded-2xl text-sm font-bold bg-[#6366f1] text-white hover:bg-[#5558e6] transition-colors">
                Go home
              </a>
            </div>
          </div>
        } />
      </Routes>
      </WebSocketProvider>
    </BrowserRouter>
  );
}

export default App;
