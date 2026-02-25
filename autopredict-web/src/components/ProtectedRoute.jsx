import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * Auth guard — checks localStorage for a valid mock JWT and matching role.
 * Redirects to /login if unauthenticated or wrong role.
 *
 * Usage:
 *   <ProtectedRoute role="ops"><OperationsDashboard /></ProtectedRoute>
 */
export default function ProtectedRoute({ role, children }) {
  const token = localStorage.getItem('ap_token');
  const storedRole = localStorage.getItem('ap_role');

  /* No token → login */
  if (!token) return <Navigate to="/login" replace />;

  /* Decode mock JWT and check expiry */
  try {
    const payload = JSON.parse(atob(token));
    if (payload.exp < Date.now()) {
      localStorage.removeItem('ap_token');
      localStorage.removeItem('ap_role');
      return <Navigate to="/login" replace />;
    }
  } catch {
    return <Navigate to="/login" replace />;
  }

  /* Role mismatch → redirect to the user's correct dashboard */
  if (role && storedRole !== role) {
    const rolePathMap = { ops: '/dashboard/operations', manager: '/dashboard/manager', executive: '/dashboard/executive' };
    return <Navigate to={rolePathMap[storedRole] || '/login'} replace />;
  }

  return children;
}
