import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { WebSocketProvider } from './contexts/WebSocketContext';
const HeroSection = lazy(() => import('./components/HeroSection'));
const Login = lazy(() => import('./pages/Login'));
import ProtectedRoute from './components/ProtectedRoute';

/* ── Shared pages ─────────────────────────────────── */
const ConversationsPage = lazy(() => import('./pages/ConversationsPage'));
const RecallsPage = lazy(() => import('./pages/RecallsPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

/* ── Operations Dashboard (nested) ───────────────── */
const OperationsLayout = lazy(() => import('./pages/operations/OperationsLayout'));
const OpsOverview = lazy(() => import('./pages/operations/OpsOverview'));
const OpsFleet = lazy(() => import('./pages/operations/OpsFleet'));
const OpsCalendar = lazy(() => import('./pages/operations/OpsCalendar'));
const OpsConversations = lazy(() => import('./pages/operations/OpsConversations'));
const OpsWarnings = lazy(() => import('./pages/operations/OpsWarnings'));

/* ── Manager Dashboard (nested) ──────────────────── */
const ManagerLayout = lazy(() => import('./pages/manager/ManagerLayout'));
const ManagerOverview = lazy(() => import('./pages/manager/ManagerOverview'));
const ManagerEscalations = lazy(() => import('./pages/manager/ManagerEscalations'));
const ManagerRevenue = lazy(() => import('./pages/manager/ManagerRevenue'));
const ManagerWorkload = lazy(() => import('./pages/manager/ManagerWorkload'));

/* ── Executive Dashboard (nested) ────────────────── */
const ExecutiveLayout = lazy(() => import('./pages/executive/ExecutiveLayout'));
const ExecOverview = lazy(() => import('./pages/executive/ExecOverview'));
const ExecFleetHealth = lazy(() => import('./pages/executive/ExecFleetHealth'));
const ExecTrends = lazy(() => import('./pages/executive/ExecTrends'));
const ExecRecalls = lazy(() => import('./pages/executive/ExecRecalls'));

function App() {
  return (
    <BrowserRouter>
      <WebSocketProvider>
        <Suspense fallback={<div className="p-8 text-sm text-gray-400">Loading…</div>}>
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
            <Route path="warnings" element={<OpsWarnings />} />
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
        </Suspense>
      </WebSocketProvider>
    </BrowserRouter>
  );
}

export default App;
