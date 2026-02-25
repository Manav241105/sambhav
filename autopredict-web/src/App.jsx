import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HeroSection from './components/HeroSection';
import OperationsDashboard from './pages/OperationsDashboard';
import ManagerDashboard from './pages/ManagerDashboard';
import TopManagementDashboard from './pages/TopManagementDashboard';
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HeroSection />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard/operations"
          element={
            <ProtectedRoute role="ops">
              <OperationsDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/manager"
          element={
            <ProtectedRoute role="manager">
              <ManagerDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/executive"
          element={
            <ProtectedRoute role="executive">
              <TopManagementDashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
