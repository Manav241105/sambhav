import React from 'react';
import { Navigate } from 'react-router-dom';
import { ROLE_HOME, getRole, hasSession } from '../lib/auth';

/**
 * Route guard for the staff dashboards.
 * Client-side checks only decide what to render; the API enforces access on every request.
 *
 * Usage:
 *   <ProtectedRoute role="ops"><OperationsDashboard /></ProtectedRoute>
 */
export default function ProtectedRoute({ role, children }) {
  if (!hasSession()) return <Navigate to="/login" replace />;

  const storedRole = getRole();
  if (role && storedRole !== role && storedRole !== 'admin') {
    return <Navigate to={ROLE_HOME[storedRole] || '/login'} replace />;
  }
  return children;
}
