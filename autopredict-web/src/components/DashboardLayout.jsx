import React, { useState, useCallback } from 'react';
import Sidebar from '../components/Sidebar';

/**
 * Shared wrapper for all dashboard pages.
 * Sidebar exposes its collapsed state so we can adjust the main margin.
 */
export default function DashboardLayout({ title, children }) {
  const [collapsed, setCollapsed] = useState(false);

  const handleCollapseChange = useCallback((val) => {
    setCollapsed(val);
  }, []);

  return (
    <div className="flex min-h-screen bg-[#f4f5f0] dark:bg-[#0b0f19] transition-colors">
      <Sidebar onCollapseChange={handleCollapseChange} />

      {/* Main content — dynamically offset by sidebar width */}
      <main
        className="flex-1 p-8 transition-all duration-300"
        style={{ marginLeft: collapsed ? 72 : 256 }}
      >
        <h1 className="text-2xl font-extrabold text-gray-900 dark:text-white mb-6">
          {title}
        </h1>
        {children}
      </main>
    </div>
  );
}
